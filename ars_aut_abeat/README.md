# Vallis Simulacri

**"The Valley of Likeness."** An interactive gallery installation that finds the exact picture at which art stops being art — for each visitor personally. A classical artwork is shown, then ten AI-degraded versions of it. Facial emotion detection measures the visitor's deviation from their own baseline, and the picture that provoked the strongest reaction becomes the verdict: everything before it was art (*ARS*), from there on it no longer is (*ABEAT*).

Designed for projection on a large display. Visitors see themselves full-screen, raise both hands to begin, and receive a personal breaking-point verdict.

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
- **Dev:** open `http://localhost:5173` (Vite proxies `/ws`, `/frames` and `/api` to :8000)

> **First run:** MediaPipe models (~20 MB each) are downloaded automatically on first startup. The face/pose models download in the background on the analysis thread — you will see the app load immediately, but face detection becomes active ~10–30 s later depending on your connection.

---

## The Experience

```
IDLE → BASELINE (19 s) → GALLERY (30 s) → REVEAL (25 s) → IDLE
```

1. **BASELINE** — the visitor sees the untouched original for 19 seconds, with title, artist and a short description to read. Meanwhile the camera silently samples their emotions; the average becomes their personal **baseline** — their face at rest, looking at real art.
2. **GALLERY** — ten AI-degraded pictures, one every 3 seconds with a soft crossfade, like walking past ten works in a gallery. Each picture's emotion samples are collected into a separate bucket (offset by a 0.7 s reaction lag, since the face trails the change).
3. **REVEAL** — the picture whose bucket deviates most from the baseline is the **breaking point**. Three pictures side by side: the original, the picture before the break stamped **ARS** (still art), and the breaking point stamped **ABEAT** (no longer art) — followed by an animated reaction curve over all ten pictures. If no picture moved the visitor beyond the threshold, the original is shown with **ARS MANSIT** — for them, it never stopped being art.

---

## Architecture

```
ars_aut_abeat/
├── backend/
│   ├── main.py         ← FastAPI app: WebSocket endpoint, static files, /api/mode + /api/trigger
│   ├── ws_handler.py   ← GallerySession, singleton processor + state
│   └── graphs.py       ← matplotlib → base64 PNG (attract graph)
├── frontend/           ← React + Vite + TypeScript
│   └── src/
│       ├── hooks/
│       │   ├── useCamera.ts      ← getUserMedia, 10 Hz canvas capture
│       │   └── useWebSocket.ts   ← persistent WS, auto-reconnect, ServerState
│       └── components/
│           ├── CameraBackground.tsx  ← always mounted, drives 10 Hz capture
│           ├── IdlePhase.tsx         ← left: camera mirror; right: status / attract content
│           ├── BaselinePhase.tsx     ← left: original artwork; right: calibration text + progress
│           ├── GalleryPhase.tsx      ← left: crossfading picture sequence; right: live emotion bars
│           ├── RevealPhase.tsx       ← ORIGINAL/ARS/ABEAT triptych + reaction plot
│           └── SlidesPhase.tsx       ← in-app presentation deck (German), toggled via UI button
├── core/
│   ├── state_machine.py  ← InstallationState dataclass, phase FSM
│   ├── session.py        ← ViewerSession (baseline samples + per-picture buckets)
│   └── verdict.py        ← deviation scoring, breaking point, VALLIS / LIMEN / FIRMA
├── vision/
│   ├── camera.py         ← GalleryProcessor: push_frame(), analysis thread
│   ├── emotion.py        ← MediaPipe blendshapes → 7 emotions (FACS)
│   ├── face_detector.py  ← FaceResult dataclass
│   └── gaze.py           ← head pose → "looking at camera" gate
├── catalog/
│   └── manager.py        ← round-robin artwork picker, singleton
├── data/
│   ├── db.py             ← SQLite init (SQLAlchemy) + column migrations
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
IDLE → BASELINE (19 s) → GALLERY (30 s) → REVEAL (25 s) → IDLE
```

| Phase | Duration | Trigger / What happens |
|-------|----------|------------------------|
| **IDLE** | Indefinite | Both hands raised ≥ 1.5 s (or Space in show mode) |
| **BASELINE** | 19 s | Original + title/description shown; emotions sampled into `baseline_samples`; frontend preloads all 11 frames |
| **GALLERY** | 30 s | 10 pictures, soft crossfade every 3 s; emotions bucketed per picture with 0.7 s reaction-lag offset |
| **REVEAL** | 25 s | Breaking point computed once; DB write; triptych + animated reaction plot |

All durations are tunable in `config.py`.

The processor and installation state are **singletons** — a browser reconnect (page refresh) resumes the same session rather than cold-starting.

### Show mode (presentations)

For live demos in front of an audience there is a **show mode**, toggled with the `◎ SELF / ◉ SHOW` button bottom-right (or `POST /api/mode {"mode": "show"}`). In show mode the hands-raised gesture is bypassed; pressing **Space** or **Enter** (or `POST /api/trigger`) starts a run from IDLE. The `◎ SLIDES` button opens an in-app German presentation deck (`SlidesPhase`) explaining the concept.

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
                     (0.4 s grace period before hands count as lowered)
  solvePnP         → head pose — yaw ≤ 35°, pitch ≤ 30° gating
             ↓
CameraState (thread-safe) read by ws_handler on each frame tick
             ↓
advance_state() → InstallationState mutated → JSON ServerState sent to browser
```

MediaPipe models are downloaded once and cached in `/tmp`. The analysis thread starts at server startup so models are warm before visitors arrive.

### Emotion Detection

MediaPipe FaceLandmarker blendshapes (52 FACS action units). No TensorFlow, no DeepFace.

| Emotion | Key blendshapes |
|---------|-----------------|
| Disgust | noseSneer, mouthPucker |
| Fear | eyeWide + browInnerUp |
| Surprise | eyeWide, jawOpen, browOuterUp |
| Sad | mouthFrown, browInnerUp |
| Angry | browDown, noseSneer |
| Neutral | Residual (1.5 baseline) |
| Happy | mouthSmile, cheekSquint |

---

## Breaking-Point Scoring

During BASELINE the average emotion vector is stored as the visitor's **baseline**. During GALLERY each picture gets its own bucket of samples. At reveal time:

```
deviation(picture k) = Σ over emotions  BREAKING_WEIGHTS[e] × |bucket_avg_k[e] − baseline[e]|

breaking point = argmax k  deviation(k)        (None if max < BREAKING_MIN_DEVIATION)
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

Any *change* from baseline counts — the weights only decide how much.

### Verdict

| Condition | Verdict | Meaning |
|-----------|---------|---------|
| max deviation ≥ 0.25 | **VALLIS** | Strong reaction — fell into the valley |
| breaking point exists, deviation < 0.25 | **LIMEN** | Measurable but mild — at the threshold |
| max deviation < 0.08 (no breaking point) | **FIRMA** | Unmoved — *ARS MANSIT*, it never stopped being art |

Thresholds are in `config.py` (`BREAKING_MIN_DEVIATION`, `VERDICT_VALLIS_DEVIATION`) and will need live tuning with real faces.

---

## WebSocket Protocol

**Client → Server:** binary JPEG frames at ~10 Hz

**Server → Client:** JSON `ServerState` on every change:

```ts
{
  show_mode: boolean
  phase: "IDLE" | "BASELINE" | "GALLERY" | "REVEAL"
  phase_elapsed: number        // seconds since phase start
  phase_duration: number       // total duration of current phase
  phase_started_at: number     // Unix timestamp (seconds) — frontend animation clock
  attract_mode: boolean        // show attract screen in IDLE
  soul_count: number
  emotions: Record<string, number>   // 0–1 per emotion key
  face_present: boolean
  hands_raised: boolean
  artwork: { slug, title, artist, total_frames } | null
  verdict: "VALLIS" | "LIMEN" | "FIRMA" | ""
  personal_lines: [string, number][]
  breaking_index: number | null  // 1-based picture where art broke; null = never
  deviations: number[]           // per-picture deviation from baseline
  collective: { soul_count, dominant_latin, verdict, concordance } | null
  attract_graph: string | null   // base64 PNG
}
```

### HTTP endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/mode` | POST `{"mode": "show" \| "self"}` | Toggle show mode |
| `/api/trigger` | POST | Start a run from IDLE (show mode only) |
| `/frames/{slug}/{n:04d}.png` | GET | Artwork pictures (static) |

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
| `BASELINE_DURATION` | 19.0 s | Original + description; baseline calibration |
| `GALLERY_DURATION` | 30.0 s | 10-picture sequence |
| `REVEAL_DURATION` | 25.0 s | Triptych verdict + reaction plot |
| `FRAME_COUNT` | 10 | Pictures per artwork (0000 = original, 0001–0010) |
| `SECONDS_PER_PICTURE` | 3.0 s | Derived: `GALLERY_DURATION / FRAME_COUNT` |
| `REACTION_LAG_S` | 0.7 s | Facial reaction delay used for bucket attribution |
| `BREAKING_WEIGHTS` | see above | Per-emotion deviation weights |
| `BREAKING_MIN_DEVIATION` | 0.08 | Below this max deviation → FIRMA |
| `VERDICT_VALLIS_DEVIATION` | 0.25 | Above this max deviation → VALLIS |
| `ATTRACT_CYCLE_S` | 30 s | Full attract cycle length |
| `ATTRACT_DURATION_S` | 15 s | Attract screen visible window |
| `EMOTION_SAMPLE_RATE_HZ` | 10 | Analysis thread target rate |
| `GAZE_YAW_THRESHOLD_DEG` | 35.0 | Max head yaw to count as engaged |
| `GAZE_PITCH_THRESHOLD_DEG` | 30.0 | Max head pitch |
| `MIN_FACE_AREA_FRACTION` | 0.01 | Minimum face bbox area |

---

## Catalog

Artwork pictures live in `../uncanny_maker/catalog_iterations_10/{slug}/0000–0010.png`.  
Original JPGs in `../uncanny_maker/catalog/{slug}.jpg`.

The catalog manager scans those directories on startup and auto-registers artworks in the SQLite database. Round-robin picks the least-viewed artwork for each session. An artwork is only loaded when its `0010.png` exists — partially generated sequences are skipped.

Generate the sequences with `uncanny_maker/iterate_degrade.py` (two phases: pictures 1–5 direct from the original, 6–10 chained model collapse; see `../docs/PIPELINE.md`).

### Resetting data

```bash
rm data/gallery.db   # wipe all viewings; DB is recreated on next start
```

---

## Database

SQLite at `data/gallery.db`. Auto-created on first run; missing columns are added automatically (`data/db.py:_migrate`).

**artworks** — id, slug, title, artist, year, image_path, description  
**viewings** — id, artwork_id, session_id, timestamp, duration_seconds, emotion_json, dominant_emotion, verdict, num_faces_in_frame, **breaking_index** (1-based picture where art broke; NULL = never)

---

## Design Aesthetic

**Fonts:** Cinzel (titles), Cormorant Garamond (body), Pinyon Script (flourishes) — Google Fonts  
**Palette:** Ink black `#1C1410`, parchment `#F4E8D0`, gold `#C9A961`, burgundy `#6B2C2C`  
**Layout:** `16:9` landscape — camera feed left (58%), info panel right (42%). Letterboxed on non-16:9 screens. The reveal screen is a full-bleed split.  
**All text sized for projection** — `clamp()` with `vh`-based fluid values; panel never overflows regardless of screen size.

---

## Tests

```bash
python3 tests/test_verdict.py
python3 tests/test_gaze.py
```
