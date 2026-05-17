"""Matplotlib graph generators sized for the 112:199 portrait column."""

import io
import base64
import json


def recap_graph(timestamps: list, samples: list) -> str:
    """Emotion-over-time line chart. Portrait-friendly: wide/shallow aspect ratio."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from config import EMOTION_LATIN

    colors = {
        "happy":    "#E8C87A",
        "sad":      "#6B9E7A",
        "angry":    "#CC5555",
        "surprise": "#C9A961",
        "fear":     "#9B7FCC",
        "disgust":  "#C97A50",
        "neutral":  "#8B8B7E",
    }

    # figsize chosen so that when rendered at dpi=130 and displayed at the
    # full column width (~600 px) the resulting height is ≈25 vh.
    fig, ax = plt.subplots(figsize=(6.0, 3.2))

    if timestamps and samples:
        for emotion, color in colors.items():
            values = [s.get(emotion, 0) * 100 for s in samples]
            ax.plot(timestamps, values, color=color, linewidth=2.2,
                    label=EMOTION_LATIN.get(emotion, emotion), alpha=0.92)

    fig.patch.set_facecolor("#1C1410")
    ax.set_facecolor("#120E0A")
    ax.tick_params(colors="#8B6F2E", labelsize=11)
    for spine in ax.spines.values():
        spine.set_color("#3D2810")
    ax.set_xlabel("Seconds", color="#8B6F2E", fontsize=12)
    ax.set_ylabel("Intensity %", color="#8B6F2E", fontsize=12)
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 100)
    ax.legend(
        loc="upper right", facecolor="#1C1410", edgecolor="#3D2810",
        labelcolor="#C9A961", fontsize=10, framealpha=0.9,
        ncol=2, handlelength=1.4, borderpad=0.6,
    )
    ax.grid(axis="y", color="#2A1E0A", linewidth=0.7, alpha=0.7)
    fig.subplots_adjust(left=0.10, right=0.97, top=0.94, bottom=0.17)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def attract_graph(db) -> str | None:
    """Verdict donut + average emotion bars, stacked vertically for portrait display."""
    from data.models import Viewing
    from config import EMOTION_LATIN

    viewings = db.query(Viewing).all()
    if not viewings:
        return None

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    verdict_counts: dict = {"VALLIS": 0, "LIMEN": 0, "FIRMA": 0}
    emotion_sums: dict = {}
    emotion_n = 0
    for v in viewings:
        verdict_counts[v.verdict] = verdict_counts.get(v.verdict, 0) + 1
        try:
            em = json.loads(v.emotion_json) if isinstance(v.emotion_json, str) else {}
        except Exception:
            em = {}
        if em:
            for k, val in em.items():
                emotion_sums[k] = emotion_sums.get(k, 0.0) + val
            emotion_n += 1

    avg_emotions = {k: v / emotion_n for k, v in emotion_sums.items()} if emotion_n else {}

    # Stacked vertically: donut on top, horizontal bars below.
    # Aspect ratio ~0.85:1 (portrait-friendly) — displayed at full column width
    # the height comes to roughly 50 vh which fits the attract overlay.
    fig, (ax_donut, ax_bar) = plt.subplots(
        2, 1, figsize=(5.0, 6.0),
        gridspec_kw={"height_ratios": [1.15, 1]},
    )
    fig.patch.set_facecolor("#1C1410")

    # ── Donut ──────────────────────────────────────────────────────────────────
    donut_labels    = [k for k, c in verdict_counts.items() if c > 0]
    donut_sizes     = [verdict_counts[k] for k in donut_labels]
    donut_color_map = {"VALLIS": "#8B2222", "LIMEN": "#6B7B5E", "FIRMA": "#C9A961"}
    d_colors        = [donut_color_map.get(k, "#888888") for k in donut_labels]

    if donut_sizes:
        wedges, _, autotexts = ax_donut.pie(
            donut_sizes,
            labels=None,
            colors=d_colors,
            autopct=lambda p: f"{p:.0f}%" if p > 5 else "",
            pctdistance=0.72,
            startangle=90,
            wedgeprops={"width": 0.52, "edgecolor": "#1C1410", "linewidth": 2.5},
        )
        for at in autotexts:
            at.set_color("#F4E8D0")
            at.set_fontsize(13)
        ax_donut.legend(
            wedges,
            [f"{k}  ({verdict_counts[k]})" for k in donut_labels],
            loc="lower center",
            facecolor="#1C1410", edgecolor="#3D2810", labelcolor="#C9A961",
            fontsize=11, framealpha=0.9,
            ncol=len(donut_labels),
            bbox_to_anchor=(0.5, -0.12),
        )
    else:
        ax_donut.text(0.5, 0.5, "No data yet", ha="center", va="center",
                      color="#8B6F2E", fontsize=13, fontfamily="serif",
                      transform=ax_donut.transAxes)

    ax_donut.set_facecolor("#1C1410")
    ax_donut.set_title("VERDICT DISTRIBUTION", color="#8B6F2E",
                        fontsize=12, fontfamily="serif", pad=8, fontweight="bold")

    # ── Horizontal bar chart ────────────────────────────────────────────────────
    emotion_colors = {
        "happy": "#E8C87A", "sad": "#6B9E7A", "angry": "#CC5555",
        "surprise": "#C9A961", "fear": "#9B7FCC", "disgust": "#C97A50",
        "neutral": "#8B8B7E",
    }
    if avg_emotions:
        sorted_em  = sorted(avg_emotions.items(), key=lambda x: x[1], reverse=True)
        bar_labels = [EMOTION_LATIN.get(k, k.capitalize()) for k, _ in sorted_em]
        bar_values = [v * 100 for _, v in sorted_em]
        b_colors   = [emotion_colors.get(k, "#C9A961") for k, _ in sorted_em]
        ax_bar.barh(bar_labels[::-1], bar_values[::-1],
                    color=b_colors[::-1], edgecolor="#1C1410",
                    linewidth=0.5, height=0.65)
        ax_bar.set_xlim(0, 100)
        ax_bar.set_xlabel("Average Intensity %", color="#8B6F2E", fontsize=11)
        ax_bar.tick_params(colors="#8B6F2E", labelsize=11)
        for spine in ax_bar.spines.values():
            spine.set_color("#3D2810")
        ax_bar.grid(axis="x", color="#2A1E0A", linewidth=0.6, alpha=0.6)
    else:
        ax_bar.text(0.5, 0.5, "No emotion data yet", ha="center", va="center",
                    color="#8B6F2E", fontsize=13, fontfamily="serif",
                    transform=ax_bar.transAxes)

    ax_bar.set_facecolor("#120E0A")
    ax_bar.set_title("AVERAGE EMOTIONAL RESPONSE", color="#8B6F2E",
                      fontsize=12, fontfamily="serif", pad=8, fontweight="bold")

    fig.subplots_adjust(left=0.15, right=0.97, top=0.94, bottom=0.12, hspace=0.55)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()
