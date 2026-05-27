# System Architecture — Vallis Simulacri

## Overview

The project is split into two independent systems that share only the filesystem:

- **`uncanny_maker`** — offline preprocessing pipeline (run once). Produces the artwork catalog.
- **`ars_aut_abeat`** — real-time gallery application (runs live during the installation).

```
┌──────────────────────────────────────────────────────────────────┐
│  OFFLINE PREPROCESSING  (run once before installation)           │
│                                                                  │
│  Met Museum API                                                  │
│      └──► download_human_figures.py                              │
│               └──► catalog/*.jpg  (source paintings)            │
│                        └──► iterate_degrade.py                  │
│                                 │  LLaVA → description prompt   │
│                                 │  Stable Diffusion × 100       │
│                                 └──► catalog_iterations/        │
│                                      {slug}/0000–0100.png        │
└──────────────────────────────────────────────────────────────────┘
                              │  shared filesystem
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  GALLERY APPLICATION  (live)                                     │
│                                                                  │
│  Kiosk Browser (Brave/Chrome)                                    │
│      │  JPEG frames via WebSocket binary  (10 Hz)               │
│      │  JSON ServerState via WebSocket text  (on change)        │
│      │                                                           │
│  FastAPI + Uvicorn (backend/)                                    │
│      │                                                           │
│      ├── GalleryProcessor (vision/)                              │
│      │     analysis thread @ 10 Hz:                             │
│      │     MediaPipe FaceLandmarker → blendshapes → 7 emotions   │
│      │     MediaPipe PoseLandmarker → hands_raised bool         │
│      │     OpenCV solvePnP          → gaze bool                 │
│      │     ↓ writes CameraState (thread-safe)                   │
│      │                                                           │
│      ├── InstallationState + advance_state() (core/)             │
│      │     FSM: IDLE → INTRO → MORPHING → RECAP → IDLE          │
│      │     called on every WebSocket tick                        │
│      │                                                           │
│      ├── ViewerSession (core/session.py)                         │
│      │     accumulates emotion samples during MORPHING           │
│      │                                                           │
│      ├── Verdict engine (core/verdict.py)                        │
│      │     weighted emotion sum → VALLIS / LIMEN / FIRMA         │
│      │                                                           │
│      └── SQLite gallery.db (data/)                               │
│            artworks + viewings tables                            │
└──────────────────────────────────────────────────────────────────┘
```

---

## File-by-File Reference

### `backend/`

| File | Role |
|------|------|
| `main.py` | FastAPI app entry point. Mounts `/frames` and `/catalog` as static dirs, registers `/ws` WebSocket endpoint, serves built React SPA from `frontend/dist/`. Pre-warms MediaPipe models and catalog on startup. |
| `ws_handler.py` | `GallerySession` handles one WebSocket connection. Singleton `GalleryProcessor` and `InstallationState` are shared across all connections (reconnects resume mid-session). Calls `advance_state()` on each frame tick and pushes a JSON `ServerState` diff to the client. |
| `graphs.py` | Matplotlib chart generators. `recap_graph()` produces an emotion-over-time line chart; `attract_graph()` produces a verdict-distribution donut + average-emotion bar chart. Both return base64-encoded PNG strings. |

### `core/`

| File | Role |
|------|------|
| `state_machine.py` | `InstallationState` dataclass + `advance_state()` function. Called on every frame tick. Reads `CameraState` and wall-clock time; transitions phases; triggers `_finalize_viewing()` at MORPHING end. |
| `session.py` | `ViewerSession` per visitor. Stores a UUID, artwork ID, list of emotion dicts sampled during MORPHING, and matching timestamps. |
| `verdict.py` | `score_emotions()`, `verdict_label()`, `personal_verdict_text()`, `save_viewing()`, `collective_summary()`. Computes and persists all per-session and collective results. |

### `vision/`

| File | Role |
|------|------|
| `camera.py` | `GalleryProcessor`. Receives JPEG bytes via `push_frame()`. Background analysis thread runs at 10 Hz: decodes JPEG, runs FaceLandmarker and PoseLandmarker, computes head pose, writes `CameraState`. Thread-safe: one lock on the frame buffer, one on the state snapshot. |
| `emotion.py` | `_blendshapes_to_emotions()` maps MediaPipe's 52 FACS blendshape scores to 7 emotion channels using weighted sums. `neutral` is computed as a residual with a 1.5 baseline so quiet faces don't show as zero. `average_samples()` averages a list of per-frame dicts. |
| `face_detector.py` | `FaceResult` dataclass — thin wrapper kept for import compatibility. Actual detection runs in `camera.py`. |
| `gaze.py` | `is_looking_at_camera()` — returns True when `|yaw| ≤ 35°` and `|pitch| ≤ 30°`. `most_centered_face()` selects the face closest to the frame centre. |

### `catalog/`

| File | Role |
|------|------|
| `manager.py` | `CatalogManager` scans `uncanny_maker/catalog_iterations/` on startup. For each artwork slug it checks whether `{slug}/0100.png` exists (100-frame mode) or falls back to the legacy 4-stage format. Auto-registers artworks in SQLite. `pick_next()` selects the least-viewed artwork for balanced data collection. |

### `data/`

| File | Role |
|------|------|
| `db.py` | SQLite init via SQLAlchemy. `init_db()` creates the schema and seeds from `catalog/artworks.json` if present. `get_session()` returns a new SQLAlchemy session. |
| `models.py` | `Artwork` and `Viewing` ORM models. |
| `stats.py` | `artwork_summary()` — aggregate emotion averages and verdict counts for one artwork. `concordance()` — how closely a viewer's emotion profile matches the crowd average for the same artwork. `_score()` — the core weighted-sum scoring function used by both stats and verdict. |

### `frontend/src/`

| File | Role |
|------|------|
| `hooks/useWebSocket.ts` | Manages the WebSocket connection. Sends binary JPEG blobs to server; parses incoming JSON into `ServerState`. Auto-reconnects on disconnect (2 s). `ServerState` is the single source of truth for all UI. |
| `hooks/useCamera.ts` | Wraps `getUserMedia`. Captures at 640×480, 15 fps. Every 100 ms (10 Hz) draws a frame to an off-screen canvas, encodes as JPEG at 70 % quality, passes to caller as a `Blob`. |
| `components/CameraBackground.tsx` | Always mounted — passes frames to `sendFrame` continuously. Never unmounts between phases, so the camera stream never stops. |
| `components/IdlePhase.tsx` | Mirror overlay. Shows visitor detection status and hands-raised prompt. Switches to attract mode (concept text + aggregate graphs) on a 30-second cycle. |
| `components/IntroPhase.tsx` | Shows the original painting + artwork title + explanatory text. Preloads all 101 frames into browser cache during its 8-second window so MorphingPhase starts without stalls. |
| `components/MorphingPhase.tsx` | rAF crossfade loop over 101 frames. Driven by wall-clock time anchored to `phase_started_at` (server timestamp) so it stays in sync even across page refreshes. Piecewise easing: frames 0–5 run slowly (first 50 % of duration) to show the initial distortion clearly; frames 5–100 race through the second 50 %. Live emotion bars update from `state.emotions`. |
| `components/RecapPhase.tsx` | Before/after thumbnail pair, emotion-over-time graph (base64 PNG from server), verdict seal medallion. |

---

## State Machine

Implemented in `core/state_machine.py`. `advance_state()` is called on every WebSocket tick (~10 Hz). All durations are configurable in `config.py`.

```
IDLE ──[hands raised ≥ 1.5 s]──► INTRO ──[8 s]──► MORPHING ──[30 s]──► RECAP ──[15 s]──► IDLE
```

| Phase | Duration | What happens |
|-------|----------|-------------|
| `IDLE` | Indefinite | Camera mirror; attract screen cycles every 30 s; waiting for hands-raised trigger |
| `INTRO` | 8 s | Full-screen original artwork; frontend preloads all frames |
| `MORPHING` | 30 s | 100-frame crossfade animation; emotion sampling active; ViewerSession accumulates samples |
| `RECAP` | 15 s | `_finalize_viewing()` called once: averages emotions, scores, writes DB, builds recap chart |

The DB write happens exactly once, at the start of `RECAP`, inside `_finalize_viewing()`.

---

## Threading Model

```
WebSocket handler (asyncio event loop)
    ├── receive(): waits up to 2 s for JPEG bytes
    │       → on bytes: calls push_frame() — non-blocking (<1 ms, just stashes the frame)
    │       → on timeout: calls _tick(None) — advances state without a new frame
    └── _tick(): reads CameraState, calls advance_state(), sends JSON if state changed

GalleryProcessor analysis thread (daemon, started at server startup)
    loop @ ~10 Hz:
        copy latest_rgb  (frame lock)
        FaceLandmarker.detect()    → blendshapes → emotions
        PoseLandmarker.detect()    → wrist/shoulder → hands_raised
        solvePnP()                 → yaw/pitch → gaze
        write CameraState          (state lock)
```

Key property: `push_frame()` never blocks the analysis thread. The analysis thread always operates on the most recently stashed frame.

---

## WebSocket Protocol

**Client → Server:** binary (raw JPEG bytes, 640×480, ~10 Hz)

**Server → Client:** text JSON `ServerState`, sent only when the state changes (diff-suppressed)

```typescript
interface ServerState {
  phase:           'IDLE' | 'INTRO' | 'MORPHING' | 'RECAP'
  phase_elapsed:   number        // seconds since phase start
  phase_duration:  number        // total duration of current phase
  phase_started_at: number       // Unix timestamp (seconds) — used by frontend animation clock
  attract_mode:    boolean       // show attract overlay in IDLE
  soul_count:      number        // total viewings so far
  emotions:        Record<string, number>   // 0–1 per key; only populated during INTRO+MORPHING
  face_present:    boolean
  hands_raised:    boolean
  artwork:         { slug, title, artist, total_frames } | null
  verdict:         'VALLIS' | 'LIMEN' | 'FIRMA' | ''
  personal_lines:  [latin_name: string, pct: number][]
  collective:      { soul_count, dominant_latin, verdict, concordance } | null
  recap_graph:     string | null    // base64 PNG (emotion timeline)
  attract_graph:   string | null    // base64 PNG (aggregate donut + bars)
}
```

Frames are served as static files: `/frames/{slug}/{n:04d}.png`. The frontend fetches them directly via HTTP — they do not travel through the WebSocket.

---

## Emotion Detection

### Blendshape → Emotion Mapping (FACS)

MediaPipe FaceLandmarker returns 52 action-unit scores in `[0, 1]`. These are combined into 7 channels using pre-defined weights from Facial Action Coding System (FACS) research:

| Emotion | Key blendshapes | Verdict weight |
|---------|-----------------|---------------|
| Happy | mouthSmileLeft/Right, cheekSquintLeft/Right | **−1.0** (counter-signal) |
| Disgust | noseSneerLeft/Right, mouthPucker | **+1.0** (core uncanny signal) |
| Fear | eyeWideLeft/Right + browInnerUp | **+0.9** |
| Surprise | eyeWideLeft/Right, browOuterUpLeft/Right, jawOpen | +0.4 |
| Sad | mouthFrownLeft/Right, browInnerUp | +0.2 |
| Angry | browDownLeft/Right, noseSneer | −0.1 |
| Neutral | residual (1.5 baseline − sum of others) | −0.4 |

Normalization: all channels are summed; each channel is divided by the total so they form a probability distribution summing to 1.

### Gaze Gate

Head pose is estimated via `cv2.solvePnP` using 6 canonical 3D face landmarks and an estimated camera intrinsic matrix (focal length = frame width).

A face is considered "looking at the camera" when:
```
|yaw|   ≤ 35°
|pitch| ≤ 30°
```

Hands-raised trigger and emotion sampling are not gated on gaze — only the `face_centered` field in `CameraState` reflects this.

### Hands-Raised Detection

PoseLandmarker landmarks 15 (left wrist) and 16 (right wrist) are compared to landmarks 11 (left shoulder) and 12 (right shoulder). Both wrists must have a smaller `y` value than their respective shoulder (higher on screen = lower y in normalized coordinates).

The state machine requires this condition to hold continuously for `LOCK_STABILITY_DURATION` (default 1.5 s) before transitioning from IDLE to INTRO.

---

## Verdict Scoring

```python
raw_score  = sum(emotion_probability[k] * VERDICT_WEIGHTS[k] for k in emotions)
norm_score = (raw_score + 1.0) / 2.0    # maps theoretical [-1, 1] → [0, 1]
norm_score = clamp(norm_score, 0.0, 1.0)
```

Thresholds (configurable in `config.py`):

| Condition | Verdict |
|-----------|---------|
| `norm_score ≥ 0.60` | VALLIS — fell into the valley |
| `norm_score ≥ 0.40` | LIMEN — at the threshold |
| `norm_score < 0.40` | FIRMA — stable ground |

The score is computed over the **mean** of all emotion samples collected during the 30-second MORPHING phase.

---

## Concordance Metric

At recap time, the visitor's mean emotion profile is compared to the collective average for the same artwork:

```python
concordance = 1.0 - (sum(|viewer[k] - crowd[k]| for k in keys) / (len(keys) * 1.0))
```

Returns `[0.0, 1.0]`: 1.0 = viewer matched the crowd exactly; 0.0 = opposite extreme on every emotion.

---

## Database Schema

SQLite at `data/gallery.db`. Created automatically on first run.

### `artworks`

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | Auto-increment |
| `slug` | TEXT UNIQUE | Filename stem, e.g. `The_Dance_Class_438817` |
| `title` | TEXT | Display name derived from stem |
| `artist` | TEXT | Always "Metropolitan Museum of Art" for current catalog |
| `year` | TEXT | |
| `image_path` | TEXT | Absolute path to source JPEG |
| `description` | TEXT | Optional curator note |
| `added_at` | DATETIME | UTC |

### `viewings`

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | |
| `artwork_id` | INTEGER FK | → `artworks.id` |
| `session_id` | TEXT | UUID per visit |
| `timestamp` | DATETIME | UTC, session start |
| `duration_seconds` | FLOAT | Actual MORPHING duration |
| `emotion_json` | TEXT | JSON of mean emotion probabilities |
| `dominant_emotion` | TEXT | Highest-probability emotion key |
| `verdict` | TEXT | `VALLIS` / `LIMEN` / `FIRMA` |
| `num_faces_in_frame` | INTEGER | Faces detected during MORPHING |

---

## Catalog Management

`CatalogManager` (`catalog/manager.py`) abstracts over two catalog formats:

1. **100-frame (current):** `uncanny_maker/catalog_iterations/{slug}/0000.png … 0100.png`
2. **4-stage (legacy fallback):** `catalog_uncanny/20/{slug}.png`, `60/`, `80/`

The 100-frame format is used when `{slug}/0100.png` exists. Otherwise the legacy format is used if all three intermediate files are present. Artworks with neither are skipped.

`pick_next()` selects the artwork with the fewest viewings in the DB, ensuring data is collected evenly across the full catalog.

---

## Singleton Architecture

`GalleryProcessor`, `InstallationState`, and `CatalogManager` are module-level singletons, initialised on first access and shared across all WebSocket connections. This means:

- A page refresh does **not** reset the installation state — the session continues.
- MediaPipe models are loaded once at server startup, before any visitor connects.
- The analysis thread runs continuously regardless of whether a client is connected.

---

## Configuration Reference (`config.py`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `LOCK_STABILITY_DURATION` | 1.5 s | Hands must stay raised for this long to trigger |
| `INTRO_DURATION` | 8.0 s | Artwork reveal screen |
| `MORPHING_DURATION` | 30.0 s | AI degradation animation |
| `RECAP_DURATION` | 15.0 s | Results display |
| `ATTRACT_CYCLE_S` | 30 s | Full attract cycle length |
| `ATTRACT_DURATION_S` | 15 s | Attract screen visible per cycle |
| `EMOTION_SAMPLE_RATE_HZ` | 10 | Analysis thread target rate |
| `GAZE_YAW_THRESHOLD_DEG` | 35.0° | Max head yaw to count as looking at camera |
| `GAZE_PITCH_THRESHOLD_DEG` | 30.0° | Max head pitch |
| `MIN_FACE_AREA_FRACTION` | 0.01 | Minimum face bounding-box area (fraction of frame) |
| `VERDICT_VALLIS_THRESHOLD` | 0.60 | Score ≥ this → VALLIS |
| `VERDICT_FIRMA_THRESHOLD` | 0.40 | Score < this → FIRMA |
| `FRAME_COUNT` | 100 | Degradation frames per artwork |
| `VERDICT_WEIGHTS` | see above | Per-emotion weights for the valley score |
