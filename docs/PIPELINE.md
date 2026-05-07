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
         │  Stable Diffusion img2img × 100 iterations
         ▼
  catalog_iterations/<stem>/0000.png … 0100.png
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

`iterate_degrade.py` takes each source image and runs it through 100 rounds of Stable Diffusion img2img. Each round feeds the *output* of the previous round back as the *input*, so distortion compounds like a visual game of telephone.

### Algorithm

```
load source image
query LLaVA once → description_prompt
frame_0 = source image

for i in 1..100:
    frame_i = SD_img2img(
        init_image = frame_{i-1},
        prompt     = description_prompt,
        strength   = 0.45,
        guidance   = 6.0,
        steps      = 25,
    )
    save frame_i as catalog_iterations/<stem>/<i:04d>.png

save source as 0000.png
```

The `strength` parameter (0.45) controls how aggressively each iteration changes the image. At 0.45 each frame drifts slightly; over 100 iterations the cumulative drift produces pronounced uncanny distortion while preserving enough of the original composition to remain recognisable.

### Why this produces uncanny imagery

Stable Diffusion learns a statistical model of *plausible* images. When iterated with a human-figure prompt, it repeatedly nudges the image toward the average human face in its training distribution — smoothing individual features, symmetrising asymmetries, and homogenising texture. The result is a face that is recognisably human but subtly wrong: too smooth, too symmetrical, proportions slightly off. These are precisely the attributes that trigger uncanny valley responses in viewers.

### Prompt generation (LLaVA)

Before the iteration loop, the source image is sent to a locally-running LLaVA instance (via Ollama) with the prompt:

> "Describe this artwork in under 30 words, focusing on the human figure, style, and medium. Write only the description, no preamble."

The response is used as the Stable Diffusion prompt for all 100 iterations, ensuring that each frame's drift is anchored to the original subject rather than drifting arbitrarily.

**Fallback**: if Ollama is not running, a generic prompt is used:
```
"a classical painting of a human figure, detailed, oil on canvas"
```

The quality difference between LLaVA-guided and generic prompts is meaningful for figurative paintings but negligible for sculpture photographs.

### Hardware requirements

| Device | Estimated runtime per image |
|--------|-----------------------------|
| Apple M-series (MPS) | ~8–12 min |
| NVIDIA GPU (CUDA) | ~3–6 min |
| CPU only | ~60–120 min |

Device is detected automatically: MPS → CUDA → CPU.

The script is resumable: frames that already exist on disk are skipped. A partial run (e.g. frames 0000–0047) will continue from frame 0048 on the next invocation.

### Model

`runwayml/stable-diffusion-v1-5` via Hugging Face `diffusers`. Downloaded automatically on first run (~4 GB). The model is cached in `~/.cache/huggingface/` and reused across runs.

---

## Output Format

```
uncanny_maker/
└── catalog_iterations/
    └── The_Dance_Class_438817/
        ├── 0000.png   ← source image (copy)
        ├── 0001.png   ← after 1 iteration
        ├── 0002.png
        │   …
        └── 0100.png   ← after 100 iterations
```

All frames are 512×512 px (Stable Diffusion native resolution). The gallery app upscales them to fit the display via CSS `object-fit: contain`.

The `catalog_iterations/` directory is excluded from version control (see `.gitignore`) because the full sequence set can exceed 10 GB.

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
| `ITERATIONS` | 100 | Number of feedback loops per image |
| `STRENGTH` | 0.45 | Overrides `DEFAULT_STRENGTH` |
| `GUIDANCE` | 6.0 | Overrides `DEFAULT_GUIDANCE` |
| `STEPS` | 25 | Inference steps per iteration (speed vs. quality) |

Reducing `STEPS` to 15 roughly halves runtime with only minor quality loss. Increasing `STRENGTH` above 0.6 tends to collapse the image into noise within ~30 iterations.

---

## Archive

`uncanny_maker/_archive/` contains earlier approaches that were superseded:

- **4-stage approach** (`catalog_uncanny/`): Only four fixed degradation levels (0 %, 20 %, 60 %, 80 % strength). Produced discontinuous jumps rather than smooth morphing. Still supported by `CatalogManager` as a fallback format.
- **Single-pass degradation**: No iterative feedback, just one img2img pass at increasing strength. Produced monotonic noise rather than uncanny accumulation.
