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

import streamlit.components.v1 as components
from streamlit_webrtc import webrtc_streamer, WebRtcMode

from ui.theme import inject_css
from core.state_machine import init_state, advance_state, PHASES
from data.db import init_db, get_session
from catalog.manager import get_catalog_manager
from vision.camera import GalleryVideoProcessor, CameraState
from data.models import Viewing
from config import (
    MORPHING_DURATION, RECAP_DURATION,
    FRAME_COUNT,
    EMOTION_LATIN,
    ATTRACT_CYCLE_S, ATTRACT_DURATION_S,
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


def _morphing_player_html(stem: str, total_frames: int, duration: float,
                           phase_start: float, title: str) -> str:
    import json
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Cormorant+Garamond:ital,wght@0,400;1,400&display=swap" rel="stylesheet">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ background: #1C1410; overflow: hidden; width: 100vw; height: 100vh; }}
#player {{
    position: fixed;
    top: 0; left: 50%;
    transform: translateX(-50%);
    width: min(100vw, calc(100vh * 16 / 9));
    height: 100vh;
    background: #1C1410;
    overflow: hidden;
}}
#img-a, #img-b {{
    position: absolute; top: 0; left: 0;
    width: 100%; height: 100%;
    object-fit: contain;
}}
#img-b {{ opacity: 0; }}
#frame-border {{
    position: absolute; top: 8px; left: 8px; right: 8px; bottom: 8px;
    border: 3px solid #C9A961;
    box-shadow: 0 0 0 1px #8B6F2E, inset 0 0 0 1px #8B6F2E,
                0 0 30px rgba(201,169,97,0.15), inset 0 0 30px rgba(201,169,97,0.08);
    pointer-events: none; z-index: 10;
}}
#top-overlay {{
    position: absolute; top: 0; left: 0; right: 0; z-index: 5;
    background: linear-gradient(rgba(28,20,16,0.85) 0%, transparent 100%);
    padding: 2.5vh 4vw 5vh; text-align: center;
}}
.artwork-title {{
    font-family: 'Cinzel', serif; font-weight: 700;
    font-size: clamp(1.1rem, 3vw, 2.2rem);
    letter-spacing: 0.15em; color: #C9A961;
}}
.frame-label {{
    font-family: 'Cormorant Garamond', serif; font-style: italic;
    font-size: clamp(0.85rem, 1.2vw, 1.2rem);
    letter-spacing: 0.25em; color: #8B6F2E; margin-top: 0.3rem;
}}
#progress-track {{
    position: absolute; left: 6vw; right: 6vw; bottom: 1.5vh;
    height: 2px; background: rgba(201,169,97,0.12);
    border-radius: 2px; z-index: 5;
}}
#progress-fill {{
    height: 100%;
    background: linear-gradient(90deg, #8B6F2E, #C9A961);
    border-radius: 2px;
}}
</style>
</head>
<body>
<div id="player">
  <img id="img-a" />
  <img id="img-b" />
  <div id="frame-border"></div>
  <div id="top-overlay">
    <div class="artwork-title">{title}</div>
    <div class="frame-label" id="frame-el">FRAME 000 / {total_frames}</div>
  </div>
  <div id="progress-track"><div id="progress-fill" style="width:0%"></div></div>
</div>
<script>
const STEM = {json.dumps(stem)};
const TOTAL_FRAMES = {total_frames};
const DURATION = {duration};
const STARTED_AT = {phase_start};

// Resolve an absolute origin (srcdoc iframes can have a flaky base URL,
// so we fall back to the parent window's origin if accessible).
let ORIGIN = "";
try {{ ORIGIN = window.parent.location.origin; }} catch(e) {{}}
console.log("[morphing] booting", {{stem: STEM, total: TOTAL_FRAMES, started: STARTED_AT, origin: ORIGIN}});

// Preload all frames
const imgs = Array.from({{length: TOTAL_FRAMES+1}}, (_,i) => {{
  const url = ORIGIN + `/app/static/frames/${{STEM}}/${{String(i).padStart(4,'0')}}.png`;
  const img = new Image();
  img.onerror = () => console.warn("[morphing] failed", url);
  img.src = url;
  return img;
}});
console.log("[morphing] preloaded", imgs.length, "frame requests; first url:", imgs[0].src);

// Continuous crossfade: imgA holds the "current" frame, imgB holds the "next".
// Opacity is interpolated every animation frame from the fractional progress,
// so neighbouring frames blend smoothly rather than snapping every 0.3 s.
const imgA = document.getElementById('img-a');
const imgB = document.getElementById('img-b');
let curIdx = -1, nextIdx = -1;

function tick() {{
  const elapsed  = (Date.now()/1000) - STARTED_AT;
  const progress = Math.min(elapsed/DURATION, 1.0);
  const raw      = progress * TOTAL_FRAMES;
  const ci       = Math.min(Math.floor(raw), TOTAL_FRAMES);
  const ni       = Math.min(ci + 1, TOTAL_FRAMES);
  const blend    = raw - Math.floor(raw);

  if (ci !== curIdx)  {{ curIdx  = ci;  imgA.src = imgs[ci].src; }}
  if (ni !== nextIdx) {{ nextIdx = ni;  imgB.src = imgs[ni].src; }}

  imgA.style.opacity = (1 - blend).toFixed(3);
  imgB.style.opacity = blend.toFixed(3);

  document.getElementById('progress-fill').style.width = (progress*100).toFixed(2) + '%';
  document.getElementById('frame-el').textContent =
    'FRAME '+String(ci).padStart(3,'0')+' / '+TOTAL_FRAMES;

  if (progress < 1.0) requestAnimationFrame(tick);
}}
tick();
</script>
</body>
</html>"""


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

def _make_attract_graph(db) -> str | None:
    """Render aggregate verdict donut + average emotion bars. Returns base64 PNG or None."""
    import json
    viewings = db.query(Viewing).all()
    if not viewings:
        return None

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    # ── Aggregate data ────────────────────────────────────────────────────────
    verdict_counts = {"VALLIS": 0, "LIMEN": 0, "FIRMA": 0}
    emotion_sums: dict = {}
    emotion_n = 0
    for v in viewings:
        verdict_counts[v.verdict] = verdict_counts.get(v.verdict, 0) + 1
        try:
            em = json.loads(v.emotion_json) if isinstance(v.emotion_json, str) else {}
        except Exception:
            em = {}
        if em:
            for k, val in em.items():
                emotion_sums[k] = emotion_sums.get(k, 0.0) + val
            emotion_n += 1

    avg_emotions = {k: v / emotion_n for k, v in emotion_sums.items()} if emotion_n else {}

    # ── Figure ────────────────────────────────────────────────────────────────
    fig, (ax_donut, ax_bar) = plt.subplots(1, 2, figsize=(13, 5))
    fig.patch.set_facecolor("#1C1410")

    # Left: verdict donut
    donut_labels = [k for k, c in verdict_counts.items() if c > 0]
    donut_sizes  = [verdict_counts[k] for k in donut_labels]
    donut_colors = {"VALLIS": "#8B2222", "ARS": "#8B2222", "LIMEN": "#6B7B5E", "FIRMA": "#C9A961", "ABEAT": "#C9A961"}
    colors = [donut_colors.get(k, "#888888") for k in donut_labels]

    if donut_sizes:
        wedges, texts, autotexts = ax_donut.pie(
            donut_sizes,
            labels=None,
            colors=colors,
            autopct=lambda p: f"{p:.0f}%" if p > 5 else "",
            pctdistance=0.75,
            startangle=90,
            wedgeprops={"width": 0.55, "edgecolor": "#1C1410", "linewidth": 2},
        )
        for at in autotexts:
            at.set_color("#F4E8D0")
            at.set_fontsize(9)
        ax_donut.legend(
            wedges,
            [f"{k}  ({verdict_counts[k]})" for k in donut_labels],
            loc="lower center",
            facecolor="#1C1410",
            edgecolor="#3D2810",
            labelcolor="#C9A961",
            fontsize=8,
            framealpha=0.9,
            ncol=len(donut_labels),
            bbox_to_anchor=(0.5, -0.08),
        )
    else:
        ax_donut.text(0.5, 0.5, "No data yet", ha="center", va="center",
                      color="#8B6F2E", fontsize=11, fontfamily="serif",
                      transform=ax_donut.transAxes)

    ax_donut.set_facecolor("#120E0A")
    ax_donut.set_title("VERDICT DISTRIBUTION", color="#8B6F2E",
                        fontsize=8, fontfamily="serif", pad=10)

    # Right: average emotion bars
    emotion_colors = {
        "happy": "#E8C87A", "sad": "#6B9E7A", "angry": "#CC5555",
        "surprise": "#C9A961", "fear": "#9B7FCC", "disgust": "#C97A50",
        "neutral": "#8B8B7E",
    }
    if avg_emotions:
        sorted_em = sorted(avg_emotions.items(), key=lambda x: x[1], reverse=True)
        labels = [EMOTION_LATIN.get(k, k.capitalize()) for k, _ in sorted_em]
        values = [v * 100 for _, v in sorted_em]
        bar_colors = [emotion_colors.get(k, "#C9A961") for k, _ in sorted_em]

        bars = ax_bar.barh(labels[::-1], values[::-1], color=bar_colors[::-1],
                           edgecolor="#1C1410", linewidth=0.5, height=0.6)
        ax_bar.set_xlim(0, 100)
        ax_bar.set_xlabel("Average Intensity %", color="#8B6F2E", fontsize=8)
        ax_bar.tick_params(colors="#8B6F2E", labelsize=8)
        for spine in ax_bar.spines.values():
            spine.set_color("#3D2810")
        ax_bar.grid(axis="x", color="#2A1E0A", linewidth=0.6, alpha=0.6)
    else:
        ax_bar.text(0.5, 0.5, "No emotion data yet", ha="center", va="center",
                    color="#8B6F2E", fontsize=11, fontfamily="serif",
                    transform=ax_bar.transAxes)

    ax_bar.set_facecolor("#120E0A")
    ax_bar.set_title("AVERAGE EMOTIONAL RESPONSE", color="#8B6F2E",
                      fontsize=8, fontfamily="serif", pad=10)

    fig.subplots_adjust(wspace=0.35, left=0.08, right=0.97, top=0.88, bottom=0.15)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
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

# ─── WebRTC camera — SENDONLY: processes frames server-side, never displayed ──
# The component is rendered with no `desired_playing_state` so the user has to
# click the built-in START button. That click triggers the browser's camera
# permission prompt AND its camera-picker dropdown (so iPhone / Continuity
# Camera / external webcams can be selected). Once frames are flowing, body
# gets the `camera-running` class and theme.py collapses the component to 0×0.

ctx = webrtc_streamer(
    key="gallery-cam",
    mode=WebRtcMode.SENDONLY,
    # No desired_playing_state → user clicks the component's own START button.
    video_processor_factory=GalleryVideoProcessor,
    media_stream_constraints={
        # Low-res stream: face/emotion detection runs on this, never displayed.
        # 1080p@30fps queued frames faster than the emotion model could clear them.
        "video": {
            "width":     {"ideal": 640},
            "height":    {"ideal": 480},
            "frameRate": {"ideal": 15, "max": 20},
            "facingMode": "user",
        },
        "audio": False,
    },
    async_processing=True,
)

# ─── Consent gate: show welcome screen until camera is actually streaming ───
camera_running = ctx is not None and ctx.state.playing
if camera_running:
    # Once frames start flowing, tag <body> so theme.py collapses the picker.
    components.html(
        "<script>window.parent.document.body.classList.add('camera-running');</script>",
        height=0,
    )
else:
    # Make sure the class is OFF while we're showing the picker.
    components.html(
        "<script>window.parent.document.body.classList.remove('camera-running');</script>",
        height=0,
    )
    st.markdown("""
<div class="gallery-overlay" style="flex-direction:column;gap:1.5vh;
            justify-content:flex-start;padding-top:8vh;">
  <div style="position:absolute;top:8px;left:8px;right:8px;bottom:8px;
              border:3px solid #C9A961;
              box-shadow:0 0 0 1px #8B6F2E,inset 0 0 0 1px #8B6F2E,
                         0 0 30px rgba(201,169,97,0.15);
              pointer-events:none;"></div>

  <div style="font-family:'Cinzel',serif;font-weight:700;
              font-size:clamp(1.4rem,3.5vw,3rem);letter-spacing:0.3em;color:#C9A961;
              text-shadow:0 3px 18px rgba(0,0,0,0.85);">
    VALLIS · SIMVLACRI
  </div>
  <div style="font-family:'Cormorant Garamond',serif;font-style:italic;
              font-size:clamp(0.95rem,1.4vw,1.4rem);letter-spacing:0.2em;
              color:#8B6F2E;margin-top:-0.5vh;">
    The Valley of Likeness
  </div>

  <div style="font-family:'Cormorant Garamond',serif;
              font-size:clamp(1rem,1.5vw,1.4rem);line-height:1.7;
              color:#E0D0B0;max-width:42rem;text-align:center;margin:2vh 0;">
    This installation reads your face to measure how you respond to the artwork.
    <br/>No video is stored. All processing happens on this device.
  </div>

  <div style="font-family:'Cormorant Garamond',serif;font-style:italic;
              font-size:clamp(0.95rem,1.3vw,1.25rem);color:#8B6F2E;
              text-align:center;max-width:36rem;margin:1vh auto 0;">
    Use the panel below to select your camera and press <b>START</b>.
    Your browser will ask permission. Once the camera is active this panel
    disappears and the gallery begins.
  </div>
</div>
""", unsafe_allow_html=True)
    st.stop()

# Compatibility: code below used to gate on these flags; keep them set so any
# remaining checks don't trip.
st.session_state.camera_consent = True
st.session_state._webrtc_started = True

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
    "INTRO":    1500,   # mostly static intro screen
    "MORPHING":  250,   # JS drives the animation; bar overlay rerenders ~4× / sec
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

# ─── IDLE ────────────────────────────────────────────────────────────────────
if phase == "IDLE":
    # ── Attract screen logic ──────────────────────────────────────────────────
    elapsed_idle  = time.time() - st.session_state.phase_entered_at
    show_attract  = int(elapsed_idle) % ATTRACT_CYCLE_S < ATTRACT_DURATION_S

    if show_attract:
        # Rebuild graph only when a new viewing has been logged
        db_attract = get_session()
        try:
            soul_count = db_attract.query(Viewing).count()
        finally:
            db_attract.close()

        if soul_count != st.session_state.get("attract_viewing_count"):
            db_attract2 = get_session()
            try:
                st.session_state.attract_graph = _make_attract_graph(db_attract2)
            finally:
                db_attract2.close()
            st.session_state.attract_viewing_count = soul_count

        graph_b64  = st.session_state.get("attract_graph")
        graph_tag  = (
            f'<img src="data:image/png;base64,{graph_b64}" '
            f'style="width:100%;max-height:38vh;height:auto;border-radius:4px;'
            f'border:1px solid #3D2810;display:block;margin:0.6rem 0;" />'
            if graph_b64 else
            '<div style="font-family:\'Cormorant Garamond\',serif;font-style:italic;'
            'color:#8B6F2E;text-align:center;padding:1.5rem 0;font-size:1.1rem;">'
            'Awaiting the first soul…</div>'
        )

        if soul_count == 0:
            counter_line = (
                '<div style="font-family:\'Cormorant Garamond\',serif;font-style:italic;'
                'font-size:clamp(1rem,1.8vw,1.6rem);color:#8B6F2E;text-align:center;'
                'margin:0.3rem 0;">Be the first to enter</div>'
            )
        else:
            counter_line = (
                f'<div class="attract-soul-counter">'
                f'✦ &nbsp; {soul_count} &nbsp; {"SOUL" if soul_count == 1 else "SOULS"} '
                f'HAVE ENTERED THE VALLEY &nbsp; ✦</div>'
            )

        st.markdown(f"""
<div class="attract-overlay">
  <!-- Title -->
  <div style="text-align:center;margin-bottom:0.5rem;">
    <div style="font-family:'Cinzel',serif;font-weight:700;
                font-size:clamp(1.1rem,2.8vw,2.4rem);letter-spacing:0.25em;color:#C9A961;">
      VALLIS · SIMVLACRI
    </div>
    <div style="font-family:'Cormorant Garamond',serif;font-style:italic;
                font-size:clamp(0.85rem,1.2vw,1.15rem);letter-spacing:0.2em;
                color:#8B6F2E;margin-top:0.3rem;">
      The Valley of Likeness
    </div>
  </div>

  <!-- Divider -->
  <div style="color:#C9A961;letter-spacing:0.3em;opacity:0.4;font-size:1rem;margin:0.3rem 0;">
    ❧ · · · ❧
  </div>

  <!-- Concept blurb -->
  <div style="font-family:'Cormorant Garamond',serif;font-style:italic;
              font-size:clamp(0.9rem,1.3vw,1.25rem);color:#E0D0B0;line-height:1.7;
              text-align:center;max-width:70%;margin:0.4rem auto;">
    In 1970, roboticist Masahiro Mori described the <em>uncanny valley</em> —
    the point where a human likeness becomes too real and tips into revulsion.
    This installation measures your descent in real time.
  </div>

  <!-- Soul counter -->
  <div style="margin:0.6rem 0 0.2rem;">
    {counter_line}
  </div>

  <!-- Aggregate graph -->
  {graph_tag}

  <!-- Divider -->
  <div style="color:#C9A961;letter-spacing:0.3em;opacity:0.4;font-size:1rem;margin:0.3rem 0;">
    ❧ · · · ❧
  </div>

  <!-- Call to action -->
  <div style="font-family:'Cinzel',serif;font-weight:700;
              font-size:clamp(0.85rem,1.6vw,1.4rem);letter-spacing:0.2em;
              color:#C9A961;text-align:center;">
    RAISE BOTH HANDS TO ENTER THE VALLEY
  </div>
</div>
""", unsafe_allow_html=True)

    else:
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

  <aside class="howitworks-panel">

    <div class="howitworks-title">VALLIS SIMULACRI</div>
    <div style="font-family:'Cormorant Garamond',serif;font-style:italic;
                font-size:clamp(0.8rem,0.95vw,1rem);color:#8B6F2E;
                text-align:center;letter-spacing:0.1em;margin-bottom:0.7rem;">
      The Valley of Likeness
    </div>

    <div class="howitworks-step" style="line-height:1.65;margin-bottom:0.7rem;">
      In 1970, roboticist Masahiro Mori described the <em>uncanny valley</em>:
      as a human likeness grows more realistic, our sense of familiarity rises —
      until it crosses a threshold and plunges into revulsion. Almost human
      is worse than not human at all.
    </div>

    <div class="howitworks-step" style="line-height:1.65;margin-bottom:0.8rem;">
      This installation tests that threshold. A classical artwork is fed into
      an AI, whose output is fed back in — again and again. Each cycle the
      image drifts further from the original. Your face is read throughout.
    </div>

    <div style="border-top:1px solid rgba(201,169,97,0.25);margin:0.6rem 0 0.7rem;"></div>

    <div style="font-family:'Cinzel',serif;font-size:clamp(0.6rem,0.78vw,0.8rem);
                letter-spacing:0.18em;color:#C9A961;margin-bottom:0.5rem;">
      WHAT WILL HAPPEN
    </div>
    <div class="howitworks-step"><strong>I.</strong> A classical work appears before you</div>
    <div class="howitworks-step"><strong>II.</strong> It morphs through 100 AI feedback loops over 30 seconds</div>
    <div class="howitworks-step"><strong>III.</strong> Your facial micro-expressions are analysed in real time</div>
    <div class="howitworks-step"><strong>IV.</strong> A Latin verdict and your emotional descent are revealed</div>

    <div style="border-top:1px solid rgba(201,169,97,0.25);margin:0.75rem 0 0.6rem;"></div>

    <div style="font-family:'Cinzel',serif;font-size:clamp(0.6rem,0.78vw,0.8rem);
                letter-spacing:0.18em;color:#C9A961;margin-bottom:0.5rem;">
      TO BEGIN
    </div>
    <div class="howitworks-step" style="line-height:1.6;">
      Stand within arm's reach of the screen.
      When you are ready, <strong style="color:#E8C87A;">raise both hands</strong>
      above your shoulders and hold them there for two seconds.
      The experience lasts approximately one minute.
    </div>

    <div style="border-top:1px solid rgba(201,169,97,0.25);margin:0.75rem 0 0.6rem;"></div>

    <div style="font-family:'Cinzel',serif;font-size:clamp(0.55rem,0.72vw,0.75rem);
                letter-spacing:0.15em;color:#8B6F2E;margin-bottom:0.35rem;">
      PRIVACY
    </div>
    <div class="howitworks-step" style="font-size:clamp(0.75rem,0.9vw,0.95rem);line-height:1.5;color:#8B9070;">
      No video is recorded or stored. Emotion analysis runs locally on this
      device. Only an anonymous score and aggregate statistics are saved.
    </div>

    <div style="background:rgba(139,34,34,0.18);border:1px solid rgba(139,34,34,0.45);
                border-radius:4px;padding:0.5rem 0.7rem;margin-top:0.65rem;">
      <div style="font-family:'Cinzel',serif;font-size:clamp(0.55rem,0.75vw,0.78rem);
                  letter-spacing:0.15em;color:#CC6666;margin-bottom:0.25rem;">
        &#9888; CONTENT WARNING
      </div>
      <div class="howitworks-step" style="color:#E0B0B0;margin:0;
                  font-size:clamp(0.75rem,0.9vw,0.95rem);line-height:1.5;">
        Images become progressively distorted. Some viewers find the results
        unsettling. Raising both hands constitutes your consent to participate.
      </div>
    </div>

  </aside>

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

elif phase == "INTRO":
    artwork = st.session_state.current_artwork
    base_url = f"/app/static/frames/{artwork['slug']}/0000.png"
    st.markdown(f"""
<div class="gallery-overlay" style="padding:0;">
  <img src="{base_url}" style="position:absolute;top:0;left:0;width:100%;height:100%;
                                object-fit:contain;z-index:1;" />

  <!-- Gilt frame border -->
  <div style="position:absolute;top:8px;left:8px;right:8px;bottom:8px;
              border:3px solid #C9A961;
              box-shadow:0 0 0 1px #8B6F2E,inset 0 0 0 1px #8B6F2E,
                         0 0 30px rgba(201,169,97,0.15),inset 0 0 30px rgba(201,169,97,0.08);
              pointer-events:none;z-index:10;"></div>

  <!-- Top: title -->
  <div style="position:absolute;top:0;left:0;right:0;z-index:5;
              background:linear-gradient(rgba(28,20,16,0.92) 0%,rgba(28,20,16,0.55) 70%,transparent 100%);
              padding:3vh 4vw 6vh;text-align:center;">
    <div style="font-family:'Cormorant Garamond',serif;font-style:italic;
                font-size:clamp(0.85rem,1.3vw,1.25rem);letter-spacing:0.3em;
                color:#8B6F2E;margin-bottom:0.6rem;">
      THIS IS
    </div>
    <div style="font-family:'Cinzel',serif;font-weight:700;
                font-size:clamp(1.3rem,3.5vw,2.8rem);letter-spacing:0.15em;color:#E8C87A;
                text-shadow:0 3px 18px rgba(0,0,0,0.85);">
      {artwork['title']}
    </div>
  </div>

  <!-- Bottom: AI explanation -->
  <div style="position:absolute;bottom:0;left:0;right:0;z-index:5;
              background:linear-gradient(transparent,rgba(28,20,16,0.85) 30%,rgba(28,20,16,0.97));
              padding:6vh 8vw 4vh;text-align:center;">
    <div style="font-family:'Cormorant Garamond',serif;
                font-size:clamp(1.05rem,1.8vw,1.7rem);line-height:1.6;
                color:#E0D0B0;max-width:64rem;margin:0 auto;">
      We will now give this picture to an
      <span style="font-family:'Cinzel',serif;font-weight:700;letter-spacing:0.18em;color:#C9A961;">AI</span>.
      It will try to recreate the same picture &mdash;
      <span style="color:#E8C87A;font-weight:600;">over 100 times</span>.
    </div>
    <div style="font-family:'Cormorant Garamond',serif;font-style:italic;
                font-size:clamp(0.95rem,1.5vw,1.4rem);
                color:#8B6F2E;margin-top:1.2rem;letter-spacing:0.15em;">
      Let us see what the AI does.
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

elif phase == "MORPHING":
    artwork      = st.session_state.current_artwork
    emotions     = camera_state.latest_emotions
    total_frames = len(artwork["frames"]) - 1

    # Stable HTML — same string every rerun, so React keeps the iframe mounted
    # and the JS animation runs uninterrupted for the full 30s.
    components.html(
        _morphing_player_html(
            stem=artwork["slug"],
            total_frames=total_frames,
            duration=MORPHING_DURATION,
            phase_start=st.session_state.phase_entered_at,
            title=artwork["title"],
        ),
        height=1080,
    )

    # Live emotion bars — separate Streamlit overlay, re-renders each tick on
    # top of the iframe (z-index higher than the iframe's 9999).
    bars = ""
    for eng, val in sorted(emotions.items(), key=lambda x: -x[1])[:5]:
        label_name = EMOTION_LATIN.get(eng, eng.capitalize())
        pct = round(val * 100, 1)
        bars += (
            f'<div style="margin:0.3rem 0;">'
            f'<div style="display:flex;justify-content:space-between;'
            f'font-family:\'Cinzel\',serif;font-size:clamp(0.8rem,1.1vw,1.1rem);'
            f'letter-spacing:0.07em;color:#C9A961;margin-bottom:3px;">'
            f'<span>{label_name}</span><span>{pct}%</span></div>'
            f'<div style="height:clamp(5px,0.8vw,9px);background:rgba(201,169,97,0.15);'
            f'border-radius:5px;overflow:hidden;">'
            f'<div style="width:{pct}%;height:100%;'
            f'background:linear-gradient(90deg,#8B6F2E,#E8C87A);'
            f'border-radius:5px;transition:width 0.2s linear;"></div></div></div>'
        )

    if not bars:
        bars = (
            '<div style="font-family:\'Cormorant Garamond\',serif;font-style:italic;'
            'color:#8B6F2E;text-align:center;">Reading…</div>'
        )

    st.markdown(f"""
<div class="morphing-emotion-overlay">
  <div style="font-family:'Cinzel',serif;font-size:clamp(0.65rem,0.85vw,0.85rem);
              letter-spacing:0.2em;color:#8B6F2E;text-align:center;margin-bottom:0.6rem;">
    YOUR EMOTIONS
  </div>
  {bars}
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

    # ── Two thumbnails: original + final frame ──────────────────────────────
    slug      = artwork["slug"]
    first_url = f"/app/static/frames/{slug}/0000.png"
    last_url  = f"/app/static/frames/{slug}/{len(artwork['frames']) - 1:04d}.png"

    graph_tag = (
        f'<img src="data:image/png;base64,{graph_b64}" '
        f'style="width:100%;max-height:34vh;height:auto;border-radius:4px;'
        f'border:1px solid #3D2810;display:block;" />'
        if graph_b64 else
        '<div style="color:#8B6F2E;font-style:italic;text-align:center;padding:1rem;">'
        'No emotion data recorded.</div>'
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
  <div style="text-align:center;margin-bottom:1.2vh;width:100%;flex-shrink:0;">
    <div style="font-family:'Cinzel',serif;font-weight:700;
                font-size:clamp(0.85rem,1.4vw,1.3rem);letter-spacing:0.3em;color:#8B6F2E;">
      YOUR EMOTIONAL DESCENT
    </div>
    <div style="font-family:'Cormorant Garamond',serif;font-style:italic;
                font-size:clamp(0.9rem,1.2vw,1.2rem);color:#8B6F2E;opacity:0.8;margin-top:0.2rem;">
      {artwork['title']}
    </div>
  </div>

  <!-- Before / after: original + final frame, side-by-side -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5vw;width:100%;
              flex-shrink:0;margin-bottom:1.5vh;">
    <div style="text-align:center;">
      <div style="font-family:'Cinzel',serif;font-size:clamp(0.6rem,0.85vw,0.85rem);
                  letter-spacing:0.22em;color:#8B6F2E;margin-bottom:0.4rem;">
        ORIGINAL
      </div>
      <div style="border:2px solid #3D2810;padding:4px;background:#0a0806;">
        <img src="{first_url}" style="width:100%;height:28vh;object-fit:contain;display:block;" />
      </div>
    </div>
    <div style="text-align:center;">
      <div style="font-family:'Cinzel',serif;font-size:clamp(0.6rem,0.85vw,0.85rem);
                  letter-spacing:0.22em;color:#8B6F2E;margin-bottom:0.4rem;">
        AFTER 100 ITERATIONS
      </div>
      <div style="border:2px solid #3D2810;padding:4px;background:#0a0806;">
        <img src="{last_url}" style="width:100%;height:28vh;object-fit:contain;display:block;" />
      </div>
    </div>
  </div>

  <!-- Emotion graph -->
  <div style="width:100%;flex-shrink:0;margin-bottom:1.5vh;">
    {graph_tag}
  </div>

  <!-- Verdict seal -->
  <div style="display:flex;justify-content:center;flex-shrink:0;">
    <div class="seal-medallion" style="
                width:clamp(110px,15vw,170px);height:clamp(110px,15vw,170px);
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
