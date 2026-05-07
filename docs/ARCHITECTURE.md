# System Architecture — Vallis Simulacri

## Overview

The installation is split into two independent systems that share only the filesystem: an **offline preprocessing pipeline** (`uncanny_maker`) that produces the artwork catalog, and a **real-time gallery application** (`ars_aut_abeat`) that runs during the installation itself.

```
┌─────────────────────────────────────────────────────────────────┐
│  PREPROCESSING  (run once, offline)                             │
│                                                                 │
│  Met Museum API ──► download_human_figures.py                   │
│                           │                                     │
│                           ▼                                     │
│                    catalog/  (source JPEGs)                     │
│                           │                                     │
│                           ▼                                     │
│  LLaVA + Stable Diffusion ──► iterate_degrade.py               │
│                           │                                     │
│                           ▼                                     │
│             catalog_iterations/<slug>/0000–0100.png             │
└─────────────────────────────────────────────────────────────────┘
                             │  filesystem
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  GALLERY APPLICATION  (runs live)                               │
│                                                                 │
│  Browser / Kiosk                                                │
│      │  WebRTC stream                                           │
│      ▼                                                          │
│  GalleryVideoProcessor (daemon thread @ 10 Hz)                  │
│      │  MediaPipe: FaceLandmarker + PoseLandmarker              │
│      │  → blendshapes → emotion dict                            │
│      │  → head pose (solvePnP) → gaze bool                     │
│      │  → pose landmarks → hands_raised bool                    │
│      ▼                                                          │
│  CameraState (thread-safe snapshot)                             │
│      │                                                          │
│      ▼                                                          │
│  State Machine (advance_state called every Streamlit rerun)     │
│      │  IDLE → LOCKED → MORPHING → RECAP → FADE → IDLE         │
│      │                                                          │
│      ▼                                                          │
│  ViewerSession  (emotion samples accumulated during MORPHING)   │
│      │                                                          │
│      ▼                                                          │
│  Verdict Engine  (score_emotions + verdict_label)               │
│      │                                                          │
│      ▼                                                          │
│  SQLite  (gallery.db — Artwork, Viewing tables)                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## State Machine

Implemented in `core/state_machine.py`. Streamlit reruns the entire script on every autorefresh tick; `advance_state()` reads wall-clock time and the latest `CameraState` snapshot to decide whether to transition.

```
IDLE  ──[hands_raised ≥ 1.5 s]──►  LOCKED  ──[2.5 s elapsed]──►  MORPHING
                                                                        │
                        ◄──────[FADE: 3 s]──  RECAP  ◄──[30 s elapsed]─┘
```

### Phase responsibilities

| Phase | Duration | What happens |
|-------|----------|-------------|
| `IDLE` | indefinite | Camera mirror, wait for raise trigger |
| `LOCKED` | 2.5 s | Artwork title reveal, emotion sampling disabled |
| `MORPHING` | 30 s | Frame sequence plays, emotions sampled at 10 Hz |
| `RECAP` | 15 s | Verdict rendered, emotion timeline drawn, DB write |
| `FADE` | 3 s | Exit animation, reset session |

The DB write happens exactly once, at the start of `RECAP`, via `_finalize_viewing()`.

---

## Threading Model

WebRTC frame delivery and MediaPipe inference run on separate threads to keep the UI responsive.

```
WebRTC thread (aiortc)
    recv(frame) ──► stash RGB bytes into self._latest_frame (lock-protected)
                    return immediately (<1 ms)

Analysis thread (daemon, started in __init__)
    loop at ~10 Hz:
        acquire lock, copy latest frame
        run FaceLandmarker.detect_for_video()
        run PoseLandmarker.detect_for_video()
        compute blendshape→emotion mapping
        compute head pose via solvePnP
        compute hands_raised from wrist/shoulder landmarks
        write result into self._state (lock-protected)

Streamlit main thread
    camera_state = processor.get_state()  ← lock-protected read
    advance_state(camera_state, ...)
```

This design ensures that MediaPipe never blocks the WebRTC pipeline and that the Streamlit thread always has a fresh, non-blocking snapshot.

---

## Emotion Detection

### Blendshape → Emotion Mapping (FACS)

MediaPipe FaceLandmarker returns 52 action-unit scores in [0, 1]. These are grouped into 7 emotion channels:

| Emotion | Action Units | Direction |
|---------|-------------|-----------|
| Happy | mouthSmileLeft/Right, cheekSquintLeft/Right | −1.0 (away from valley) |
| Disgust | noseSneerLeft/Right, mouthPuckerLeft/Right | +1.0 (core uncanny signal) |
| Fear | eyeWideLeft/Right + browInnerUp | +0.9 |
| Surprise | eyeWideLeft/Right, browOuterUpLeft/Right, jawOpen | +0.4 |
| Sad | mouthFrownLeft/Right, browInnerUp | +0.2 |
| Angry | browDownLeft/Right | −0.1 |
| Neutral | residual (1.5 baseline) | −0.4 |

### Verdict Scoring

The final score for a session is the weighted sum over the **mean** of all emotion samples collected during MORPHING:

```
raw_score   = Σ (weight_i × mean_emotion_i)
norm_score  = (raw_score + 1.0) / 2.0          # maps [-1, 1] → [0, 1]
```

Thresholds (configurable in `config.py`):

```
norm_score ≥ 0.60  →  VALLIS  (fell into the valley)
norm_score < 0.40  →  FIRMA   (stable ground)
otherwise          →  LIMEN   (at the threshold)
```

### Gaze Detection

Head pose is estimated via `cv2.solvePnP` using a canonical 3D face model (6 landmark anchor points) and the camera's estimated intrinsic matrix. A viewer is considered to be "looking at the camera" when:

```
|yaw|   ≤ 35°   (horizontal tolerance)
|pitch| ≤ 30°   (vertical tolerance)
```

Faces outside this cone are recorded but flagged in the DB as `face_centered = False`.

---

## Catalog Management

`CatalogManager` (`catalog/manager.py`) abstracts over two catalog formats:

1. **Current**: `uncanny_maker/catalog_iterations/<slug>/0000.png` … `0100.png` (101 frames)
2. **Legacy**: `catalog/_archive/artworks/<slug>_20.jpg`, `_60.jpg`, `_80.jpg` (4-stage, deprecated)

During MORPHING the frame index is computed from elapsed time:

```python
frame_idx = int((elapsed / MORPHING_DURATION) * total_frames)
```

`pick_next()` selects the artwork with the fewest viewings in the DB, ensuring balanced data collection across the catalog.

---

## Database Schema

SQLite file at `ars_aut_abeat/data/gallery.db` (created automatically on first run, excluded from version control).

### `artworks`

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | Auto-increment |
| `slug` | TEXT UNIQUE | Filename stem, e.g. `The_Dance_Class_438817` |
| `title` | TEXT | Display name |
| `artist` | TEXT | |
| `year` | INTEGER | |
| `image_path` | TEXT | Absolute path to source image |
| `description` | TEXT | Optional curator note |
| `added_at` | DATETIME | |

### `viewings`

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | |
| `artwork_id` | INTEGER FK | → `artworks.id` |
| `session_id` | TEXT | UUID per visit |
| `timestamp` | DATETIME | Session start |
| `duration_seconds` | FLOAT | Actual MORPHING duration |
| `emotion_json` | TEXT | JSON of mean emotion dict |
| `dominant_emotion` | TEXT | Highest-probability emotion |
| `verdict` | TEXT | VALLIS / LIMEN / FIRMA |
| `num_faces_in_frame` | INTEGER | Detected faces during MORPHING |

---

## Concordance Metric

At the end of each session the viewer's emotion profile is compared to the crowd average for that artwork:

```
concordance = 1.0 − (Σ |viewer_i − crowd_i|) / max_possible_deviation
```

`max_possible_deviation` is the theoretical maximum if the viewer is at the opposite extreme of every emotion from the crowd. The result ranges from 0.0 (complete disagreement) to 1.0 (perfect match) and is displayed on the RECAP screen.

---

## Known Issues and Workarounds

### SessionShutdownObserver race condition

Streamlit reruns the script on every autorefresh tick. Without intervention, MediaPipe's `SessionShutdownObserver` is re-instantiated on each rerun, causing a brief initialization spike and visible frame drops. This is patched in `app.py` by monkey-patching the observer class to a no-op before the first `import mediapipe`. The patch is idempotent.

### libavdevice warning on macOS

`streamlit-webrtc` may print `[Errno 2] No such file or directory: 'libavdevice'` on macOS. This is cosmetic — the WebRTC pipeline uses `libavcodec` directly and does not require `libavdevice`. No action needed.

### Autorefresh cadence

`streamlit-autorefresh` is configured per-phase:

| Phase | Refresh rate | Reason |
|-------|-------------|--------|
| IDLE | 500 ms | Responsive to hand trigger |
| MORPHING | 200 ms | Smooth frame animation |
| RECAP / FADE | 1 000 ms | No frame updates needed |
