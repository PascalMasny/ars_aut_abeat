# Vallis Simulacri
### *The Valley of Likeness* — Interactive Gallery Installation

> *At what point does a human find their own species wrong?*

---

## TL;DR — What this project does (for the confused colleague)

**In one sentence:** Visitors look at a classical painting while their emotional baseline is read, then walk through ten increasingly AI-distorted versions of it; the picture that provokes their strongest reaction becomes the verdict — everything before it was art (**ARS**), from there on it no longer is (**ABEAT**).

**What runs:** A FastAPI + React web app on a PC connected to a camera. The browser captures video, sends frames over WebSocket to a Python backend, which runs face/emotion analysis in real time, drives a state machine through four phases, and pushes results back to the frontend.

**How the distorted images are made:** A one-time offline pipeline (`uncanny_maker`) generates 10 pictures per painting with Stable Diffusion img2img in two phases: pictures 1–5 each directly from the original with a gentle strength ramp (subtle, coherent drift), pictures 6–10 chained output-to-input — true model collapse, where reconstruction errors compound and the painting disintegrates. The result is a body that is simultaneously too-human and deeply wrong.

**What "uncanny valley" means here:** Roboticist Masahiro Mori (1970) described how a near-perfect human likeness triggers revulsion more than a clearly non-human one. We measure that response in real visitors, one face at a time.

---

## The Experience (Visitor Perspective)

```
 IDLE        Large display shows a mirror view of visitors.
             Attract screen cycles every 30 s.
               │
               │  visitor raises both hands for 1.5 s
               │  (or presenter presses Space in show mode)
               ▼
 BASELINE    "THIS IS — [artwork title]"
             The untouched original for 19 s with title and description
             to read. Meanwhile the camera reads the visitor's
             face and stores the average as their personal baseline —
             their expression when looking at real art.
               │
               ▼
 GALLERY     Ten AI-degraded pictures, soft crossfade every 3 s (30 s) —
             like walking past ten works in a gallery. Each picture collects
             its own bucket of emotion samples (0.7 s reaction-lag offset).
             Live emotion bars float on the right.
               │
               ▼
 REVEAL      The picture whose bucket deviates most from the baseline is
             the breaking point. Three pictures side by side:
               ORIGINAL        — the human hand
               ARS    (gold)   — the last picture that was still art
               ABEAT  (red)    — the breaking point, strongest reaction
             Below: a reaction curve over all ten pictures.
             "HERE, ART DIED FOR YOU — your strongest reaction:
              picture k of 10. You drew this line — not the machine."
             No reaction at all → ARS MANSIT: it never stopped being art.
               │
               ▼
 IDLE        Resets. Waits for the next visitor.
```

---

## Repository Structure

```
.
├── ars_aut_abeat/          Real-time gallery application (FastAPI + React/Vite)
│   ├── backend/            FastAPI server: WebSocket handler, graph generation
│   ├── core/               Phase state machine, per-session data, verdict scoring
│   ├── vision/             MediaPipe emotion detection, head-pose gaze gate
│   ├── catalog/            Artwork loader — maps source images to 10-picture sequences
│   ├── data/               SQLAlchemy ORM, SQLite persistence, aggregate analytics
│   ├── frontend/           React + TypeScript + Vite UI
│   │   └── src/
│   │       ├── hooks/      useWebSocket.ts, useCamera.ts
│   │       └── components/ IdlePhase, BaselinePhase, GalleryPhase, RevealPhase, SlidesPhase
│   ├── start.sh            Production launcher (builds frontend, starts server, opens kiosk)
│   ├── install.sh          One-time Ubuntu/Debian setup
│   └── config.py           All tunable parameters (timings, thresholds, weights)
│
├── uncanny_maker/          Offline preprocessing pipeline (run once)
│   ├── iterate_degrade.py  Main script — 10 pictures per artwork (5 direct + 5 chained collapse)
│   ├── download_human_figures.py  Met Museum API scraper
│   ├── core/               Stable Diffusion img2img + LLaVA prompt generation
│   └── catalog/            Source artwork JPEGs (downloaded by scraper)
│
├── _prototypes/            Early experiments (not production code)
└── docs/
    ├── CONCEPT.md          Philosophy, the uncanny valley, model collapse as art
    ├── ARCHITECTURE.md     Technical architecture, data flow, all modules explained
    └── PIPELINE.md         Preprocessing pipeline — how the 10-picture sequences are made
```

---

## Quick Start

### Prerequisites

- Python 3.10–3.12 (MediaPipe does not support 3.13+ yet)
- Node.js 18+
- A webcam
- Brave Browser, Chrome, or Chromium (for kiosk mode)

### Ubuntu / Linux (recommended for the actual installation)

```bash
cd ars_aut_abeat
chmod +x install.sh start.sh
./install.sh          # one-time setup: Python venv, Node, system libs, browser
./start.sh            # builds frontend + starts server + opens kiosk browser
```

### macOS (development)

```bash
cd ars_aut_abeat
pip install -r requirements.txt
cd frontend && npm install && cd ..
./start.sh
```

Open `http://localhost:8000` in your browser.

> **First run note:** MediaPipe downloads two model files (~20 MB each) on first startup.
> The app loads immediately; face detection becomes active ~10–30 s later.

### Development mode (hot reload)

```bash
./dev.sh    # uvicorn with --reload + Vite HMR in parallel
            # frontend: http://localhost:5173 (proxies /ws and /frames to :8000)
```

---

## How the Artwork Images Are Made (Offline Pipeline)

Run once before the installation. Requires a GPU (Apple M-series MPS, NVIDIA CUDA, or slow CPU).

```bash
cd uncanny_maker
pip install -r requirements.txt

# Step 1 — download ~200 figurative paintings/sculptures from Met Museum Open Access
python download_human_figures.py

# Step 2 — generate 10 pictures per image:
#          1–5 direct from the original (subtle drift), 6–10 chained model collapse
ollama serve &          # optional — provides better prompts via LLaVA
python iterate_degrade.py
```

Output: `uncanny_maker/catalog_iterations_10/{artwork_slug}/0000.png … 0010.png`

Both scripts are **fully resumable** — interrupted runs continue from where they stopped.

Estimated time per artwork: ~1 min on Apple M-series, ~30 s on NVIDIA GPU.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Uvicorn |
| Frontend | React 18 + TypeScript + Vite |
| Camera transport | WebSocket binary (JPEG frames, browser → server) |
| Computer vision | MediaPipe FaceLandmarker (52 FACS blendshapes) |
| Pose detection | MediaPipe PoseLandmarker (hands-raised trigger) |
| Head pose | OpenCV `solvePnP` (gaze gate: yaw ≤ 35°, pitch ≤ 30°) |
| Image generation | Stable Diffusion v1.5 via Hugging Face `diffusers` |
| Vision LLM | LLaVA via Ollama (optional — improves SD prompts) |
| Database | SQLite via SQLAlchemy 2.0 |
| Charts | Matplotlib → base64 PNG |
| Art source | Met Museum Open Access API (public domain) |
| Display | Large landscape display / video wall, 16:9 |

---

## Verdict System — the Breaking Point

During BASELINE the visitor's average emotion vector is stored as their personal zero point. During GALLERY each of the 10 pictures collects its own bucket of emotion samples. At reveal time every bucket is compared to the baseline:

```
deviation(picture k) = Σ over emotions  weight[e] × |bucket_avg_k[e] − baseline[e]|
breaking point       = picture with maximum deviation
```

| Emotion | Weight | Rationale |
|---------|--------|-----------|
| Disgust | 1.0 | Core uncanny signal |
| Fear | 0.9 | Threat response |
| Surprise | 0.7 | Strong involuntary reaction |
| Angry | 0.6 | Rejection |
| Sad | 0.5 | Negative shift |
| Happy | 0.5 | A laugh is also a reaction |
| Neutral | 0.2 | Mostly absorbs the others' movement |

Any *change* from the baseline counts as a reaction — the weights only decide how much.

| Condition | Verdict | Meaning |
|-----------|---------|---------|
| max deviation ≥ 0.25 | **VALLIS** | Strong reaction — fell into the valley |
| breaking point exists, < 0.25 | **LIMEN** | Measurable but mild — at the threshold |
| max deviation < 0.08 | **FIRMA** | *ARS MANSIT* — it never stopped being art |

The reveal screen shows the breaking-point picture stamped **ABEAT** (no longer art) next to the picture before it, stamped **ARS** (still art). The visitor — not the machine — drew the line.

---

## Privacy

- No video is stored anywhere.
- Emotion analysis runs entirely on the installation hardware.
- Only anonymous numerical scores are written to the database (no images, no identity).
- The visitor initiates by raising both hands — a deliberate consent gesture.

---

## Documentation

| File | Contents |
|------|----------|
| [`docs/CONCEPT.md`](docs/CONCEPT.md) | Philosophy — uncanny valley, model collapse as artistic medium, Freud, Mori |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System design, WebSocket protocol, vision pipeline, all modules |
| [`docs/PIPELINE.md`](docs/PIPELINE.md) | Preprocessing pipeline — Stable Diffusion loop, LLaVA, degradation mechanics |
| [`ars_aut_abeat/README.md`](ars_aut_abeat/README.md) | App-level reference: quick start, config, state machine, DB schema |

---

## Design Language

Deliberately anachronistic — a 21st-century computer-vision experiment dressed as a 17th-century cabinet of curiosities.

- **Fonts:** Cinzel (inscriptions), Cormorant Garamond (body text), Pinyon Script (flourishes)
- **Palette:** Ink black `#1C1410` · Parchment `#F4E8D0` · Gold `#C9A961` · Burgundy `#6B2C2C`
- **Layout:** `16:9` landscape viewport, letterboxed on non-16:9 screens
- **Text scale:** CSS `clamp()` throughout — readable from phone screen to 65-inch projection
