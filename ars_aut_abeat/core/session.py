import uuid
import time
from dataclasses import dataclass, field

from config import FRAME_COUNT, SECONDS_PER_PICTURE, REACTION_LAG_S


@dataclass
class ViewerSession:
    session_id:         str              = field(default_factory=lambda: str(uuid.uuid4()))
    artwork_id:         int | None       = None
    artwork_slug:       str              = ""
    emotion_samples:    list[dict[str, float]] = field(default_factory=list)
    emotion_timestamps: list[float]      = field(default_factory=list)  # seconds from GALLERY start
    baseline_samples:   list[dict[str, float]] = field(default_factory=list)
    gallery_buckets:    list[list[dict[str, float]]] = field(
        default_factory=lambda: [[] for _ in range(FRAME_COUNT)]
    )
    started_at:         float            = field(default_factory=time.time)

    def add_baseline_sample(self, emotions: dict[str, float]):
        if emotions:
            self.baseline_samples.append(emotions)

    def add_gallery_sample(self, emotions: dict[str, float], elapsed: float):
        if not emotions:
            return
        self.emotion_samples.append(emotions)
        self.emotion_timestamps.append(elapsed)
        # Attribute the sample to the picture the viewer is reacting to:
        # the face trails the cut by REACTION_LAG_S; earlier samples still
        # belong to the baseline original and are not bucketed.
        shifted = elapsed - REACTION_LAG_S
        if shifted < 0:
            return
        idx = min(int(shifted / SECONDS_PER_PICTURE), FRAME_COUNT - 1)
        self.gallery_buckets[idx].append(emotions)

    def duration(self) -> float:
        return time.time() - self.started_at
