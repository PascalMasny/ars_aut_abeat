import io
import os
import sys
import time
import base64
from pathlib import Path

# Silence MediaPipe/TF glog spam before any vision import loads them.
os.environ.setdefault("GLOG_minloglevel", "3")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("GRPC_VERBOSITY", "ERROR")

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from streamlit_autorefresh import st_autorefresh

# Workaround for streamlit-webrtc race in SessionShutdownObserver.stop():
# the original checks `if self._polling_thread:` then dereferences
# self._polling_thread.is_alive() a few lines later. A concurrent stop() on
# another thread can set it to None in between, causing AttributeError and
# restarting the webrtc worker (which re-loads MediaPipe) on every rerun.
import threading as _threading
from streamlit_webrtc.shutdown import SessionShutdownObserver as _SSO
def _sso_stop_safe(self, timeout: float = 1.0) -> None:
    thread = self._polling_thread
    if thread is None:
        return
    self._polling_thread_stop_event.set()
    if _threading.current_thread() is not thread:
        thread.join(timeout=timeout)
    self._polling_thread = None
_SSO.stop = _sso_stop_safe

from streamlit_webrtc import webrtc_streamer, WebRtcMode

from ui.theme import inject_css
from core.state_machine import init_state, advance_state, PHASES
from data.db import init_db, get_session
from catalog.manager import get_catalog_manager
from vision.camera import GalleryVideoProcessor, CameraState
from config import (
    BASE_DIR,
    MORPHING_DURATION, RECAP_DURATION,
    FRAME_COUNT, FRAME_RATE,
    EMOTION_LATIN,
)

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Vallis Simulacri",
    page_icon="⚜",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()
init_db()
init_state()
catalog = get_catalog_manager()


@st.cache_data(show_spinner=False)
def _artwork_data_uri(path_str: str) -> str:
    p = Path(path_str)
    if not p.exists():
        return ""
    ext = p.suffix.lstrip(".") or "jpg"
    return f"data:image/{ext};base64,{base64.b64encode(p.read_bytes()).decode()}"


def _morph_frame_idx(elapsed_t: float, total_frames: int) -> tuple[int, int, float]:
    """Return (cur_idx, next_idx, blend) for elapsed time.

    blend=0.0 → show only cur; blend=1.0 → show only next.
    """
    progress = min(elapsed_t / MORPHING_DURATION, 1.0)
    raw      = progress * total_frames
    cur_idx  = min(int(raw), total_frames - 1)
    next_idx = min(cur_idx + 1, total_frames)
    blend    = raw - int(raw)
    return cur_idx, next_idx, blend


def _make_recap_graph(timestamps: list[float], samples: list[dict]) -> str:
    """Render emotion-over-time line graph. Returns base64 PNG."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {
        "happy":    "#E8C87A", "sad":      "#6B9E7A",
        "angry":    "#CC5555", "surprise": "#C9A961",
        "fear":     "#9B7FCC", "disgust":  "#C97A50",
        "neutral":  "#8B8B7E",
    }

    fig, ax = plt.subplots(figsize=(13, 5))

    if timestamps and samples:
        for emotion, color in colors.items():
            values = [s.get(emotion, 0) * 100 for s in samples]
            ax.plot(timestamps, values, color=color, linewidth=1.8,
                    label=EMOTION_LATIN.get(emotion, emotion), alpha=0.9)


    fig.patch.set_facecolor("#1C1410")
    ax.set_facecolor("#120E0A")
    ax.tick_params(colors="#8B6F2E", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#3D2810")
    ax.set_xlabel("Seconds", color="#8B6F2E", fontsize=9)
    ax.set_ylabel("Intensity %", color="#8B6F2E", fontsize=9)
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 100)
    ax.legend(loc="upper right", facecolor="#1C1410", edgecolor="#3D2810",
              labelcolor="#C9A961", fontsize=7, framealpha=0.85,
              ncol=2, handlelength=1.2)
    ax.grid(axis="y", color="#2A1E0A", linewidth=0.6, alpha=0.6)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()

# ─── IDLE header (above camera) ──────────────────────────────────────────────
phase = st.session_state.get("phase", "IDLE")

# ─── Developer zoom control ──────────────────────────────────────────────────
if "cam_zoom" not in st.session_state:
    st.session_state.cam_zoom = 1.0

query_params = st.query_params
if "dev" in query_params:
    with st.sidebar:
        st.markdown("### Dev Controls")
        st.session_state.cam_zoom = st.slider("Camera Zoom", 1.0, 3.0, st.session_state.cam_zoom, 0.1)

zoom = st.session_state.cam_zoom
zoom_css = f"""<style>
[data-testid="stCustomComponentV1"]:nth-of-type(1) iframe {{
    transform: scale({zoom}) !important;
    transform-origin: center center !important;
}}
</style>""" if zoom != 1.0 else ""
if zoom_css:
    st.markdown(zoom_css, unsafe_allow_html=True)

# ─── WebRTC camera — always renders, visible in IDLE, covered in other phases ─
# desired_playing_state=True ONLY on first render; passing it on every rerun causes
# the component to re-evaluate state and cycle connections.
_first_render = not st.session_state.get("_webrtc_started", False)
st.session_state._webrtc_started = True

ctx = webrtc_streamer(
    key="gallery-cam",
    mode=WebRtcMode.SENDRECV,
    desired_playing_state=True if _first_render else None,
    video_processor_factory=GalleryVideoProcessor,
    media_stream_constraints={
        "video": {
            "width":     {"min": 1920, "ideal": 1920},
            "height":    {"min": 1080, "ideal": 1080},
            "frameRate": {"min":   15, "ideal":   30},
            "facingMode": "user",
        },
        "audio": False,
    },
    async_processing=True,
    video_html_attrs={
        "style": {"width": "100%", "height": "100%"},
        "controls": False,
        "autoPlay": True,
        "muted": True,
    },
)

# ─── Auto-refresh ─────────────────────────────────────────────────────────────
# Aggressive reruns remount the webrtc iframe and kill the preview. Refresh only
# as fast as each phase needs:
#   IDLE          — 1.5s (just to pick up face/hands changes)
#   LOCKED/FADE   — 1s (transitions)
#   VIEWING       — 750ms (countdown + emotion bars)
#   VERDICT_*     — 2s (static screen)
_phase = st.session_state.get("phase", "IDLE")
_refresh_ms = {
    "IDLE":     1500,
    "LOCKED":   1000,
    "MORPHING":  300,   # ~3.3 reruns/s to advance frames at FRAME_RATE=3fps
    "RECAP":    5000,   # mostly static after first render
    "FADE":     1000,
}.get(_phase, 1500)
st_autorefresh(interval=_refresh_ms, key="gallery-refresh")

# ─── Read camera state ────────────────────────────────────────────────────────
camera_state = CameraState()
if ctx.video_processor:
    processor: GalleryVideoProcessor = ctx.video_processor
    camera_state = processor.get_state()
    processor.set_emotion_sampling(st.session_state.phase == "MORPHING")
    processor.set_pose_sampling(st.session_state.phase == "IDLE")

# ─── State machine ────────────────────────────────────────────────────────────
db = get_session()
try:
    advance_state(camera_state, catalog, db)
finally:
    db.close()

# Re-read phase (may have changed)
phase = st.session_state.phase

# ─── IDLE: text overlaid on full-screen video ───────────────────────────────
if phase == "IDLE":
    face = camera_state.face_present
    hands = camera_state.hands_raised
    if hands:
        status_icon = "✦"
        status_text = "CONSENT ACKNOWLEDGED — HOLD"
        status_color = "#E8C87A"
        hint = "Entering the valley…"
    elif face:
        status_icon = "◉"
        status_text = "VISITOR DETECTED"
        status_color = "#C9A961"
        hint = "Read the panel. Raise both hands to accept and begin."
    else:
        status_icon = "◎"
        status_text = "APPROACH · BE SEEN"
        status_color = "#8B6F2E"
        hint = "Stand before the glass and read the instructions."

    st.markdown(f"""
<div class="mirror-overlay">
  <!-- Top: title -->
  <div class="mirror-top">
    <div style="font-family:'Cinzel',serif; font-weight:700; font-size:clamp(1.5rem,5vw,4rem);
                letter-spacing:0.25em; color:#C9A961; text-shadow:0 3px 20px rgba(0,0,0,0.8);">
      VALLIS · SIMVLACRI
    </div>
    <div style="color:#C9A961; font-size:clamp(0.9rem,1.5vw,1.5rem);
                letter-spacing:0.3em; opacity:0.5; margin-top:0.5rem;">
      ❧ · · ❧
    </div>
  </div>

  <aside class="howitworks-panel"><div class="howitworks-title">THE EXPERIENCE</div><div class="howitworks-step" style="margin-bottom:0.6rem;line-height:1.6;">A classical artwork is presented to you — then fed into an AI. The AI output is fed back in again. And again. Each cycle pushes the image further into the uncanny valley: recognisable, yet deeply wrong.</div><div style="border-top:1px solid rgba(201,169,97,0.25);margin:0.6rem 0;"></div><div class="howitworks-step"><strong>I.</strong>A classical work appears before you</div><div class="howitworks-step"><strong>II.</strong>It slowly morphs through AI feedback loops</div><div class="howitworks-step"><strong>III.</strong>Your emotional response is recorded in real time</div><div class="howitworks-step"><strong>IV.</strong>A graph of your descent is revealed</div><div style="border-top:1px solid rgba(201,169,97,0.25);margin:0.6rem 0;"></div><div style="background:rgba(139,34,34,0.18);border:1px solid rgba(139,34,34,0.5);border-radius:4px;padding:0.5rem 0.7rem;"><div style="font-family:'Cinzel',serif;font-size:clamp(0.6rem,0.85vw,0.85rem);letter-spacing:0.15em;color:#CC6666;margin-bottom:0.25rem;">&#9888; CONTENT WARNING</div><div class="howitworks-step" style="color:#E0B0B0;margin:0;">Some images may appear disturbing due to uncanny distortion. Raise both hands to acknowledge and begin.</div></div></aside>

  <!-- Bottom: status + plaque -->
  <div class="mirror-bottom">
    <div style="font-family:'Cinzel',serif; font-weight:700;
                font-size:clamp(0.9rem,3vw,2rem);
                letter-spacing:0.22em; color:{status_color};
                text-shadow:0 3px 15px rgba(0,0,0,0.9);
                display:flex; align-items:center; justify-content:center; gap:0.8rem;">
      <span>{status_icon}</span>
      {status_text}
      <span>{status_icon}</span>
    </div>
    <div style="font-family:'Cormorant Garamond',serif; font-style:italic;
                color:#E0D0B0; font-size:clamp(0.95rem,2vw,1.5rem); margin-top:0.5rem;
                text-shadow:0 2px 12px rgba(0,0,0,0.9);">
      {hint}
    </div>
    <div style="color:#C9A961; font-size:clamp(0.85rem,1.2vw,1.2rem);
                letter-spacing:0.3em; opacity:0.5; margin:0.6rem 0 0.4rem;">
      ❧ · · ❧
    </div>
    <div style="font-family:'Pinyon Script',cursive; font-size:clamp(1.4rem,4vw,3rem);
                color:#C9A961; opacity:0.7; text-shadow:0 3px 15px rgba(0,0,0,0.8);">
      Vallis Simulacri
    </div>
    <div style="font-family:'Cormorant Garamond',serif; font-size:clamp(0.8rem,1.2vw,1.1rem);
                letter-spacing:0.15em; color:#8B6F2E; margin-top:0.2rem;
                text-shadow:0 2px 8px rgba(0,0,0,0.8);">
      THE VALLEY OF LIKENESS
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── Non-IDLE: full-screen overlay on top of webrtc ──────────────────────────
elif phase == "LOCKED":
    artwork = st.session_state.current_artwork
    title = artwork["title"] if artwork else "..."
    st.markdown(f"""
<div class="gallery-overlay">
  <div style="font-family:'Cinzel',serif; font-weight:700; font-size:clamp(1.1rem,3vw,2.2rem);
              letter-spacing:0.3em; color:#C9A961;">VALLIS · SIMVLACRI</div>
  <div style="color:#C9A961; font-size:clamp(0.9rem,1.3vw,1.4rem); letter-spacing:0.3em; opacity:0.7; margin:1rem 0;">❧ · · ❧</div>
  <div style="border:3px solid #C9A961; border-radius:50%; padding:clamp(0.8rem,1.5vw,1.5rem) clamp(1.5rem,3vw,3rem);
              box-shadow:0 0 40px rgba(201,169,97,0.35);">
    <div style="font-family:'Cinzel',serif; font-weight:700; font-size:clamp(1rem,3vw,2rem);
                letter-spacing:0.25em; color:#C9A961;">SPECTATOR IDENTIFIED</div>
  </div>
  <div style="color:#C9A961; font-size:clamp(0.9rem,1.3vw,1.4rem); letter-spacing:0.3em; opacity:0.7; margin:1rem 0;">❧ · · ❧</div>
  <div style="font-family:'Cormorant Garamond',serif; font-style:italic; color:#E0D0B0;
              font-size:clamp(1.1rem,1.8vw,1.8rem);">
    Prepare thyself to confront —
  </div>
  <div style="font-family:'Cinzel',serif; font-weight:700; font-size:clamp(1.4rem,5vw,3.5rem);
              color:#E8C87A; margin-top:0.5rem; text-align:center; padding:0 1rem;">
    {title}
  </div>
</div>
""", unsafe_allow_html=True)

elif phase == "MORPHING":
    artwork   = st.session_state.current_artwork
    elapsed_t = time.time() - st.session_state.phase_entered_at
    emotions  = camera_state.latest_emotions

    frames       = artwork["frames"]
    total_frames = len(frames) - 1   # e.g. 100

    cur_idx, next_idx, blend = _morph_frame_idx(elapsed_t, total_frames)

    uri_cur  = _artwork_data_uri(frames[cur_idx])
    uri_next = _artwork_data_uri(frames[next_idx])

    progress_pct = min(100, int((elapsed_t / MORPHING_DURATION) * 100))
    frame_label  = f"FRAME {cur_idx:03d} / {total_frames}"

    # ── Build stacked image layers (current + next, blended) ─────────────────
    img_layers = ""
    if uri_cur:
        img_layers += (
            f'<img src="{uri_cur}" style="position:absolute;top:0;left:0;'
            f'width:100%;height:100%;object-fit:contain;'
            f'opacity:{1 - blend:.3f};transition:opacity 0.15s;" />'
        )
    if uri_next and uri_next != uri_cur:
        img_layers += (
            f'<img src="{uri_next}" style="position:absolute;top:0;left:0;'
            f'width:100%;height:100%;object-fit:contain;'
            f'opacity:{blend:.3f};transition:opacity 0.15s;" />'
        )

    # ── Emotion bars (overlay inside artwork) ────────────────────────────────
    bars = ""
    for eng, val in sorted(emotions.items(), key=lambda x: -x[1])[:5]:
        label_name = EMOTION_LATIN.get(eng, eng.capitalize())
        pct = round(val * 100, 1)
        bars += f"""
<div style="margin:0.3rem 0;">
  <div style="display:flex;justify-content:space-between;font-family:'Cinzel',serif;
              font-size:clamp(0.8rem,1.1vw,1.1rem);letter-spacing:0.07em;color:#C9A961;margin-bottom:3px;">
    <span>{label_name}</span><span>{pct}%</span>
  </div>
  <div style="height:clamp(5px,0.8vw,9px);background:rgba(201,169,97,0.15);border-radius:5px;overflow:hidden;">
    <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,#8B6F2E,#E8C87A);border-radius:5px;transition:width 0.3s;"></div>
  </div>
</div>"""

    st.markdown(f"""
<div class="gallery-overlay" style="padding:0;">
  <!-- Fullscreen image stack -->
  {img_layers if img_layers else '<div style="position:absolute;top:0;left:0;width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:#8B6F2E;">[ IMAGE AWAITED ]</div>'}

  <!-- Gilt frame border -->
  <div style="position:absolute;top:8px;left:8px;right:8px;bottom:8px;
              border:3px solid #C9A961;
              box-shadow:0 0 0 1px #8B6F2E,inset 0 0 0 1px #8B6F2E,
                         0 0 30px rgba(201,169,97,0.15),inset 0 0 30px rgba(201,169,97,0.08);
              pointer-events:none;z-index:10;"></div>

  <!-- Top overlay: title + frame counter -->
  <div style="position:absolute;top:0;left:0;right:0;z-index:5;
              background:linear-gradient(rgba(28,20,16,0.85) 0%,transparent 100%);
              padding:2.5vh 4vw 5vh;text-align:center;">
    <div style="font-family:'Cinzel',serif;font-weight:700;
                font-size:clamp(1.1rem,3vw,2.2rem);letter-spacing:0.15em;color:#C9A961;">
      {artwork['title']}
    </div>
    <div style="font-family:'Cormorant Garamond',serif;font-style:italic;
                font-size:clamp(0.85rem,1.2vw,1.2rem);letter-spacing:0.25em;
                color:#8B6F2E;margin-top:0.3rem;">
      {frame_label}
    </div>
  </div>

  <!-- Bottom overlay: emotions + progress bar -->
  <div style="position:absolute;bottom:0;left:0;right:0;z-index:5;
              background:linear-gradient(transparent,rgba(28,20,16,0.88) 25%,rgba(28,20,16,0.96));
              padding:3vh 6vw 2.5vh;">
    <div style="font-family:'Cinzel',serif;font-size:clamp(0.65rem,0.85vw,0.85rem);
                letter-spacing:0.2em;color:#8B6F2E;text-align:center;margin-bottom:0.6rem;">
      YOUR EMOTIONS
    </div>
    {bars if bars else '<div style="font-family:\'Cormorant Garamond\',serif;font-style:italic;color:#8B6F2E;text-align:center;">Reading…</div>'}
    <div style="height:2px;background:rgba(201,169,97,0.12);border-radius:2px;margin-top:1rem;">
      <div style="width:{progress_pct}%;height:100%;background:linear-gradient(90deg,#8B6F2E,#C9A961);
                  border-radius:2px;transition:width 0.3s linear;"></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

elif phase == "RECAP":
    artwork  = st.session_state.current_artwork
    session  = st.session_state.viewer_session
    verdict  = st.session_state.personal_verdict
    seal_colors = {"VALLIS": "#8B2222", "LIMEN": "#8B9E6B", "FIRMA": "#C9A961"}
    sc = seal_colors.get(verdict, "#C9A961")

    # Generate graph once per viewing session
    if "recap_graph" not in st.session_state:
        st.session_state.recap_graph = _make_recap_graph(
            session.emotion_timestamps,
            session.emotion_samples,
        )
    graph_b64 = st.session_state.recap_graph

    # ── 2×2 thumbnail grid — pick 4 evenly-spaced frames ────────────────────
    frames = artwork["frames"]
    n      = len(frames) - 1   # e.g. 100
    thumb_paths = [
        frames[0],
        frames[max(1, n // 3)],
        frames[max(1, 2 * n // 3)],
        frames[n],
    ]
    thumb_uris = [_artwork_data_uri(p) for p in thumb_paths]

    stage_labels_en = ["ORIGINAL", "LIGHT", "MEDIUM", "DEEP"]
    thumb_cells_grid = ""
    for lbl, uri in zip(stage_labels_en, thumb_uris):
        img_tag = (
            f'<img src="{uri}" style="width:100%;height:20vh;object-fit:contain;display:block;" />'
            if uri else '<div style="height:20vh;background:#0a0806;"></div>'
        )
        thumb_cells_grid += f"""
<div style="text-align:center;">
  <div style="font-family:'Cinzel',serif;font-size:clamp(0.5rem,0.7vw,0.72rem);
              letter-spacing:0.15em;color:#8B6F2E;margin-bottom:0.25rem;">{lbl}</div>
  <div style="border:2px solid #3D2810;padding:3px;background:#0a0806;">{img_tag}</div>
</div>"""

    graph_tag = (
        f'<img src="data:image/png;base64,{graph_b64}" '
        f'style="width:100%;max-height:20vh;height:auto;border-radius:4px;border:1px solid #3D2810;display:block;" />'
        if graph_b64 else
        '<div style="color:#8B6F2E;font-style:italic;text-align:center;padding:1rem;">No emotion data recorded.</div>'
    )

    st.markdown(f"""
<div class="gallery-overlay" style="justify-content:flex-start;padding:2.5vh 3vw 2vh;">
  <!-- Gilt frame border -->
  <div style="position:absolute;top:8px;left:8px;right:8px;bottom:8px;
              border:3px solid #C9A961;
              box-shadow:0 0 0 1px #8B6F2E,inset 0 0 0 1px #8B6F2E,
                         0 0 30px rgba(201,169,97,0.15);
              pointer-events:none;z-index:20;"></div>

  <!-- Header -->
  <div style="text-align:center;margin-bottom:1vh;width:100%;flex-shrink:0;">
    <div style="font-family:'Cinzel',serif;font-weight:700;
                font-size:clamp(0.85rem,1.4vw,1.3rem);letter-spacing:0.3em;color:#8B6F2E;">
      YOUR EMOTIONAL DESCENT
    </div>
    <div style="font-family:'Cormorant Garamond',serif;font-style:italic;
                font-size:clamp(0.85rem,1.1vw,1.1rem);color:#8B6F2E;opacity:0.7;margin-top:0.2rem;">
      {artwork['title']}
    </div>
  </div>

  <!-- 2×2 thumbnail grid -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.4rem;width:100%;flex-shrink:0;margin-bottom:1vh;">
    {thumb_cells_grid}
  </div>

  <!-- Compact emotion graph -->
  <div style="width:100%;flex-shrink:0;margin-bottom:1vh;">
    {graph_tag}
  </div>

  <!-- Prominent verdict seal -->
  <div style="display:flex;justify-content:center;flex-shrink:0;">
    <div class="seal-medallion" style="
                width:clamp(110px,16vw,180px);height:clamp(110px,16vw,180px);
                border:5px solid {sc};
                background:radial-gradient(circle at 40% 35%,{sc}66,{sc}22);
                color:{sc};font-size:clamp(1rem,1.8vw,1.6rem);">
      {verdict}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

elif phase == "FADE":
    st.markdown("""
<div class="gallery-overlay">
  <div style="font-family:'Cinzel',serif; font-weight:700; font-size:clamp(2rem,4vw,3rem);
              letter-spacing:0.3em; color:#8B6F2E;">
    THE VALLEY AWAITS THE NEXT SOUL
  </div>
  <div style="color:#C9A961; font-size:4rem; margin-top:1rem; opacity:0.6;">⚜</div>
</div>
""", unsafe_allow_html=True)
