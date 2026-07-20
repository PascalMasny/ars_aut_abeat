# How to regenerate the artwork catalog from an empty checkout

Start from a fresh `git clone` with no images on disk and end with a running
installation showing all 169 artworks. This is the recovery path after the image
directories have been deleted — they are excluded from git by design, so a clone
never contains them.

Total wall-clock: **~3 hours on an Apple M-series**, most of it unattended.

## Prerequisites

- Python 3.10–3.12 (MediaPipe has no 3.13 wheels yet)
- A GPU: Apple M-series (MPS) or NVIDIA (CUDA). CPU works but takes ~10× longer.
- ~15 GB free disk (362 MB sources + 11 GB pictures + 4 GB model cache)
- Network access to `collectionapi.metmuseum.org` and `huggingface.co`
- Optional: [Ollama](https://ollama.com) with the `llava` model, for prompt generation

```bash
cd uncanny_maker
pip install -r requirements.txt
```

## Step 1: Restore the source artworks

```bash
python restore_catalog.py
```

Downloads the exact 169 Met Museum images listed in
[`CATALOG_MANIFEST.md`](CATALOG_MANIFEST.md), each under its original filename.

Expected output:

```
Manifest: 169 artworks — 0 present, 169 missing
Target:   .../uncanny_maker/catalog

  [  1/169] 436284  A_Donor_Presented_by_a_Saint_436284
  ...
Restored 169/169 file(s).
```

**Use this, not `download_human_figures.py`.** That script discovers artworks by
keyword search and selects them by index into the result set. Met search results
shift over time, so re-running it yields a *different* catalog: different
artworks, different filename stems, and therefore different seeds and different
pictures. It is the right tool for building a *new* catalog, the wrong one for
restoring this one.

Verify before continuing:

```bash
ls catalog/*.jpg | wc -l     # expect 169
```

If some artworks fail (the Met occasionally withdraws an image or revokes
public-domain status), the script lists them and continues. A smaller catalog is
fine — `CatalogManager` loads whatever is present.

## Step 2: Generate the picture sequences

Optional but recommended, in a second terminal:

```bash
ollama serve
ollama pull llava
```

Then:

```bash
python iterate_degrade.py
```

This is the long step: 169 artworks × 10 pictures, about **1 min per artwork on
M-series**, ~30 s on NVIDIA. Stable Diffusion v1.5 (~4 GB) downloads on first run
and is cached in `~/.cache/huggingface/`.

Expected output:

```
Catalog: 169 image(s) — 0 already complete, 169 to process
Settings: 10 pictures · direct 1–5 0.1→0.3 · chain 6–10 0.22→0.42 · guidance=6.0 · steps=25

Fetching LLaVA prompts in parallel (8 workers)…
  [A_Woman_Reading_435991.jpg] hyperrealistic woman reading, glassy eyes, waxy skin…

Loading Stable Diffusion pipeline…
[1/169] A_Donor_Presented_by_a_Saint_436284.jpg
   10/10  5.8s/iter  ETA 0.0 min
  Done in 1.0 min → catalog_iterations_10/A_Donor_Presented_by_a_Saint_436284
```

**Fully resumable.** Kill it and re-run any time; artworks whose `0010.png`
exists are skipped, and chained pictures reload their predecessor from disk.

If `torch.compile()` errors on your PyTorch build:

```bash
python iterate_degrade.py --skip-compile
```

## Step 3: Verify

```bash
ls -d catalog_iterations_10/*/ | wc -l              # expect 169
find catalog_iterations_10 -name '0010.png' | wc -l # expect 169 — all complete
du -sh catalog_iterations_10                        # expect ~11 GB
```

Every artwork directory should hold 11 files, `0000.png` (the untouched source)
through `0010.png`.

## Step 4: Run the installation

```bash
cd ../ars_aut_abeat
./start.sh
```

Open `http://localhost:8000`. Raise both hands for 1.5 s to trigger a run, or
switch to SHOW mode and press Space.

## How exact is the reproduction?

Pictures are deterministic given the source image and its filename:
`iterate_degrade.py` seeds each artwork with `zlib.crc32(stem)` and each chained
step with `seed + i`. Same input file, same stem, same
`DIRECT_*`/`CHAIN_*`/`GUIDANCE`/`STEPS` → same pictures, bit for bit.

Two things break exactness, neither of which affects how the piece works:

1. **The LLaVA prompt.** Ollama's output is not deterministic, so a re-run
   produces a differently-worded anchoring prompt and therefore visually
   different (not worse) pictures. Running *without* Ollama is fully
   deterministic — every artwork falls back to the fixed prompt
   `"classical painting, human figure, museum artwork, detailed"`.
2. **Model or library versions.** A different `diffusers`, `torch`, or
   `stable-diffusion-v1-5` revision changes the numerics.

To reproduce the pictures exactly as first generated, run **without Ollama**.
To reproduce the *installation as exhibited*, any run is fine — the measurement
concept does not depend on specific pixels.

## Troubleshooting

**`No images found in .../catalog` from `iterate_degrade.py`**
Step 1 did not run or wrote elsewhere. Check `ls catalog/*.jpg | wc -l`.

**The app starts but stays on IDLE and never triggers**
`CatalogManager` found zero artworks, so `pick_next()` returns `None` and the
state machine cannot leave IDLE. It scans `uncanny_maker/catalog/*.jpg` and
requires a matching `catalog_iterations_10/{stem}/0010.png`. A source JPEG with
no completed sequence is silently skipped. Re-run Step 2.

**Pictures 404 in the browser, artwork title shows**
`/frames` is mounted at import time only if `catalog_iterations_10/` exists.
If you generated pictures while the server was running, restart it.

**`RuntimeError: Cannot reach Ollama`**
Harmless. Prompt generation falls back to the fixed prompt. Start `ollama serve`
first if you want LLaVA-guided prompts.

**Out of memory on MPS/CUDA**
Lower `STEPS` in `iterate_degrade.py` (25 → 15 roughly halves runtime and memory
pressure with minor quality loss), or run with `--skip-compile`.

## Related

- [`CATALOG_MANIFEST.md`](CATALOG_MANIFEST.md) — the exact 169-artwork source list
- [`PIPELINE.md`](PIPELINE.md) — why the two-phase degradation works the way it does
- [`ARCHITECTURE.md`](ARCHITECTURE.md#configuration-reference-configpy) — every tunable parameter
