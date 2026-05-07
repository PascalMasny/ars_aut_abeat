import torch
from PIL import Image
from config import SD_MODEL_ID, DEFAULT_GUIDANCE, NEGATIVE_PROMPT


def _device() -> str:
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def load_pipeline():
    from diffusers import StableDiffusionImg2ImgPipeline

    device = _device()
    dtype = torch.float16 if device in ("mps", "cuda") else torch.float32
    pipe = StableDiffusionImg2ImgPipeline.from_pretrained(SD_MODEL_ID, torch_dtype=dtype)
    pipe = pipe.to(device)
    pipe.safety_checker = None

    # MPS / unified-memory optimisations
    pipe.enable_attention_slicing(1)
    try:
        pipe.enable_vae_slicing()
    except AttributeError:
        pass

    return pipe


def run_img2img(image: Image.Image, prompt: str, strength: float) -> Image.Image:
    pipe = load_pipeline()
    original_size = image.size
    working = image.convert("RGB").resize((512, 512), Image.LANCZOS)
    result = pipe(
        prompt=prompt,
        image=working,
        strength=strength,
        guidance_scale=DEFAULT_GUIDANCE,
        negative_prompt=NEGATIVE_PROMPT,
        num_inference_steps=30,
    ).images[0]
    return result.resize(original_size, Image.LANCZOS)
