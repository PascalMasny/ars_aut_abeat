"""
Iterative AI degradation — optimised for Apple M4 Max / MPS.

Each image is fed through Stable Diffusion img2img ITERATIONS times.
The output of each pass becomes the input for the next, so artefacts
accumulate like a visual game of telephone. LLaVA is called once per
image to produce an anchoring prompt; the same prompt is reused for
all 100 iterations so drift is driven by the model's own reconstruction
errors rather than changing instructions.

Performance features (M4 Max / MPS):
  • All LLaVA prompts are fetched in parallel before SD starts
  • Frame saves happen in a background I/O thread — SD never stalls on disk
  • enable_attention_slicing + enable_vae_slicing for MPS memory throughput
  • torch.compile() on the UNet for ~15–25 % faster inference (PyTorch 2.x)
  • Exponential-moving-average ETA per image

Output:
    catalog_iterations/<stem>/0000.png  ← original
    catalog_iterations/<stem>/0001.png  ← iteration 1
    …
    catalog_iterations/<stem>/0100.png  ← iteration 100

The run is resumable: frames already on disk are skipped.

Usage:
    python iterate_degrade.py [--workers N] [--skip-compile]
"""

import io
import sys
import time
import queue
import pathlib
import threading
import argparse
import concurrent.futures
from typing import Optional

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from PIL import Image

# ── Configuration ──────────────────────────────────────────────────────────────
CATALOG_DIR  = pathlib.Path(__file__).parent / "catalog"
OUTPUT_ROOT  = pathlib.Path(__file__).parent / "catalog_iterations"
IMAGE_EXTS   = {".jpg", ".jpeg", ".png", ".webp"}

ITERATIONS   = 100    # feedback loops per image
STRENGTH     = 0.45   # per-iteration change magnitude (0.1 subtle → 0.9 heavy)
GUIDANCE     = 6.0    # classifier-free guidance scale
STEPS        = 25     # inference steps per iteration
# ──────────────────────────────────────────────────────────────────────────────


# ── Background I/O thread ─────────────────────────────────────────────────────

class _SaveWorker:
    """Saves PIL images to disk on a dedicated thread so SD is never I/O-bound."""

    def __init__(self):
        self._q: queue.Queue = queue.Queue()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def submit(self, image: Image.Image, path: pathlib.Path) -> None:
        self._q.put((image, path))

    def flush(self) -> None:
        self._q.join()

    def _loop(self) -> None:
        while True:
            image, path = self._q.get()
            try:
                image.save(path)
            finally:
                self._q.task_done()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _all_done(out_dir: pathlib.Path) -> bool:
    return (out_dir / f"{ITERATIONS:04d}.png").exists()


def _resume_point(out_dir: pathlib.Path, original: Image.Image):
    """Return (start_iter, current_frame) for resumable runs."""
    for n in range(ITERATIONS, 0, -1):
        frame = out_dir / f"{n:04d}.png"
        if frame.exists():
            return n + 1, Image.open(frame).convert("RGB")
    return 1, original


def _fetch_prompt(img_path: pathlib.Path) -> tuple[pathlib.Path, str]:
    """Fetch a LLaVA prompt for one image (called from a thread pool)."""
    from core.llm import analyze_and_prompt
    image_bytes = img_path.read_bytes()
    try:
        prompt = analyze_and_prompt(image_bytes)
    except (RuntimeError, Exception):
        prompt = "classical painting, human figure, museum artwork, detailed"
    return img_path, prompt


def _ema(prev: float, new: float, alpha: float = 0.25) -> float:
    return alpha * new + (1.0 - alpha) * prev


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Iterative AI degradation pipeline")
    parser.add_argument("--workers", type=int, default=8,
                        help="Thread-pool workers for parallel LLaVA queries (default: 8)")
    parser.add_argument("--skip-compile", action="store_true",
                        help="Skip torch.compile() on the UNet (use if it causes errors)")
    args = parser.parse_args()

    images = sorted(p for p in CATALOG_DIR.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    if not images:
        print(f"No images found in {CATALOG_DIR}")
        print("Run download_human_figures.py first.")
        sys.exit(1)

    pending = [p for p in images if not _all_done(OUTPUT_ROOT / p.stem)]
    total   = len(images)
    done    = total - len(pending)
    print(f"Catalog: {total} image(s) — {done} already complete, {len(pending)} to process")
    if not pending:
        print("Nothing to do.")
        return

    print(f"Settings: {ITERATIONS} iters · strength={STRENGTH} · guidance={GUIDANCE} · steps={STEPS}\n")

    # ── Pre-fetch all LLaVA prompts in parallel ────────────────────────────────
    print(f"Fetching LLaVA prompts in parallel ({args.workers} workers)…")
    prompts: dict[pathlib.Path, str] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(_fetch_prompt, p): p for p in pending}
        for fut in concurrent.futures.as_completed(futures):
            img_path, prompt = fut.result()
            prompts[img_path] = prompt
            short = prompt[:60] + "…" if len(prompt) > 60 else prompt
            print(f"  [{img_path.name}] {short}")
    print()

    # ── Load Stable Diffusion pipeline ────────────────────────────────────────
    import torch
    from core.transform import load_pipeline

    print("Loading Stable Diffusion pipeline…")
    pipe = load_pipeline()

    # torch.compile() on the UNet — gives ~15-25 % throughput gain on MPS
    if not args.skip_compile and hasattr(torch, "compile"):
        print("Compiling UNet with torch.compile() (first inference will be slower)…")
        try:
            pipe.unet = torch.compile(pipe.unet, mode="reduce-overhead", fullgraph=False)
        except Exception as e:
            print(f"  torch.compile() failed ({e}) — continuing without it")
    print("Pipeline ready.\n")

    saver = _SaveWorker()

    # ── Process each image sequentially ───────────────────────────────────────
    for idx, img_path in enumerate(pending, 1):
        out_dir = OUTPUT_ROOT / img_path.stem
        out_dir.mkdir(parents=True, exist_ok=True)

        prompt = prompts[img_path]
        print(f"[{idx}/{len(pending)}] {img_path.name}")
        print(f"  Prompt: {prompt}")

        original      = Image.open(img_path).convert("RGB")
        original_size = original.size

        # Frame 0 = unmodified source
        saver.submit(original.copy(), out_dir / "0000.png")

        start_iter, current = _resume_point(out_dir, original)
        if start_iter > 1:
            print(f"  Resuming from iteration {start_iter - 1}")

        ema_sec: Optional[float] = None
        t0 = time.perf_counter()

        for i in range(start_iter, ITERATIONS + 1):
            t_iter = time.perf_counter()

            working = current.resize((512, 512), Image.LANCZOS)
            result  = pipe(
                prompt            = prompt,
                image             = working,
                strength          = STRENGTH,
                guidance_scale    = GUIDANCE,
                num_inference_steps = STEPS,
            ).images[0]
            current = result.resize(original_size, Image.LANCZOS)

            # Non-blocking save
            saver.submit(current.copy(), out_dir / f"{i:04d}.png")

            iter_sec = time.perf_counter() - t_iter
            ema_sec  = iter_sec if ema_sec is None else _ema(ema_sec, iter_sec)
            remaining = ema_sec * (ITERATIONS - i)
            print(
                f"  {i:>3}/{ITERATIONS}  {iter_sec:.1f}s/iter  "
                f"ETA {remaining/60:.1f} min          ",
                end="\r",
            )

        elapsed = time.perf_counter() - t0
        print(f"\n  Done in {elapsed/60:.1f} min → {out_dir}\n")

    # Flush remaining saves before exit
    print("Flushing remaining frame saves…")
    saver.flush()
    print(f"\nAll done. Output: {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
