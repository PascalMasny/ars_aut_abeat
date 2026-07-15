# Preprocessing Pipeline — uncanny_maker

The `uncanny_maker` pipeline is a standalone tool that produces the artwork catalog consumed by the gallery application. It runs entirely offline and only needs to be executed once per catalog update.

## Overview

```
Met Museum Open Access API
         │
         ▼
download_human_figures.py
         │  saves full-resolution JPEGs
         ▼
  catalog/<ObjectID>_<Title>.jpg   (source images)
         │
         ▼
iterate_degrade.py  (one run per image)
         │  LLaVA → description prompt
         │  Stable Diffusion img2img × 10 pictures:
         │  1–5 direct from original (0.10 → 0.30, fixed seed)
         │  6–10 chained feedback / model collapse (0.22 → 0.42)
         ▼
  catalog_iterations_10/<stem>/0000.png … 0010.png
```

---

## Step 1 — Acquiring Source Artworks

`download_human_figures.py` queries the Met Museum Open Access API for public-domain works that feature human figures: classical sculptures, Renaissance portraits, figure paintings, and devotional panels.

**Query strategy**

Three searches are issued in sequence:

| Query | Target |
|-------|--------|
| `"figure" AND "classical"` | Greco-Roman sculpture |
| `"portrait" AND "Renaissance"` | 15th–17th century oil portraits |
| `"figure" AND "painting"` | Broader figurative paintings |

Each result is filtered to artworks that:
- Have `isPublicDomain = true`
- Carry a primary image URL
- Belong to medium categories likely to contain human figures (checked via `medium` field keyword scan)

**Output**

Images are saved as `catalog/<objectID>_<sanitised_title>.jpg`. The script is resumable: if a file matching `*<objectID>*.jpg` already exists in `catalog/`, that object is skipped.

Typical run: ~200 images, runtime depends on network speed.

---

## Step 2 — Generating Degradation Sequences

`iterate_degrade.py` generates 10 pictures per source image in **two phases**:

- **Phase 1 — pictures 1–5, direct.** Each is a single img2img pass straight from the original with a gentle strength ramp (0.10 → 0.30) and a per-artwork fixed seed. One VAE roundtrip per picture, so these stay genuinely close to the source: subtle, coherent drift.
- **Phase 2 — pictures 6–10, chained.** Each output becomes the next input (true *model collapse*) with strength 0.22 → 0.42 and a per-step seed. VAE-roundtrip damage and hallucinations compound: the paint surface disintegrates and the figure falls apart with accelerating wrongness while the composition survives.

The 10 pictures map directly onto the gallery experience: the installation shows one picture every 3 seconds and measures which one breaks the visitor.

### Algorithm

```
load source image
query LLaVA once → description_prompt
seed = crc32(filename)                                  # stable per artwork

for i in 1..5:                                          # phase 1: direct
    strength_i = 0.10 + (0.30 − 0.10) · (i − 1) / 4
    picture_i  = SD_img2img(original 512×512, prompt, strength_i, seed)

current = picture_5
for i in 6..10:                                         # phase 2: chained
    strength_i = 0.22 + (0.42 − 0.22) · (i − 6) / 4
    picture_i  = SD_img2img(current, prompt, strength_i, seed + i)
    current    = picture_i

save original as 0000.png; pictures as <i:04d>.png      # guidance 6.0, steps 25
```

Full strength schedule: `0.10 · 0.15 · 0.20 · 0.25 · 0.30 │ 0.22 · 0.27 · 0.32 · 0.37 · 0.42` (the `│` marks the phase switch). The first pictures stay almost faithful — the visitor should not be jolted immediately — the collapse sets in at picture 6 and deepens to full disintegration by 10. This mirrors the uncanny-valley curve itself: a slow approach, then a plunge.

### Why two phases (findings from visual testing)

1. **A pure chain fails early.** Every img2img pass sends the image through SD's VAE (encode → latent → decode) plus a resize to 512×512. That roundtrip repaints fine texture *regardless of strength*; chained from picture 1, the damage compounds and the paint surface is mush by picture 5 — too much, too early.
2. **A pure direct ramp fails late.** Single passes at high strength re-cohere: instead of collapsing, picture 10 becomes a clean *different* painting. No disintegration character.
3. **Chain strength must stay low.** Chained passes above ~0.5 also re-cohere into a new scene. Keeping the chain at 0.22–0.42 lets roundtrip damage accumulate into painterly disintegration while the composition survives.
4. **Chain seeds must vary.** Re-injecting the *same* noise pattern into a feedback loop resonates and explodes into high-frequency artefacts within one step; per-step seeds (`seed + i`) produce organic collapse instead.

The hybrid keeps the best of both: pictures 1–5 genuinely sit next to the original (one roundtrip each), pictures 6–10 are true model collapse.

### Why this produces uncanny imagery

Stable Diffusion's training distribution has a strong prior on what a human looks like — symmetrical, smooth, proportions near the statistical mean. As its freedom grows, the model substitutes its prior for the painter's choices: features erode, asymmetries symmetrise, and details it cannot read (eyes, hands, fabric) are hallucinated back imperfectly. In the chained phase these errors become the next pass's ground truth and compound. The figure remains recognisably human while becoming deeply wrong — simultaneously over-familiar and foreign. That tension is the operating principle of the piece.

### Prompt generation (LLaVA)

Before the iteration loop, the source image is sent to a locally-running LLaVA instance (via Ollama) with the prompt:

> "Describe this artwork in under 30 words, focusing on the human figure, style, and medium. Write only the description, no preamble."

The response is used as the Stable Diffusion prompt for all 10 pictures, ensuring that each picture's drift is anchored to the original subject rather than drifting arbitrarily.

**Fallback**: if Ollama is not running, a generic prompt is used:
```
"a classical painting of a human figure, detailed, oil on canvas"
```

The quality difference between LLaVA-guided and generic prompts is meaningful for figurative paintings but negligible for sculpture photographs.

### Hardware requirements

| Device | Estimated runtime per image (10 iterations) |
|--------|---------------------------------------------|
| Apple M-series (MPS) | ~1 min |
| NVIDIA GPU (CUDA) | ~30 s |
| CPU only | ~10 min |

Device is detected automatically: MPS → CUDA → CPU.

The script is resumable: existing pictures are skipped; chained pictures reload their predecessor from disk. An artwork is considered complete when `0010.png` exists — delete its directory to force regeneration. Fixed seeds make reruns reproduce identical pictures.

### Model

`runwayml/stable-diffusion-v1-5` via Hugging Face `diffusers`. Downloaded automatically on first run (~4 GB). The model is cached in `~/.cache/huggingface/` and reused across runs.

---

## Output Format

```
uncanny_maker/
└── catalog_iterations_10/
    └── The_Dance_Class_438817/
        ├── 0000.png   ← source image (copy) — shown during BASELINE
        ├── 0001.png   ← direct, strength 0.10 (texture retouch)
        │   …
        ├── 0005.png   ← direct, strength 0.30 (drifting, still the painting)
        ├── 0006.png   ← chained, collapse sets in
        │   …
        └── 0010.png   ← chained, disintegrated
```

All frames are 512×512 px (Stable Diffusion native resolution). The gallery app upscales them to fit the display via CSS `object-fit: contain`.

The directory is excluded from version control (see `.gitignore`). The older 50/100-frame sets in `catalog_iterations/` are kept as an archive but are no longer read by the app.

---

## Configuration

All tunable parameters are in `uncanny_maker/config.py`:

| Parameter | Default | Effect |
|-----------|---------|--------|
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server address |
| `OLLAMA_MODEL` | `llava` | Vision LLM for prompt generation |
| `SD_MODEL_ID` | `runwayml/stable-diffusion-v1-5` | Diffusion base model |
| `DEFAULT_STRENGTH` | 0.55 | Per-iteration change magnitude |
| `DEFAULT_GUIDANCE` | 7.5 | Classifier-free guidance scale |
| `NEGATIVE_PROMPT` | `"cartoon, anime, ..."` | What to avoid in generation |

In `iterate_degrade.py` itself:

| Variable | Default | Effect |
|----------|---------|--------|
| `ITERATIONS` | 10 | Pictures per artwork |
| `DIRECT_COUNT` | 5 | Pictures generated directly from the original |
| `DIRECT_START` / `DIRECT_END` | 0.10 / 0.30 | Strength ramp of the direct phase |
| `CHAIN_START` / `CHAIN_END` | 0.22 / 0.42 | Strength ramp of the chained phase (higher values re-cohere into a different painting instead of collapsing) |
| `GUIDANCE` | 6.0 | Overrides `DEFAULT_GUIDANCE` |
| `STEPS` | 25 | Inference steps per picture (speed vs. quality) |

Reducing `STEPS` to 15 roughly halves runtime with only minor quality loss. If the early drift is too strong, lower `DIRECT_END`; if the collapse is too tame, raise `CHAIN_END` (stay below ~0.5). Test a single artwork first with `python test_single.py catalog/<image>.jpg`.

---

## Archive

`uncanny_maker/_archive/` contains earlier approaches that were superseded:

- **4-stage approach** (`catalog_uncanny/`): Only four fixed degradation levels (0 %, 20 %, 60 %, 80 % strength). Produced discontinuous jumps rather than a gradual descent. Still supported by `CatalogManager` as a fallback format.
- **Feedback-chain degradation** (`catalog_iterations/`, 50–100 frames): each output fed back as the next input — model collapse as a compositional tool. Visually compelling in the late frames but unusable early: compounding VAE-roundtrip damage repainted the texture from picture 1. Replaced by direct per-picture generation with a fixed seed.
