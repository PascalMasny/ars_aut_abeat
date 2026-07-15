import json
from config import (
    VERDICT_VALLIS_THRESHOLD, VERDICT_FIRMA_THRESHOLD, EMOTION_LATIN,
    BREAKING_WEIGHTS, BREAKING_MIN_DEVIATION, VERDICT_VALLIS_DEVIATION,
)
from data.stats import artwork_summary, concordance, _score
from data.models import Viewing
from vision.emotion import dominant_emotion, EMOTION_KEYS


def score_emotions(emotions: dict[str, float]) -> float:
    return _score(emotions)


def verdict_label(score: float) -> str:
    # VALLIS — fell into the uncanny valley (high disgust/fear)
    # LIMEN  — on the threshold (mixed / unsure)
    # FIRMA  — stable ground, unaffected by the likeness
    if score >= VERDICT_VALLIS_THRESHOLD:
        return "VALLIS"
    elif score >= VERDICT_FIRMA_THRESHOLD:
        return "LIMEN"
    return "FIRMA"


def deviation_score(emotions: dict[str, float], baseline: dict[str, float]) -> float:
    """Weighted absolute deviation of an emotion vector from the baseline."""
    return sum(
        BREAKING_WEIGHTS.get(k, 0.0) * abs(emotions.get(k, 0.0) - baseline.get(k, 0.0))
        for k in EMOTION_KEYS
    )


def find_breaking_point(
    bucket_avgs: list[dict[str, float]], baseline: dict[str, float]
) -> tuple[int | None, list[float]]:
    """Picture (1-based) where the viewer's emotions deviated most from baseline.

    Returns (None, deviations) when no picture provoked a deviation above
    BREAKING_MIN_DEVIATION — for this viewer, it never stopped being art.
    """
    deviations = [
        deviation_score(avg, baseline) if avg else 0.0
        for avg in bucket_avgs
    ]
    if not baseline or not any(deviations):
        return None, deviations
    best = max(range(len(deviations)), key=lambda i: deviations[i])
    if deviations[best] < BREAKING_MIN_DEVIATION:
        return None, deviations
    return best + 1, deviations


def verdict_from_deviation(max_deviation: float, breaking_index: int | None) -> str:
    if breaking_index is None:
        return "FIRMA"
    if max_deviation >= VERDICT_VALLIS_DEVIATION:
        return "VALLIS"
    return "LIMEN"


def personal_verdict_text(emotions: dict[str, float]) -> list[tuple[str, float]]:
    """Returns sorted list of (latin_name, pct) for display."""
    lines = []
    for eng, pct in sorted(emotions.items(), key=lambda x: -x[1]):
        latin = EMOTION_LATIN.get(eng, eng.capitalize())
        lines.append((latin, round(pct * 100, 1)))
    return lines


def save_viewing(session_obj, avg_emotions: dict, verdict: str, db_session,
                 num_faces: int = 1, breaking_index: int | None = None):
    v = Viewing(
        artwork_id=session_obj.artwork_id,
        session_id=session_obj.session_id,
        duration_seconds=session_obj.duration(),
        emotion_json=json.dumps(avg_emotions),
        dominant_emotion=dominant_emotion(avg_emotions),
        verdict=verdict,
        num_faces_in_frame=num_faces,
        breaking_index=breaking_index,
    )
    db_session.add(v)
    db_session.commit()


def collective_summary(artwork_id: int, viewer_emotions: dict, db_session) -> dict:
    summary = artwork_summary(artwork_id, db_session)
    conc = concordance(viewer_emotions, summary.get("avg_emotions", {}))
    score = summary.get("score", 0.5)
    label = verdict_label(score)
    if summary["avg_emotions"]:
        dominant = max(summary["avg_emotions"], key=summary["avg_emotions"].get)
        dominant_latin = EMOTION_LATIN.get(dominant, dominant.capitalize())
    else:
        dominant = "neutral"
        dominant_latin = EMOTION_LATIN["neutral"]
    return {
        "count": summary["count"],
        "avg_emotions": summary["avg_emotions"],
        "score": score,
        "verdict": label,
        "concordance": conc,
        "dominant": dominant,
        "dominant_latin": dominant_latin,
        "verdict_counts": summary.get("verdict_counts", {}),
    }
