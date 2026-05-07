"""
Generate 10 uncanny SD frames for the prototype.

Picks one statue from the catalog, calls LLaVA once for a prompt,
then runs SD img2img at 10 increasing strengths.

Output:  proto_frames/
           00_original.jpg
           01_s012.jpg  …  10_s072.jpg

Run:  python make_proto_frames.py
"""

import io
import sys
import pathlib

# Allow imports from uncanny_maker
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT / "uncanny_maker"))

from PIL import Image

# ── Config ──────────────────────────────────────────────────────────────────────
SOURCE_IMAGE = ROOT / "uncanny_maker" / "catalog" / "Marble_portrait_of_the_emperor_Caracalla_253592.jpg"
OUT_DIR      = ROOT / "proto_frames"

# 10 strengths: subtle start (0.12) → strong finish (0.72)
STRENGTHS = [0.12, 0.19, 0.25, 0.32, 0.38, 0.45, 0.52, 0.58, 0.65, 0.72]

assert len(STRENGTHS) == 10, "Must be exactly 10 strengths"


def strength_tag(s: float) -> str:
    return f"s{round(s * 100):03d}"


def main():
    OUT_DIR.mkdir(exist_ok=True)

    # ── Load + crop to portrait ──────────────────────────────────────────────
    print(f"Source: {SOURCE_IMAGE.name}")
    original = Image.open(SOURCE_IMAGE).convert("RGB")
    ow, oh = original.size
    if ow / oh > 2 / 3:
        nw = int(oh * 2 / 3)
        left = (ow - nw) // 2
        original = original.crop((left, 0, left + nw, oh))
    # Keep native resolution for SD; resize to 512x768 (SD's sweet spot for portrait)
    original = original.resize((512, 768), Image.LANCZOS)
    print(f"Working size: {original.size}")

    # ── Save original ────────────────────────────────────────────────────────
    orig_path = OUT_DIR / "00_original.jpg"
    original.save(orig_path, format="JPEG", quality=92)
    print(f"Saved {orig_path.name}")

    # ── Check which frames already exist ────────────────────────────────────
    missing = [
        s for s in STRENGTHS
        if not (OUT_DIR / f"{STRENGTHS.index(s) + 1:02d}_{strength_tag(s)}.jpg").exists()
    ]
    if not missing:
        print("All 10 frames already exist — nothing to do.")
        print(f"\nFrames in: {OUT_DIR}")
        return

    # ── Prompt: try LLaVA, fall back to hardcoded ────────────────────────────
    # Hardcoded prompt crafted specifically for the Caracalla marble bust.
    # Used automatically when Ollama is not running.
    FALLBACK_PROMPT = (
        "marble Roman emperor bust becoming flesh, hyperrealistic, uncanny valley, "
        "waxy skin, glassy unseeing eyes, slightly wrong proportions, cold pallor, "
        "unsettling stillness, photorealistic sculpture, eerie lifelike stone"
    )
    try:
        print("\nConsulting LLaVA for uncanny prompt…")
        from core.llm import analyze_and_prompt
        image_bytes = io.BytesIO()
        original.save(image_bytes, format="JPEG", quality=92)
        prompt = analyze_and_prompt(image_bytes.getvalue())
        print(f"Prompt (LLaVA): {prompt}\n")
    except RuntimeError as e:
        print(f"LLaVA unavailable ({e})")
        print(f"Using hardcoded prompt instead.")
        prompt = FALLBACK_PROMPT
        print(f"Prompt (fallback): {prompt}\n")

    # ── Load SD pipeline ─────────────────────────────────────────────────────
    print("Loading Stable Diffusion pipeline…")
    from core.transform import load_pipeline, run_img2img
    load_pipeline()
    print("Pipeline ready.\n")

    # ── Generate 10 frames ───────────────────────────────────────────────────
    for i, strength in enumerate(STRENGTHS, start=1):
        tag  = strength_tag(strength)
        dest = OUT_DIR / f"{i:02d}_{tag}.jpg"

        if dest.exists():
            print(f"[{i:2d}/10] {dest.name}  already exists — skip")
            continue

        print(f"[{i:2d}/10] strength {strength:.2f}  →  {dest.name}")
        result = run_img2img(original, prompt, strength)
        result = result.resize((512, 768), Image.LANCZOS)
        result.save(dest, format="JPEG", quality=92)
        print(f"        saved {dest.name}")

    print(f"\nDone. Frames in: {OUT_DIR}")
    for p in sorted(OUT_DIR.glob("*.jpg")):
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
