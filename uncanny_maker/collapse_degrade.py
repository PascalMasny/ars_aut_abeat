"""
Forced model collapse — iterative feedback loop between LLaVA and Stable Diffusion.

Unlike iterate_degrade.py (which fixes the prompt at frame 0 and only drifts
the image), this script re-runs LLaVA on *every* output frame. The vision model
describes the AI's artefacts as real features; that description becomes the next
generation's prompt. Both the image and its semantic representation drift together.

This is the true model collapse feedback loop:
    LLaVA(frame_n) → prompt_n  → SD(frame_n, prompt_n) → frame_{n+1}
                      ↑                                        │
                      └────────────────────────────────────────┘

Differences from iterate_degrade.py:
  • LLaVA is called once per iteration (not once per image)
  • strength=0.60  (more change per pass — accelerates hallucination accumulation)
  • guidance=7.5   (stronger prompt adherence — drifting prompts have more effect)
  • Negative prompt drops "deformed" and "blurry" — allows collapse artefacts through
  • Output goes to catalog_collapse/<stem>/ so it never overwrites uncanny sequences

Usage:
    python collapse_degrade.py [--workers N] [--skip-compile] [--iters N]
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
OUTPUT_ROOT  = pathlib.Path(__file__).parent / "catalog_collapse"
IMAGE_EXTS   = {".jpg", ".jpeg", ".png", ".webp"}

ITERATIONS   = 100    # feedback loops per image
STRENGTH     = 0.60   # higher than uncanny (0.45) — accelerates collapse
GUIDANCE     = 7.5    # stronger prompt adherence amplifies drifting descriptions
STEPS        = 25     # inference steps per iteration

# Negative prompt deliberately omits "deformed" and "blurry" — those artefacts
# are the collapse signal we want to preserve, not suppress.
NEGATIVE_PROMPT = "cartoon, anime, text, watermark, logo, signature"

FALLBACK_PROMPT = "a human figure, classical artwork"
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

def _all_done(out_dir: pathlib.Path, iterations: int) -> bool:
    return (out_dir / f"{iterations:04d}.png").exists()


def _resume_point(out_dir: pathlib.Path, original: Image.Image, iterations: int):
    """Return (start_iter, current_frame) for resumable runs."""
    for n in range(iterations, 0, -1):
        frame = out_dir / f"{n:04d}.png"
        if frame.exists():
            return n + 1, Image.open(frame).convert("RGB")
    return 1, original


def _describe_frame(frame: Image.Image) -> str:
    """Run LLaVA on the current (possibly degraded) frame. Returns prompt string."""
    from core.llm import analyze_and_prompt
    buf = io.BytesIO()
    frame.save(buf, format="PNG")
    try:
        return analyze_and_prompt(buf.getvalue())
    except Exception:
        return FALLBACK_PROMPT


def _ema(prev: float, new: float, alpha: float = 0.25) -> float:
    return alpha * new + (1.0 - alpha) * prev


def _log_prompt_drift(i: int, prompt: str, prompt_log: pathlib.Path) -> None:
    with open(prompt_log, "a", encoding="utf-8") as f:
        f.write(f"{i:04d}\t{prompt}\n")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Forced model collapse pipeline")
    parser.add_argument("--workers", type=int, default=4,
                        help="Thread-pool workers for parallel LLaVA calls (default: 4). "
                             "Lower than iterate_degrade because LLaVA is called every iter.")
    parser.add_argument("--skip-compile", action="store_true",
                        help="Skip torch.compile() on the UNet")
    parser.add_argument("--iters", type=int, default=ITERATIONS,
                        help=f"Feedback iterations per image (default: {ITERATIONS})")
    args = parser.parse_args()

    iters = args.iters

    images = sorted(p for p in CATALOG_DIR.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    if not images:
        print(f"No images found in {CATALOG_DIR}")
        print("Run download_human_figures.py first.")
        sys.exit(1)

    pending = [p for p in images if not _all_done(OUTPUT_ROOT / p.stem, iters)]
    total   = len(images)
    done    = total - len(pending)
    print(f"Catalog: {total} image(s) — {done} already complete, {len(pending)} to process")
    if not pending:
        print("Nothing to do.")
        return

    print(f"Settings: {iters} iters · strength={STRENGTH} · guidance={GUIDANCE} · steps={STEPS}")
    print(f"Mode: LLaVA re-queried every iteration (forced model collapse)\n")

    # ── Load Stable Diffusion pipeline ────────────────────────────────────────
    import torch
    from diffusers import StableDiffusionImg2ImgPipeline
    from config import SD_MODEL_ID

    print("Loading Stable Diffusion pipeline…")
    device = ("mps" if torch.backends.mps.is_available()
               else "cuda" if torch.cuda.is_available()
               else "cpu")
    dtype  = torch.float16 if device in ("mps", "cuda") else torch.float32
    pipe   = StableDiffusionImg2ImgPipeline.from_pretrained(SD_MODEL_ID, torch_dtype=dtype)
    pipe   = pipe.to(device)
    pipe.safety_checker = None
    pipe.enable_attention_slicing(1)
    try:
        pipe.enable_vae_slicing()
    except AttributeError:
        pass

    if not args.skip_compile and hasattr(torch, "compile"):
        print("Compiling UNet with torch.compile() (first inference will be slower)…")
        try:
            pipe.unet = torch.compile(pipe.unet, mode="reduce-overhead", fullgraph=False)
        except Exception as e:
            print(f"  torch.compile() failed ({e}) — continuing without it")
    print(f"Pipeline ready on {device}.\n")

    saver = _SaveWorker()

    # ── Process each image sequentially ───────────────────────────────────────
    for img_idx, img_path in enumerate(pending, 1):
        out_dir = OUTPUT_ROOT / img_path.stem
        out_dir.mkdir(parents=True, exist_ok=True)

        prompt_log = out_dir / "prompts.tsv"  # records every prompt for analysis

        print(f"[{img_idx}/{len(pending)}] {img_path.name}")

        original      = Image.open(img_path).convert("RGB")
        original_size = original.size

        # Frame 0 = unmodified source
        saver.submit(original.copy(), out_dir / "0000.png")

        start_iter, current = _resume_point(out_dir, original, iters)
        if start_iter > 1:
            print(f"  Resuming from iteration {start_iter - 1}")

        ema_sec: Optional[float] = None
        t0 = time.perf_counter()

        # LLaVA executor — runs in parallel with SD to hide latency
        llava_executor = concurrent.futures.ThreadPoolExecutor(max_workers=args.workers)
        next_prompt_future: Optional[concurrent.futures.Future] = None

        # Pre-fetch prompt for the first iteration
        next_prompt_future = llava_executor.submit(_describe_frame, current)

        for i in range(start_iter, iters + 1):
            t_iter = time.perf_counter()

            # Collect prompt for this iteration (was fetched during previous SD run)
            prompt = next_prompt_future.result() if next_prompt_future else FALLBACK_PROMPT
            short  = prompt[:70] + "…" if len(prompt) > 70 else prompt
            _log_prompt_drift(i, prompt, prompt_log)

            # Run Stable Diffusion
            working = current.resize((512, 512), Image.LANCZOS)
            result  = pipe(
                prompt              = prompt,
                negative_prompt     = NEGATIVE_PROMPT,
                image               = working,
                strength            = STRENGTH,
                guidance_scale      = GUIDANCE,
                num_inference_steps = STEPS,
            ).images[0]
            current = result.resize(original_size, Image.LANCZOS)

            # Non-blocking save
            saver.submit(current.copy(), out_dir / f"{i:04d}.png")

            # Pre-fetch prompt for *next* iteration while SD would be running
            if i < iters:
                next_prompt_future = llava_executor.submit(_describe_frame, current.copy())

            iter_sec = time.perf_counter() - t_iter
            ema_sec  = iter_sec if ema_sec is None else _ema(ema_sec, iter_sec)
            remaining = ema_sec * (iters - i)
            print(
                f"  {i:>3}/{iters}  {iter_sec:.1f}s/iter  "
                f"ETA {remaining/60:.1f} min  [{short}]          ",
                end="\r",
            )

        llava_executor.shutdown(wait=False)
        elapsed = time.perf_counter() - t0
        print(f"\n  Done in {elapsed/60:.1f} min → {out_dir}")
        print(f"  Prompt drift log: {prompt_log}\n")

    print("Flushing remaining frame saves…")
    saver.flush()
    print(f"\nAll done. Output: {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
