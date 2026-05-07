# Vallis Simulacri
### *The Valley of Likeness* — An Interactive Gallery Installation

> *At what point does a human find their own species wrong?*

**Vallis Simulacri** takes classical paintings and sculptures of the human figure and feeds them into an AI — then feeds the output back in again, one hundred times. Each cycle the image drifts further from the original. Features smooth. Proportions shift. Something that was familiar becomes wrong.

The visitor watches this happen. Their face is read throughout, silently, at ten frames per second. The micro-expressions they cannot control — the involuntary flickers of disgust and fear — are recorded and scored. At the end, a verdict is rendered.

The installation is not about AI. It is about the human nervous system: its extraordinary sensitivity to the human body, and the precise moment that sensitivity becomes alarm. The AI is just the instrument. The subject is *you*.

See [`docs/CONCEPT.md`](docs/CONCEPT.md) for the full philosophical framing.

---

Visitors stand before a screen showing a classical artwork. By raising both hands they initiate a 30-second session: the image morphs through AI-driven distortion while MediaPipe facial analysis silently records their emotional response at 10 Hz. At the end a wax-seal verdict in Latin is rendered:

| Verdict | Latin meaning | Score |
|---------|--------------|-------|
| **VALLIS** | *The valley* — deep uncanny reaction | ≥ 0.60 |
| **LIMEN** | *The threshold* — ambivalent response | 0.40 – 0.60 |
| **FIRMA** | *Solid ground* — no significant reaction | < 0.40 |

The installation runs autonomously on a looped kiosk, collects anonymous viewing data, and builds a crowd-level record of collective response for each artwork in the catalog.

---

## Repository Structure

```
.
├── ars_aut_abeat/          Interactive gallery application (Streamlit + WebRTC)
│   ├── app.py              Entrypoint — state machine driver and UI renderer
│   ├── config.py           All tunable parameters (timings, thresholds, weights)
│   ├── core/               State machine, session model, verdict scoring
│   ├── vision/             MediaPipe emotion detection and gaze analysis
│   ├── data/               SQLAlchemy ORM, SQLite persistence, analytics
│   ├── catalog/            Artwork loader — maps source images to frame sequences
│   ├── ui/                 CSS theme (parchment, gilded frames, wax seals)
│   └── tests/              Unit tests for scoring and gaze thresholds
│
├── uncanny_maker/          Offline preprocessing pipeline
│   ├── iterate_degrade.py  Main script — 100-frame iterative AI degradation
│   ├── download_human_figures.py  Met Museum API scraper (~200 artworks)
│   ├── core/               Stable Diffusion img2img + LLaVA prompt generation
│   └── catalog/            Source artwork images (downloaded by scraper)
│
├── _prototypes/            Early experiments (not production)
└── docs/                   Extended technical documentation
    ├── ARCHITECTURE.md     System architecture and design decisions
    └── PIPELINE.md         Preprocessing pipeline — how degradation works
```

---

## Quick Start

### Gallery Application

```bash
cd ars_aut_abeat
pip install -r requirements.txt

# macOS only — fix SSL certificates for MediaPipe model download
/Applications/Python\ 3.x/Install\ Certificates.command

streamlit run app.py
# → http://localhost:8501
```

On first launch MediaPipe downloads two model files (~300 MB total). After that the app is fully offline.

Developer overlay (camera debug + manual frame scrubber):
```
http://localhost:8501/?dev=1
```

### Preprocessing Pipeline

Run once before the first installation session to build the artwork catalog and generate degradation sequences.

```bash
cd uncanny_maker
pip install -r requirements.txt

# Step 1 — download source artworks from Met Museum Open Access
python download_human_figures.py

# Step 2 — generate 100-frame degradation sequences with Stable Diffusion
#           Ollama + LLaVA is optional; falls back to a generic prompt automatically
ollama serve  # optional, in a separate terminal
python iterate_degrade.py
```

Both scripts are fully resumable — interrupted runs continue from where they stopped.

---

## How the Interaction Works

```
 IDLE          Kiosk mirror view; waits for a visitor
   │
   │  both hands raised ≥ 1.5 s
   ▼
 LOCKED        "SPECTATOR IDENTIFIED" — artwork title revealed (2.5 s)
   │
   ▼
 MORPHING      Image degrades through 100 AI-generated frames (30 s)
               Emotions sampled at 10 Hz via MediaPipe blendshapes
   │
   ▼
 RECAP         Verdict seal + emotion timeline + crowd concordance (15 s)
   │
   ▼
 FADE          "THE VALLEY AWAITS THE NEXT SOUL" (3 s) → IDLE
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| UI framework | Streamlit + streamlit-webrtc |
| Computer vision | MediaPipe FaceLandmarker (52 FACS blendshapes) + PoseLandmarker |
| Head pose | OpenCV `solvePnP` |
| Image generation | Stable Diffusion v1.5 via Hugging Face `diffusers` |
| Vision LLM | LLaVA via Ollama (optional) |
| Database | SQLite via SQLAlchemy 2.0 |
| Art source | Met Museum Open Access API |

---

## Documentation

- [`docs/CONCEPT.md`](docs/CONCEPT.md) — Philosophy, core idea, and what the installation sets out to achieve
- [`ars_aut_abeat/README.md`](ars_aut_abeat/README.md) — Full gallery app reference (architecture, config, installation, DB schema)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — System design, threading model, emotion scoring
- [`docs/PIPELINE.md`](docs/PIPELINE.md) — Preprocessing pipeline, degradation algorithm, LLaVA integration

---

## Design Language

The visual identity is deliberately anachronistic: a 21st-century computer vision experiment dressed in the aesthetic of a 17th-century cabinet of curiosities.

- **Typography**: Cinzel (inscriptions), Cormorant Garamond (body), Pinyon Script (flourishes)
- **Palette**: Ink black `#1C1410` · Parchment `#F4E8D0` · Gold `#C9A961` · Burgundy `#6B2C2C`
- **Motifs**: Gilded frames, wax seals, filigree dividers, parchment scroll textures
- **Layout**: 16:9 centered; all text sizes scale from phone to beamer via CSS `clamp()`
