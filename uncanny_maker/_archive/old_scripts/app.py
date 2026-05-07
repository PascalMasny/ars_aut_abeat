import io
import sys
import os

# Allow imports from this directory
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from PIL import Image

from config import DEFAULT_STRENGTH
from ui.theme import inject

st.set_page_config(
    page_title="Uncanny Maker",
    page_icon="⚗",
    layout="centered",
)
inject()

st.title("Uncanny Maker")
st.markdown(
    "<p style='color:#C9A961;font-style:italic;'>Upload portraits. Let the oracle render them unsettling.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# ── Upload ────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Upload images",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if not uploaded:
    st.markdown(
        "<p style='color:#8B6F2E;text-align:center;padding:2rem;'>"
        "No images uploaded yet. Drag files above to begin."
        "</p>",
        unsafe_allow_html=True,
    )
    st.stop()

# ── Thumbnail strip ───────────────────────────────────────────────────────────
st.markdown("**Select an image:**")
names = [f.name for f in uploaded]

if "selected_idx" not in st.session_state:
    st.session_state.selected_idx = 0

cols = st.columns(min(len(uploaded), 6))
for i, (col, uf) in enumerate(zip(cols, uploaded)):
    with col:
        thumb = Image.open(uf).convert("RGB")
        thumb.thumbnail((120, 120))
        st.image(thumb, use_container_width=True)
        if st.button(f"{'▶ ' if i == st.session_state.selected_idx else ''}{uf.name[:12]}", key=f"sel_{i}"):
            st.session_state.selected_idx = i
            st.session_state.pop("result_image", None)
            st.session_state.pop("used_prompt", None)
            st.rerun()

st.markdown("---")

# ── Main work area ────────────────────────────────────────────────────────────
idx = st.session_state.selected_idx
selected_file = uploaded[idx]
selected_file.seek(0)
image_bytes = selected_file.read()
original = Image.open(io.BytesIO(image_bytes)).convert("RGB")

col_orig, col_result = st.columns(2)

with col_orig:
    st.markdown("**Original**")
    st.image(original, use_container_width=True)

with col_result:
    st.markdown("**Uncanny**")
    if "result_image" in st.session_state:
        st.image(st.session_state.result_image, use_container_width=True)
        if "used_prompt" in st.session_state:
            st.markdown(
                f"<div class='prompt-box'>{st.session_state.used_prompt}</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            "<div style='height:200px;display:flex;align-items:center;"
            "justify-content:center;border:1px dashed #8B6F2E;color:#8B6F2E;"
            "font-style:italic;border-radius:2px;'>"
            "awaiting transformation"
            "</div>",
            unsafe_allow_html=True,
        )

st.markdown("---")

# ── Controls ──────────────────────────────────────────────────────────────────
strength = st.slider(
    "Transformation strength",
    min_value=0.30,
    max_value=0.80,
    value=DEFAULT_STRENGTH,
    step=0.05,
    help="Higher = more uncanny, further from the original.",
)

if st.button("⚗ Make Uncanny"):
    try:
        with st.spinner("Consulting the oracle (LLaVA)…"):
            from core.llm import analyze_and_prompt
            prompt = analyze_and_prompt(image_bytes)

        st.toast(f"Prompt: {prompt}", icon="🔮")

        with st.spinner("Transforming (Stable Diffusion)…"):
            from core.transform import run_img2img
            result = run_img2img(original, prompt, strength)

        st.session_state.result_image = result
        st.session_state.used_prompt = prompt
        st.rerun()

    except RuntimeError as e:
        st.error(str(e))

# ── Download ──────────────────────────────────────────────────────────────────
if "result_image" in st.session_state:
    buf = io.BytesIO()
    st.session_state.result_image.save(buf, format="PNG")
    st.download_button(
        label="Download result",
        data=buf.getvalue(),
        file_name=f"uncanny_{selected_file.name.rsplit('.', 1)[0]}.png",
        mime="image/png",
    )
