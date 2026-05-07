"""
Batch-process all images in catalog/ at three uncanny strengths.

Output structure:
    catalog_uncanny/
        20/   ← strength 0.20
        60/   ← strength 0.60
        80/   ← strength 0.80

Ollama is called ONCE per image; the resulting prompt is reused for all
three strength variants. Already-completed files are skipped so the run
can be safely interrupted and resumed.

Usage:
    python batch_uncanny.py

Requires:
    - Ollama running:  ollama serve  +  ollama pull llava
    - pip install diffusers torch transformers accelerate Pillow requests
"""

import io
import sys
import os
import pathlib
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from PIL import Image

CATALOG_DIR  = pathlib.Path(__file__).parent / "catalog"
OUTPUT_ROOT  = pathlib.Path(__file__).parent / "catalog_uncanny"
STRENGTHS    = [0.20, 0.60, 0.80]
IMAGE_EXTS   = {".jpg", ".jpeg", ".png", ".webp"}


def strength_label(s: float) -> str:
    return str(int(s * 100))


def output_path(strength: float, filename: str) -> pathlib.Path:
    folder = OUTPUT_ROOT / strength_label(strength)
    folder.mkdir(parents=True, exist_ok=True)
    stem = pathlib.Path(filename).stem
    return folder / f"{stem}.png"


def all_done(filename: str) -> bool:
    return all(output_path(s, filename).exists() for s in STRENGTHS)


def main():
    images = sorted(
        p for p in CATALOG_DIR.iterdir()
        if p.suffix.lower() in IMAGE_EXTS
    )
    if not images:
        print(f"No images found in {CATALOG_DIR}")
        sys.exit(1)

    total = len(images)
    print(f"Found {total} images in {CATALOG_DIR}")
    print(f"Output → {OUTPUT_ROOT}\n")

    # Import heavy deps here so startup is fast
    from core.llm import analyze_and_prompt
    from core.transform import load_pipeline, run_img2img

    print("Loading Stable Diffusion pipeline (first run downloads ~4 GB)…")
    load_pipeline()
    print("Pipeline ready.\n")

    for i, img_path in enumerate(images, 1):
        filename = img_path.name
        print(f"[{i:>3}/{total}] {filename}")

        if all_done(filename):
            print("         already complete — skipping\n")
            continue

        # Read image bytes once
        image_bytes = img_path.read_bytes()
        original = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Call LLM once per image
        try:
            print("         consulting oracle (LLaVA)…")
            prompt = analyze_and_prompt(image_bytes)
            print(f"         prompt: {prompt}")
        except RuntimeError as e:
            print(f"         LLM error: {e} — skipping\n")
            continue

        # Apply each strength
        for strength in STRENGTHS:
            label = strength_label(strength)
            dest = output_path(strength, filename)

            if dest.exists():
                print(f"         {label}% already exists — skipping")
                continue

            print(f"         transforming at {label}%…")
            try:
                result = run_img2img(original, prompt, strength)
                result.save(dest, format="PNG")
                print(f"         saved → {dest.relative_to(pathlib.Path(__file__).parent)}")
            except Exception as e:
                print(f"         transform error at {label}%: {e}")

        print()

    print("Done.")
    for s in STRENGTHS:
        folder = OUTPUT_ROOT / strength_label(s)
        count = len(list(folder.glob("*.png"))) if folder.exists() else 0
        print(f"  {strength_label(s)}%  →  {count} images  ({folder})")


if __name__ == "__main__":
    main()
