"""Generate ONE test sequence with the current iterate_degrade.py settings so
the degradation curve can be judged visually before a full catalog run.

Replicates the two-phase logic exactly: pictures 1..DIRECT_COUNT direct from
the original (seeded), the rest chained (model collapse).

Usage: python test_single.py [image_path]
Output: catalog_iterations_10_TEST/<stem>/0000..0010.png
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from PIL import Image
from iterate_degrade import (
    _fetch_prompt, _strength_for, _seed_for,
    ITERATIONS, DIRECT_COUNT, GUIDANCE, STEPS,
)

CATALOG_DIR = pathlib.Path(__file__).parent / "catalog"
OUT_ROOT    = pathlib.Path(__file__).parent / "catalog_iterations_10_TEST"


def main():
    img_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else sorted(CATALOG_DIR.glob("*.jpg"))[0]

    out_dir = OUT_ROOT / img_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    _, prompt = _fetch_prompt(img_path)
    print(f"Image:  {img_path.name}")
    print(f"Prompt: {prompt}")

    import torch
    from core.transform import load_pipeline
    print("Loading SD pipeline…")
    pipe = load_pipeline()

    original = Image.open(img_path).convert("RGB")
    size = original.size
    original.save(out_dir / "0000.png")

    source512 = original.resize((512, 512), Image.LANCZOS)
    seed = _seed_for(img_path.stem)
    current512 = None

    for i in range(1, ITERATIONS + 1):
        frame_path = out_dir / f"{i:04d}.png"
        if frame_path.exists():
            if i >= DIRECT_COUNT:
                current512 = Image.open(frame_path).convert("RGB").resize((512, 512), Image.LANCZOS)
            print(f"  {i:>2}/{ITERATIONS}  exists, skipped")
            continue
        s = _strength_for(i)
        working = source512 if i <= DIRECT_COUNT else current512
        gen = torch.Generator(pipe.device.type).manual_seed(seed if i <= DIRECT_COUNT else seed + i)
        result = pipe(
            prompt=prompt, image=working, strength=s,
            guidance_scale=GUIDANCE, num_inference_steps=STEPS,
            generator=gen,
        ).images[0]
        if i >= DIRECT_COUNT:
            current512 = result
        result.resize(size, Image.LANCZOS).save(frame_path)
        phase = "direct" if i <= DIRECT_COUNT else "chain "
        print(f"  {i:>2}/{ITERATIONS}  {phase}  strength={s:.3f}  saved")

    print(f"\nDone → {out_dir}")


if __name__ == "__main__":
    main()
