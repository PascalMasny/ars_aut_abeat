import time
from dataclasses import dataclass, field
from typing import Optional
from config import (
    LOCK_STABILITY_DURATION,
    BASELINE_DURATION,
    GALLERY_DURATION,
    REVEAL_DURATION,
)

PHASES = ["IDLE", "BASELINE", "GALLERY", "REVEAL"]

PHASE_DURATIONS = {
    "BASELINE": BASELINE_DURATION,
    "GALLERY":  GALLERY_DURATION,
    "REVEAL":   REVEAL_DURATION,
}


@dataclass
class InstallationState:
    phase: str = "IDLE"
    phase_entered_at: float = field(default_factory=time.time)
    viewer_session: Optional[object] = None
    avg_emotions: dict = field(default_factory=dict)
    baseline_emotions: dict = field(default_factory=dict)
    deviations: list = field(default_factory=list)
    breaking_index: Optional[int] = None
    personal_verdict: str = ""
    personal_lines: list = field(default_factory=list)
    current_artwork: Optional[dict] = None
    collective_data: Optional[dict] = None
    attract_graph_b64: Optional[str] = None
    attract_viewing_count: int = -1
    show_mode: bool = False
    show_trigger: bool = False


def elapsed(state: InstallationState) -> float:
    return time.time() - state.phase_entered_at


def enter_phase(state: InstallationState, phase: str):
    state.phase = phase
    state.phase_entered_at = time.time()


def advance_state(state: InstallationState, camera_state, catalog_manager, db_session):
    """Called on every frame tick. Reads camera state + timing, transitions phases."""
    phase = state.phase
    t = elapsed(state)

    if phase == "IDLE":
        _handle_idle(state, camera_state, catalog_manager)

    elif phase == "BASELINE":
        if camera_state.latest_emotions:
            state.viewer_session.add_baseline_sample(camera_state.latest_emotions)
        if t >= PHASE_DURATIONS["BASELINE"]:
            enter_phase(state, "GALLERY")
            state.viewer_session.started_at = time.time()

    elif phase == "GALLERY":
        if camera_state.latest_emotions:
            state.viewer_session.add_gallery_sample(camera_state.latest_emotions, elapsed=t)
        if t >= PHASE_DURATIONS["GALLERY"]:
            _finalize_viewing(state, db_session, camera_state)
            enter_phase(state, "REVEAL")

    elif phase == "REVEAL":
        if t >= PHASE_DURATIONS["REVEAL"]:
            _reset(state)
            enter_phase(state, "IDLE")


def _handle_idle(state: InstallationState, camera_state, catalog_manager):
    from core.session import ViewerSession

    if state.show_mode:
        if not state.show_trigger:
            return
        state.show_trigger = False
    else:
        if not camera_state.hands_raised or camera_state.hands_raised_since is None:
            return
        held_for = time.time() - camera_state.hands_raised_since
        if held_for < LOCK_STABILITY_DURATION:
            return

    artwork = catalog_manager.pick_next()
    if artwork is None:
        return
    session = ViewerSession(artwork_id=artwork["id"], artwork_slug=artwork["slug"])
    state.viewer_session = session
    state.current_artwork = artwork
    enter_phase(state, "BASELINE")


def _finalize_viewing(state: InstallationState, db_session, camera_state):
    from vision.emotion import average_samples
    from core.verdict import (
        find_breaking_point, verdict_from_deviation,
        personal_verdict_text, save_viewing, collective_summary,
    )

    s = state.viewer_session
    baseline = average_samples(s.baseline_samples)
    bucket_avgs = [average_samples(bucket) for bucket in s.gallery_buckets]
    breaking_index, deviations = find_breaking_point(bucket_avgs, baseline)
    max_dev = max(deviations) if deviations else 0.0
    label = verdict_from_deviation(max_dev, breaking_index)

    avg = average_samples(s.emotion_samples)
    state.avg_emotions = avg
    state.baseline_emotions = baseline
    state.deviations = deviations
    state.breaking_index = breaking_index
    state.personal_verdict = label
    state.personal_lines = personal_verdict_text(avg)

    save_viewing(s, avg, label, db_session,
                 num_faces=max(1, camera_state.num_faces),
                 breaking_index=breaking_index)

    coll = collective_summary(s.artwork_id, avg, db_session)
    state.collective_data = coll


def _reset(state: InstallationState):
    state.viewer_session = None
    state.avg_emotions = {}
    state.baseline_emotions = {}
    state.deviations = []
    state.breaking_index = None
    state.personal_verdict = ""
    state.personal_lines = []
    state.current_artwork = None
    state.collective_data = None
