# uncanny_maker

Offline preprocessing pipeline for *Vallis Simulacri*. Downloads public-domain artworks from the Met Museum Open Access API and generates 100-frame AI-degradation sequences used by the gallery application.

Run this once before the first installation session, or again whenever you want to expand the artwork catalog.

## Prerequisites

```bash
pip install -r requirements.txt
```

Optional but recommended: [Ollama](https://ollama.com) with the `llava` model for artwork-specific prompt generation.

```bash
ollama pull llava
ollama serve   # keep this running in a separate terminal
```

Without Ollama the pipeline falls back to a generic prompt — results are slightly less tailored but still work fine.

Stable Diffusion v1.5 (~4 GB) is downloaded automatically from Hugging Face on the first run of `iterate_degrade.py`.

## Usage

### Step 1 — Download source artworks

```bash
python download_human_figures.py
```

Queries the Met Museum API for ~200 public-domain works featuring human figures (classical sculpture, Renaissance portraits, figurative paintings) and saves them to `catalog/`. Already-downloaded images are skipped, so the script is safe to re-run.

### Step 2 — Generate degradation sequences

```bash
python iterate_degrade.py
```

For each image in `catalog/`, runs 100 rounds of Stable Diffusion img2img, feeding each output back as the next input. Output frames are saved to `catalog_iterations/<slug>/0000.png` … `0100.png`.

Resumable: frames already on disk are skipped. Interrupted runs continue from where they left off.

**Options:**

| Flag | Default | Effect |
|------|---------|--------|
| `--workers N` | `8` | Parallel threads for LLaVA prompt fetching |
| `--skip-compile` | off | Skip `torch.compile()` on the UNet (use if it errors) |

**Tunable constants** (top of `iterate_degrade.py`):

| Variable | Default | Effect |
|----------|---------|--------|
| `ITERATIONS` | `100` | Feedback loops per image |
| `STRENGTH` | `0.45` | Per-iteration change magnitude |
| `GUIDANCE` | `6.0` | Classifier-free guidance scale |
| `STEPS` | `25` | Inference steps (speed vs. quality) |

## Hardware

Device is detected automatically: **MPS** (Apple Silicon) → **CUDA** → **CPU**.

Approximate runtimes per image at default settings:

| Hardware | Time |
|----------|------|
| M4 Max (MPS) | ~8–12 min |
| NVIDIA GPU (CUDA) | ~3–6 min |
| CPU only | ~60–120 min |

## Output

```
catalog_iterations/
└── The_Dance_Class_438817/
    ├── 0000.png   ← original (unmodified)
    ├── 0001.png
    │   …
    └── 0100.png   ← after 100 iterations
```

`catalog_iterations/` is excluded from version control (~10 GB). Copy or symlink it to where `ars_aut_abeat` can find it, or set the path in `ars_aut_abeat/config.py`.

## Directory Structure

```
uncanny_maker/
├── iterate_degrade.py          Main degradation script
├── download_human_figures.py   Met Museum scraper
├── config.py                   Ollama / SD model settings
├── requirements.txt
├── catalog/                    Source images (git-ignored, ~400 MB)
├── catalog_iterations/         Generated sequences (git-ignored, ~10 GB)
├── core/
│   ├── llm.py                  LLaVA prompt generation via Ollama
│   └── transform.py            Stable Diffusion img2img wrapper
└── _archive/
    └── old_scripts/            Superseded approaches (kept for reference)
```

## Configuration

All model/server settings are in `config.py`:

```python
OLLAMA_URL     = "http://localhost:11434"
OLLAMA_MODEL   = "llava"
SD_MODEL_ID    = "runwayml/stable-diffusion-v1-5"
DEFAULT_STRENGTH = 0.55
DEFAULT_GUIDANCE = 7.5
NEGATIVE_PROMPT  = "cartoon, anime, painting, sketch, blurry, ..."
```

See [`docs/PIPELINE.md`](../docs/PIPELINE.md) for a detailed explanation of the degradation algorithm and why it produces uncanny-valley-specific distortion.
