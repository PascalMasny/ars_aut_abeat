from pathlib import Path

BASE_DIR = Path(__file__).parent

# Timing (seconds)
LOCK_STABILITY_DURATION    = 1.5
LOCKED_TRANSITION_DURATION = 2.5
BASELINE_DURATION          = 19.0  # viewer reads title/description of the original; emotions sampled = baseline
GALLERY_DURATION           = 30.0  # 10 degradation pictures, 3s each, soft crossfade
REVEAL_DURATION            = 25.0  # 3-picture verdict + reaction plot
FADE_DURATION              = 3.0
# Legacy aliases — only the retired Streamlit app.py still imports these
INTRO_DURATION    = BASELINE_DURATION
MORPHING_DURATION = GALLERY_DURATION
RECAP_DURATION    = REVEAL_DURATION

# Source artwork + iteration directories (one level up, in the uncanny_maker
# pipeline output).
_UNCANNY_ROOT       = BASE_DIR.parent / "uncanny_maker"
UNCANNY_OG_DIR      = _UNCANNY_ROOT / "catalog"
ITERATIONS_DIRNAME  = "catalog_iterations_10"
UNCANNY_ITER_DIR    = _UNCANNY_ROOT / ITERATIONS_DIRNAME
# Legacy 4-stage fallback dirs (catalog/manager.py uses them if a full
# iteration set is missing for an artwork):
UNCANNY_20_DIR = _UNCANNY_ROOT / "catalog_uncanny" / "20"
UNCANNY_60_DIR = _UNCANNY_ROOT / "catalog_uncanny" / "60"
UNCANNY_80_DIR = _UNCANNY_ROOT / "catalog_uncanny" / "80"

# Animation
FRAME_COUNT         = 10    # 0000 = original + 0001…0010 = degradation pictures
SECONDS_PER_PICTURE = GALLERY_DURATION / FRAME_COUNT
REACTION_LAG_S      = 0.7   # facial reaction trails the picture cut by roughly this much

# Vision
EMOTION_SAMPLE_RATE_HZ    = 10
GAZE_YAW_THRESHOLD_DEG    = 35.0
GAZE_PITCH_THRESHOLD_DEG  = 30.0
MIN_FACE_AREA_FRACTION    = 0.01

# Verdict scoring — measures how deeply the viewer fell into the uncanny valley.
VERDICT_WEIGHTS = {
    "disgust":  1.0,
    "fear":     0.9,
    "surprise": 0.4,
    "sad":      0.2,
    "angry":   -0.1,
    "neutral": -0.4,
    "happy":   -1.0,
}
VERDICT_VALLIS_THRESHOLD = 0.60
VERDICT_FIRMA_THRESHOLD  = 0.40

# Breaking-point scoring — per-picture deviation from the viewer's baseline.
# Any emotional shift counts as a reaction; uncanny emotions count more.
BREAKING_WEIGHTS = {
    "disgust":  1.0,
    "fear":     0.9,
    "surprise": 0.7,
    "angry":    0.6,
    "sad":      0.5,
    "happy":    0.5,
    "neutral":  0.2,
}
BREAKING_MIN_DEVIATION   = 0.08  # max deviation below this → no breaking point → FIRMA
VERDICT_VALLIS_DEVIATION = 0.25  # max deviation above this → VALLIS, between → LIMEN

# Attract screen (shown during IDLE when no one is interacting)
ATTRACT_CYCLE_S    = 30   # total cycle length in seconds
ATTRACT_DURATION_S = 15   # how long the attract screen stays visible per cycle

# Paths
DB_PATH      = BASE_DIR / "data" / "gallery.db"
CATALOG_PATH = BASE_DIR / "catalog" / "artworks.json"  # initial seed data

# Latin emotion names
EMOTION_LATIN = {
    "happy":    "Happy",
    "sad":      "Sad",
    "angry":    "Angry",
    "surprise": "Surprise",
    "fear":     "Fear",
    "disgust":  "Disgust",
    "neutral":  "Neutral",
}
