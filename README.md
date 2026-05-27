# Vallis Simulacri
### *The Valley of Likeness* — Interactive Gallery Installation

> *At what point does a human find their own species wrong?*

---

## TL;DR — What this project does (for the confused colleague)

**In one sentence:** Visitors stand in front of a giant screen, raise their hands, and watch a classical painting get slowly distorted by AI while their facial micro-expressions are silently recorded; at the end a "verdict" tells them how far they fell into the uncanny valley.

**What runs:** A FastAPI + React web app on a PC connected to a camera. The browser captures video, sends frames over WebSocket to a Python backend, which runs face/emotion analysis in real time, drives a state machine through four phases, and pushes results back to the frontend.

**How the distorted images are made:** A one-time offline pipeline (`uncanny_maker`) runs each painting through Stable Diffusion img2img 100 times in a feedback loop — each output becomes the next input. Errors compound; the result is a body that is simultaneously too-human and deeply wrong.

**What "uncanny valley" means here:** Roboticist Masahiro Mori (1970) described how a near-perfect human likeness triggers revulsion more than a clearly non-human one. We measure that response in real visitors, one face at a time.

---

## The Experience (Visitor Perspective)

```
 IDLE        65-inch portrait TV shows a mirror view of visitors.
             Aggregate data from previous visitors scrolls past every 30 s.
               │
               │  visitor raises both hands for 1.5 s
               ▼
 INTRO       "THIS IS — [artwork title]"
             Full-screen original painting for 8 s.
             Text: "We will now give this picture to an AI. It will try to
             recreate the same picture — over 100 times."
               │
               ▼
 MORPHING    The painting slowly transforms through 100 AI-distorted frames (30 s).
             Live emotion bars (happy, sad, fear, disgust, …) float on the right —
             the visitor can see their face being read in real time.
               │
               ▼
 RECAP       Before/after thumbnails side by side.
             Emotion-over-time line chart.
             A wax-seal verdict:
               VALLIS  — you fell into the valley
               LIMEN   — you stood at the threshold
               FIRMA   — you held your ground
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
│   ├── catalog/            Artwork loader — maps source images to 100-frame sequences
│   ├── data/               SQLAlchemy ORM, SQLite persistence, aggregate analytics
│   ├── frontend/           React + TypeScript + Vite UI
│   │   └── src/
│   │       ├── hooks/      useWebSocket.ts, useCamera.ts
│   │       └── components/ IdlePhase, IntroPhase, MorphingPhase, RecapPhase
│   ├── start.sh            Production launcher (builds frontend, starts server, opens kiosk)
│   ├── install.sh          One-time Ubuntu/Debian setup
│   └── config.py           All tunable parameters (timings, thresholds, weights)
│
├── uncanny_maker/          Offline preprocessing pipeline (run once)
│   ├── iterate_degrade.py  Main script — 100-frame iterative Stable Diffusion loop
│   ├── download_human_figures.py  Met Museum API scraper
│   ├── core/               Stable Diffusion img2img + LLaVA prompt generation
│   └── catalog/            Source artwork JPEGs (downloaded by scraper)
│
├── _prototypes/            Early experiments (not production code)
└── docs/
    ├── CONCEPT.md          Philosophy, the uncanny valley, model collapse as art
    ├── ARCHITECTURE.md     Technical architecture, data flow, all modules explained
    └── PIPELINE.md         Preprocessing pipeline — how the 100-frame sequences are made
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

# Step 2 — run each image through 100 Stable Diffusion feedback iterations
ollama serve &          # optional — provides better prompts via LLaVA
python iterate_degrade.py
```

Output: `uncanny_maker/catalog_iterations/{artwork_slug}/0000.png … 0100.png`

Both scripts are **fully resumable** — interrupted runs continue from where they stopped.

Estimated time per artwork: ~8–12 min on Apple M-series, ~3–6 min on NVIDIA GPU.

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
| Display | 65-inch TV, portrait orientation (112:199 aspect ratio) |

---

## Verdict System

At the end of each 30-second session the visitor's emotion samples are averaged and scored:

```
score = normalize( Σ (emotion_probability × weight) )   →   [0, 1]
```

| Emotion | Weight | Rationale |
|---------|--------|-----------|
| Disgust | +1.0 | Core uncanny signal |
| Fear | +0.9 | Threat response |
| Surprise | +0.4 | Ambiguous |
| Sad | +0.2 | Mild negative |
| Angry | −0.1 | Neutral |
| Neutral | −0.4 | No reaction |
| Happy | −1.0 | Counter-signal |

| Score | Verdict | Meaning |
|-------|---------|---------|
| ≥ 0.60 | **VALLIS** | Fell into the uncanny valley |
| 0.40 – 0.59 | **LIMEN** | At the threshold |
| < 0.40 | **FIRMA** | Unaffected, stable ground |

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
- **Layout:** `112:199` portrait column centred on the landscape display with black bars
- **Text scale:** CSS `clamp()` throughout — readable from phone screen to 65-inch projection
