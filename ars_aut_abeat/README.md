# Vallis Simulacri

**"The Valley of Likeness."** An interactive gallery installation that measures how deeply visitors fall into the uncanny valley when confronted with AI-degraded classical artworks. Facial emotion detection runs in real time and renders a Latin verdict sealed in wax.

Designed for projection on a large display. Visitors see themselves full-screen, raise both hands to enter the valley, then receive a personal and collective verdict.

---

## Quick Start

```bash
# Production — builds frontend once, then serves everything from one process
./start.sh

# Development — backend with hot reload + Vite HMR in two parallel processes
./dev.sh

# Stop all running services
./stop.sh
```

- **Production:** open `http://localhost:8000`
- **Dev:** open `http://localhost:5173` (Vite proxies `/ws` and `/frames` to :8000)

> **First run:** MediaPipe models (~20 MB each) are downloaded automatically on first startup. The face/pose models download in the background on the analysis thread — you will see the app load immediately, but face detection becomes active ~10–30 s later depending on your connection.

---

## Architecture

```
ars_aut_abeat/
├── backend/
│   ├── main.py         ← FastAPI app: WebSocket endpoint, static file serving
│   ├── ws_handler.py   ← GallerySession, singleton processor + state
│   └── graphs.py       ← matplotlib → base64 PNG (recap graph, attract graph)
├── frontend/           ← React + Vite + TypeScript
│   └── src/
│       ├── hooks/
│       │   ├── useCamera.ts      ← getUserMedia, 10 Hz canvas capture
│       │   └── useWebSocket.ts   ← persistent WS, auto-reconnect, ServerState
│       └── components/
│           ├── CameraBackground.tsx  ← always mounted, no phase flicker
│           ├── IdlePhase.tsx         ← mirror overlay + attract screen
│           ├── IntroPhase.tsx        ← artwork reveal + frame preloading
│           ├── MorphingPhase.tsx     ← rAF crossfade over 100 frames
│           └── RecapPhase.tsx        ← before/after thumbnails, graph, seal
├── core/
│   ├── state_machine.py  ← InstallationState dataclass, phase FSM
│   ├── session.py        ← ViewerSession (per-visitor emotion samples)
│   └── verdict.py        ← VALLIS / LIMEN / FIRMA scoring
├── vision/
│   ├── camera.py         ← GalleryProcessor: push_frame(), analysis thread
│   ├── emotion.py        ← MediaPipe blendshapes → 7 emotions (FACS)
│   ├── face_detector.py  ← FaceResult dataclass
│   └── gaze.py           ← head pose → "looking at camera" gate
├── catalog/
│   └── manager.py        ← round-robin artwork picker, singleton
├── data/
│   ├── db.py             ← SQLite init (SQLAlchemy)
│   ├── models.py         ← Artwork, Viewing tables
│   └── stats.py          ← aggregate queries, concordance score
├── config.py             ← all timings, thresholds, paths
├── start.sh              ← production launcher
├── dev.sh                ← dev launcher (uvicorn + Vite in parallel)
└── stop.sh               ← kill all services
```

---

## State Machine

```
IDLE → INTRO (8 s) → MORPHING (30 s) → RECAP (15 s) → IDLE
```

| Phase | Duration | Trigger |
|-------|----------|---------|
| **IDLE** | Indefinite | Both hands raised ≥ 1.5 s |
| **INTRO** | 8 s | Timer — artwork reveal, frames preloaded |
| **MORPHING** | 30 s | Timer — 100-frame rAF crossfade, live emotion bars |
| **RECAP** | 15 s | Timer — before/after thumbnails, emotion graph, verdict seal |

All durations are tunable in `config.py`.

The processor and installation state are **singletons** — a browser reconnect (page refresh) resumes the same session rather than cold-starting.

---

## Vision Pipeline

```
Browser  →  JPEG frame (640×480, 10 Hz) via WebSocket binary
             ↓
GalleryProcessor.push_frame()
             ↓
Analysis thread (10 Hz):
  FaceLandmarker   → blendshapes → 7 emotions (FACS weights)
  PoseLandmarker   → wrists above shoulders = hands_raised
  solvePnP         → head pose — yaw ≤ 35°, pitch ≤ 30° gating
             ↓
CameraState (thread-safe) read by ws_handler on each frame tick
             ↓
advance_state() → InstallationState mutated → JSON ServerState sent to browser
```

MediaPipe models are downloaded once and cached in `/tmp`. The analysis thread starts at server startup so models are warm before visitors arrive.

### Emotion Detection

MediaPipe FaceLandmarker blendshapes (52 FACS action units). No TensorFlow, no DeepFace.

| Emotion | Key blendshapes | Uncanny weight |
|---------|-----------------|---------------|
| Disgust | noseSneer, mouthPucker | **+1.0** |
| Fear | eyeWide + browInnerUp | **+0.9** |
| Surprise | eyeWide, jawOpen, browOuterUp | +0.4 |
| Sad | mouthFrown, browInnerUp | +0.2 |
| Angry | browDown, noseSneer | −0.1 |
| Neutral | Residual (1.5 baseline) | −0.4 |
| Happy | mouthSmile, cheekSquint | **−1.0** |

---

## Verdict Scoring

```
score = Σ(emotion_probability × weight)   normalized to [0, 1]
```

| Score | Verdict | Meaning |
|-------|---------|---------|
| ≥ 0.60 | **VALLIS** | Fell into the uncanny valley |
| 0.40–0.60 | **LIMEN** | At the threshold |
| < 0.40 | **FIRMA** | Stable ground |

---

## WebSocket Protocol

**Client → Server:** binary JPEG frames at ~10 Hz

**Server → Client:** JSON `ServerState` on every change:

```ts
{
  phase: "IDLE" | "INTRO" | "MORPHING" | "RECAP"
  phase_elapsed: number        // seconds since phase start
  phase_duration: number       // total duration of current phase
  phase_started_at: number     // Unix timestamp (seconds)
  attract_mode: boolean        // show attract screen in IDLE
  soul_count: number
  emotions: Record<string, number>   // 0–1 per emotion key
  face_present: boolean
  hands_raised: boolean
  artwork: { slug, title, artist, total_frames } | null
  verdict: "VALLIS" | "LIMEN" | "FIRMA" | ""
  personal_lines: [string, number][]
  collective: { soul_count, dominant_latin, verdict, concordance } | null
  recap_graph: string | null     // base64 PNG
  attract_graph: string | null   // base64 PNG
}
```

---

## Installation & Dependencies

### Ubuntu / Linux (recommended: Ubuntu 22.04+)

Run the installer once after cloning. It installs system packages, creates a
Python venv, installs pip dependencies, installs Node.js, and optionally
installs Brave Browser for kiosk mode.

```bash
cd ars_aut_abeat
chmod +x install.sh start.sh dev.sh stop.sh
./install.sh
```

The installer:
- Installs `libgl1-mesa-glx`, `libglib2.0-0`, and other OpenCV/MediaPipe system deps
- Creates `.venv/` with the correct Python version (prefers 3.12 → 3.11 → 3.10)
- Adds your user to the `video` group for camera access (log out/in once)
- Installs Node.js 20 via NodeSource if not already present
- Installs Brave Browser for kiosk (pass `--no-browser` to skip)

To skip Brave installation (e.g. Chromium already present):
```bash
./install.sh --no-browser
```

### macOS

```bash
# Python 3.10–3.12 required (mediapipe does not support 3.14 yet)
pip install -r requirements.txt

# Node 18+ required
cd frontend && npm install
```

#### macOS SSL fix (run once if MediaPipe model download fails)

```bash
/Applications/Python\ 3.x/Install\ Certificates.command
```

---

## Configuration (`config.py`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `LOCK_STABILITY_DURATION` | 1.5 s | How long hands must stay raised |
| `INTRO_DURATION` | 8.0 s | Artwork reveal screen |
| `MORPHING_DURATION` | 30.0 s | AI degradation animation |
| `RECAP_DURATION` | 15.0 s | Results display |
| `ATTRACT_CYCLE_S` | 30 s | Full attract cycle length |
| `ATTRACT_DURATION_S` | 15 s | Attract screen visible window |
| `EMOTION_SAMPLE_RATE_HZ` | 10 | Analysis thread target rate |
| `GAZE_YAW_THRESHOLD_DEG` | 35.0 | Max head yaw to count as engaged |
| `GAZE_PITCH_THRESHOLD_DEG` | 30.0 | Max head pitch |
| `MIN_FACE_AREA_FRACTION` | 0.01 | Minimum face bbox area |
| `VERDICT_VALLIS_THRESHOLD` | 0.60 | Score ≥ this = VALLIS |
| `VERDICT_FIRMA_THRESHOLD` | 0.40 | Score < this = FIRMA |
| `FRAME_COUNT` | 100 | Degradation frames per artwork |

---

## Catalog

Artwork frames live in `../uncanny_maker/catalog_iterations/{slug}/0000–0100.png`.  
Original JPGs in `../uncanny_maker/catalog/{slug}.jpg`.

The catalog manager scans those directories on startup and auto-registers artworks in the SQLite database. Round-robin picks the least-viewed artwork for each session.

### Resetting data

```bash
rm data/gallery.db   # wipe all viewings; DB is recreated on next start
```

---

## Database

SQLite at `data/gallery.db`. Auto-created on first run.

**artworks** — id, slug, title, artist, year, image_path, description  
**viewings** — id, artwork_id, session_id, timestamp, duration_seconds, emotion_json, dominant_emotion, verdict, num_faces_in_frame

---

## Design Aesthetic

**Fonts:** Cinzel (titles), Cormorant Garamond (body), Pinyon Script (flourishes) — Google Fonts  
**Palette:** Ink black `#1C1410`, parchment `#F4E8D0`, gold `#C9A961`, burgundy `#6B2C2C`  
**Aspect ratio:** `112:199` (portrait column) — centred on landscape display with black bars  
**All text sized for projection** — `clamp()` from ~1rem (phone) to 4rem (beamer)

---

## Tests

```bash
python3 tests/test_verdict.py
python3 tests/test_gaze.py
```
