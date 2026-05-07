"""
Portrait prototype — 30-second uncanny progression.
A marble statue becomes progressively wrong every 3 seconds.
Fake emotion-scan HUD overlaid on the image.

Run:  streamlit run uncanny_proto.py
"""

import io
import time
import base64
import pathlib

import numpy as np
import streamlit as st
from PIL import Image, ImageFilter

# ── Config ─────────────────────────────────────────────────────────────────────
STEP_SECONDS = 3
TOTAL_STEPS  = 10

IMAGE_PATH = (
    pathlib.Path(__file__).parent
    / "uncanny_maker" / "catalog"
    / "Marble_portrait_of_the_emperor_Caracalla_253592.jpg"
)

STAGE_NAMES = [
    "ORIGINALE",
    "LEVE  ·  I",
    "LEVE  ·  II",
    "LEVE  ·  III",
    "MEDIA  ·  I",
    "MEDIA  ·  II",
    "MEDIA  ·  III",
    "PROFVNDA  ·  I",
    "PROFVNDA  ·  II",
    "PROFVNDA  ·  III",
    "ABYSSVM",
]

# ── Fake emotion keyframes ──────────────────────────────────────────────────────
# Values shift from calm/curious toward disgust/fear as the image grows uncanny.
# Format: {step: {emotion: probability, ...}}
_EMOTION_KF = {
    0:  {"Laetitia": 0.46, "Tranquillitas": 0.31, "Admiratio": 0.13, "Fastidium": 0.05, "Timor": 0.03, "Tristitia": 0.02},
    2:  {"Laetitia": 0.29, "Tranquillitas": 0.35, "Admiratio": 0.18, "Fastidium": 0.10, "Timor": 0.05, "Tristitia": 0.03},
    4:  {"Laetitia": 0.14, "Tranquillitas": 0.25, "Admiratio": 0.17, "Fastidium": 0.24, "Timor": 0.14, "Tristitia": 0.06},
    7:  {"Laetitia": 0.05, "Tranquillitas": 0.11, "Admiratio": 0.08, "Fastidium": 0.40, "Timor": 0.27, "Tristitia": 0.09},
    10: {"Laetitia": 0.01, "Tranquillitas": 0.05, "Admiratio": 0.03, "Fastidium": 0.48, "Timor": 0.34, "Tristitia": 0.09},
}
_KF_STEPS = sorted(_EMOTION_KF)
_EMOTIONS  = list(_EMOTION_KF[0])


def _emotion_values(step: int) -> dict[str, float]:
    """Interpolate emotion probabilities for a given step."""
    lo = max(k for k in _KF_STEPS if k <= step)
    hi = min(k for k in _KF_STEPS if k >= step)
    if lo == hi:
        base = dict(_EMOTION_KF[lo])
    else:
        t = (step - lo) / (hi - lo)
        base = {e: _EMOTION_KF[lo][e] * (1 - t) + _EMOTION_KF[hi][e] * t for e in _EMOTIONS}

    # Tiny deterministic jitter so it looks live
    rng = np.random.default_rng(step * 17 + int(time.time()) % 7)
    noise = rng.uniform(-0.018, 0.018, len(_EMOTIONS))
    vals = {e: max(0.0, base[e] + noise[i]) for i, e in enumerate(_EMOTIONS)}
    total = sum(vals.values())
    return {e: v / total for e, v in vals.items()}


# ── CSS ────────────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400;1,600&display=swap');

:root {
    --ink:        #1C1410;
    --gold:       #C9A961;
    --gold-bright:#E8C87A;
    --gold-dark:  #8B6F2E;
    --parchment:  #F4E8D0;
}

html, body, [data-testid="stApp"] {
    background-color: var(--ink) !important;
    overflow: hidden;
}

[data-testid="stMainBlockContainer"] {
    max-width: 460px !important;
    padding: 1.5rem 1rem 1.5rem !important;
    margin: 0 auto;
}

#MainMenu, header, footer,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] {
    display: none !important;
}

.app-title {
    font-family: 'Cinzel', serif;
    font-weight: 900;
    font-size: 1.4rem;
    letter-spacing: 0.22em;
    color: var(--gold);
    text-align: center;
    margin-bottom: 0.15rem;
}
.app-subtitle {
    font-family: 'Cormorant Garamond', serif;
    font-style: italic;
    font-size: 0.95rem;
    color: var(--gold-dark);
    text-align: center;
    margin-bottom: 0.6rem;
}
.stage-title {
    font-family: 'Cinzel', serif;
    font-weight: 700;
    font-size: 1rem;
    letter-spacing: 0.28em;
    color: var(--gold-dark);
    text-align: center;
    margin-bottom: 0.55rem;
}

/* ── Image + overlay wrapper ── */
.scan-wrap {
    position: relative;
    display: block;
    line-height: 0;
    border: 3px solid var(--gold);
    box-shadow:
        0 0 0 1px var(--gold-dark),
        0 0 0 5px var(--ink),
        0 0 0 7px var(--gold-dark),
        0 0 35px rgba(201,169,97,0.18);
}
.scan-wrap img {
    display: block;
    width: 100%;
    height: auto;
}

/* ── Face-detection bracket ── */
.face-box {
    position: absolute;
    top: 7%;
    left: 19%;
    width: 62%;
    height: 64%;
    border: 1px dashed rgba(201,169,97,0.45);
    box-sizing: border-box;
}
.face-box .c {
    position: absolute;
    width: 13px; height: 13px;
    border-color: var(--gold);
    border-style: solid;
    border-width: 0;
}
.face-box .tl { top:-2px; left:-2px;    border-top-width:2.5px; border-left-width:2.5px; }
.face-box .tr { top:-2px; right:-2px;   border-top-width:2.5px; border-right-width:2.5px; }
.face-box .bl { bottom:-2px; left:-2px; border-bottom-width:2.5px; border-left-width:2.5px; }
.face-box .br { bottom:-2px; right:-2px;border-bottom-width:2.5px; border-right-width:2.5px; }

/* ── Scan sweep line ── */
@keyframes sweep {
    0%   { top: 7%;   opacity: 0.9; }
    90%  { top: 71%;  opacity: 0.9; }
    100% { top: 7%;   opacity: 0;   }
}
.scan-line {
    position: absolute;
    left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg,
        transparent 0%, rgba(201,169,97,0.55) 30%,
        rgba(201,169,97,0.85) 50%, rgba(201,169,97,0.55) 70%, transparent 100%);
    animation: sweep 2.4s linear infinite;
    pointer-events: none;
}

/* ── Scan-status badge ── */
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.25} }
.scan-badge {
    position: absolute;
    top: 8px;
    right: 10px;
    font-family: 'Cinzel', serif;
    font-size: 0.52rem;
    letter-spacing: 0.22em;
    color: rgba(201,169,97,0.75);
    display: flex;
    align-items: center;
    gap: 5px;
}
.scan-dot {
    width: 5px; height: 5px;
    border-radius: 50%;
    background: var(--gold);
    animation: blink 1.1s ease-in-out infinite;
}

/* ── Sample-count badge (top-left) ── */
.sample-badge {
    position: absolute;
    top: 8px;
    left: 10px;
    font-family: 'Cinzel', serif;
    font-size: 0.48rem;
    letter-spacing: 0.14em;
    color: rgba(201,169,97,0.45);
}

/* ── Emotion panel ── */
.emo-panel {
    position: absolute;
    bottom: 0; left: 0; right: 0;
    background: linear-gradient(to top,
        rgba(20,14,10,0.94) 0%,
        rgba(20,14,10,0.78) 65%,
        transparent 100%);
    padding: 1.6rem 0.85rem 0.75rem;
}
.emo-header {
    font-family: 'Cinzel', serif;
    font-size: 0.55rem;
    letter-spacing: 0.3em;
    color: rgba(201,169,97,0.45);
    text-align: center;
    margin-bottom: 0.45rem;
}
.emo-row {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    margin-bottom: 0.28rem;
}
.emo-name {
    font-family: 'Cinzel', serif;
    font-size: 0.58rem;
    letter-spacing: 0.05em;
    color: var(--gold);
    width: 82px;
    flex-shrink: 0;
}
.emo-track {
    flex: 1;
    height: 4px;
    background: rgba(201,169,97,0.1);
    border-radius: 2px;
    overflow: hidden;
}
.emo-fill {
    height: 100%;
    background: linear-gradient(90deg, #5A3E1A, #E8C87A);
    border-radius: 2px;
}
.emo-pct {
    font-family: 'Cinzel', serif;
    font-size: 0.52rem;
    color: rgba(201,169,97,0.45);
    width: 34px;
    text-align: right;
    flex-shrink: 0;
}

/* ── Progress section ── */
.prog-wrap { margin-top: 0.75rem; }
.prog-track {
    height: 2px;
    background: rgba(201,169,97,0.1);
    border-radius: 2px;
    overflow: hidden;
}
.prog-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--gold-dark), var(--gold));
    border-radius: 2px;
}
.prog-ticks {
    display: flex;
    justify-content: space-between;
    margin-top: 0.35rem;
    font-family: 'Cinzel', serif;
    font-size: 0.55rem;
    letter-spacing: 0.07em;
    color: #3D2810;
}
.dot-row {
    display: flex;
    justify-content: center;
    gap: 6px;
    margin-top: 0.6rem;
}
.dot { width:6px; height:6px; border-radius:50%; background:#2A1E0E; display:inline-block; }
.dot.active { background:var(--gold); box-shadow:0 0 6px rgba(201,169,97,0.55); }
.dot.done   { background:var(--gold-dark); }
</style>
"""


# ── Image transformation ───────────────────────────────────────────────────────
def _distort(img: Image.Image, step: int) -> Image.Image:
    t = step / TOTAL_STEPS
    arr = np.array(img, dtype=np.float32)
    h, w = arr.shape[:2]

    # 1. Stone-to-flesh warmth
    warm = min(t * 1.8, 0.8) * 22
    arr[:, :, 0] += warm
    arr[:, :, 1] += warm * 0.45
    arr[:, :, 2] -= warm * 0.7

    # 2. Skin smoothing (plastic/wax)
    blur_r = t * 4.2
    if blur_r > 0.3:
        blurred = np.array(
            Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
            .filter(ImageFilter.GaussianBlur(blur_r)),
            dtype=np.float32,
        )
        alpha = min(t * 0.85, 0.78)
        arr = arr * (1.0 - alpha) + blurred * alpha

    # 3. Wax desaturation + sickly cast
    if t > 0.25:
        wax = (t - 0.25) / 0.75
        grey = arr.mean(axis=2, keepdims=True)
        arr = arr * (1.0 - wax * 0.48) + grey * (wax * 0.48)
        arr[:, :, 1] += wax * 14
        arr[:, :, 2] -= wax * 9

    # 4. Contrast crush
    if t > 0.35:
        c = 1.0 + (t - 0.35) * 1.1
        arr = (arr - 127.5) * c + 127.5

    # 5. Creeping vignette
    if t > 0.45:
        s = (t - 0.45) / 0.55 * 0.75
        cy, cx = h / 2.0, w / 2.0
        Y, X = np.ogrid[:h, :w]
        dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
        vign = np.clip(1.0 - s * (dist / np.sqrt(cx ** 2 + cy ** 2)), 0.08, 1.0)
        arr *= vign[:, :, np.newaxis]

    # 6. Chromatic aberration
    if t > 0.55:
        px = int((t - 0.55) / 0.45 * 16)
        if px >= 1:
            r = np.roll(arr[:, :, 0],  px, axis=1)
            b = np.roll(arr[:, :, 2], -px, axis=1)
            arr = np.stack([r, arr[:, :, 1], b], axis=2)

    # 7. Scanline flicker
    if t > 0.75:
        sl = (t - 0.75) / 0.25
        mask = np.ones(h, dtype=np.float32)
        mask[::3] = 1.0 - sl * 0.45
        arr *= mask[:, np.newaxis, np.newaxis]

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


PROTO_FRAMES_DIR = pathlib.Path(__file__).parent / "proto_frames"


def _sd_frames_available() -> bool:
    """True when make_proto_frames.py has been run and all 11 files exist."""
    if not PROTO_FRAMES_DIR.exists():
        return False
    expected = ["00_original.jpg"] + [
        f"{i:02d}_s{round(s*100):03d}.jpg"
        for i, s in enumerate(
            [0.12, 0.19, 0.25, 0.32, 0.38, 0.45, 0.52, 0.58, 0.65, 0.72], start=1
        )
    ]
    return all((PROTO_FRAMES_DIR / name).exists() for name in expected)


@st.cache_data(show_spinner=False)
def build_frames(path: str) -> list[bytes]:
    # ── Use real SD frames if they exist ──────────────────────────────────────
    if _sd_frames_available():
        names = ["00_original.jpg"] + [
            f"{i:02d}_s{round(s*100):03d}.jpg"
            for i, s in enumerate(
                [0.12, 0.19, 0.25, 0.32, 0.38, 0.45, 0.52, 0.58, 0.65, 0.72], start=1
            )
        ]
        return [(PROTO_FRAMES_DIR / n).read_bytes() for n in names]

    # ── Fallback: PIL distortions ─────────────────────────────────────────────
    src = Image.open(path).convert("RGB")
    ow, oh = src.size
    if ow / oh > 2 / 3:
        nw = int(oh * 2 / 3)
        left = (ow - nw) // 2
        src = src.crop((left, 0, left + nw, oh))
    src = src.resize((480, 720), Image.LANCZOS)
    out = []
    for step in range(TOTAL_STEPS + 1):
        frame = _distort(src.copy(), step)
        buf = io.BytesIO()
        frame.save(buf, format="JPEG", quality=90)
        out.append(buf.getvalue())
    return out


def _emotion_values(step: int) -> dict[str, float]:
    lo = max(k for k in _KF_STEPS if k <= step)
    hi = min(k for k in _KF_STEPS if k >= step)
    if lo == hi:
        base = dict(_EMOTION_KF[lo])
    else:
        t = (step - lo) / (hi - lo)
        base = {e: _EMOTION_KF[lo][e] * (1 - t) + _EMOTION_KF[hi][e] * t for e in _EMOTIONS}
    rng = np.random.default_rng(step * 17 + int(time.time()) % 7)
    noise = rng.uniform(-0.018, 0.018, len(_EMOTIONS))
    vals = {e: max(0.0, base[e] + noise[i]) for i, e in enumerate(_EMOTIONS)}
    total = sum(vals.values())
    return {e: v / total for e, v in vals.items()}


# ── Session init ───────────────────────────────────────────────────────────────
if "step" not in st.session_state:
    st.session_state.step    = 0
    st.session_state.step_at = time.time()
    st.session_state.samples = 0

st.set_page_config(page_title="Vallis Simulacri", page_icon="⚗", layout="centered")
st.markdown(CSS, unsafe_allow_html=True)

using_sd = _sd_frames_available()
frames   = build_frames(str(IMAGE_PATH))

step    = st.session_state.step
pct     = int(step / TOTAL_STEPS * 100)
name    = STAGE_NAMES[step]
emotions = _emotion_values(step)
samples  = st.session_state.samples

# ── Build emotion rows HTML ────────────────────────────────────────────────────
emo_rows = ""
for emotion, val in sorted(emotions.items(), key=lambda x: -x[1]):
    bar_w = int(val * 100)
    pct_s = f"{val * 100:.1f}%"
    emo_rows += (
        f"<div class='emo-row'>"
        f"<span class='emo-name'>{emotion}</span>"
        f"<div class='emo-track'><div class='emo-fill' style='width:{bar_w}%'></div></div>"
        f"<span class='emo-pct'>{pct_s}</span>"
        f"</div>"
    )

# ── Build image + overlay HTML ─────────────────────────────────────────────────
img_b64 = base64.b64encode(frames[step]).decode()

scan_html = f"""
<div class='app-title'>VALLIS · SIMVLACRI</div>
<div class='app-subtitle'>the valley of likeness</div>
<div class='stage-title'>{name}</div>

<div class='scan-wrap'>
  <img src='data:image/jpeg;base64,{img_b64}' />

  <!-- sweeping scan line -->
  <div class='scan-line'></div>

  <!-- face-detection bracket -->
  <div class='face-box'>
    <div class='c tl'></div><div class='c tr'></div>
    <div class='c bl'></div><div class='c br'></div>
  </div>

  <!-- status badges -->
  <div class='scan-badge'><div class='scan-dot'></div>SCANNING</div>
  <div class='sample-badge'>SAMPLE #{samples:04d} · {'SD' if using_sd else 'PIL'}</div>

  <!-- emotion panel -->
  <div class='emo-panel'>
    <div class='emo-header'>ANIMA · TVSCITVR</div>
    {emo_rows}
  </div>
</div>

<div class='prog-wrap'>
  <div class='prog-track'>
    <div class='prog-fill' style='width:{pct}%'></div>
  </div>
  <div class='prog-ticks'>
    <span>ORIGINALE</span><span>LEVE</span><span>MEDIA</span>
    <span>PROFVNDA</span><span>ABYSSVM</span>
  </div>
</div>
<div class='dot-row'>
  {''.join(
      f"<span class='dot {'active' if i == step else 'done' if i < step else ''}'></span>"
      for i in range(TOTAL_STEPS + 1)
  )}
</div>
"""

st.markdown(scan_html, unsafe_allow_html=True)

# ── Timing ─────────────────────────────────────────────────────────────────────
elapsed   = time.time() - st.session_state.step_at
remaining = STEP_SECONDS - elapsed
if remaining > 0:
    time.sleep(remaining)

st.session_state.step    = (step + 1) % (TOTAL_STEPS + 1)
st.session_state.step_at = time.time()
st.session_state.samples += 1
st.rerun()
