import streamlit as st

GOOGLE_FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Cinzel:wght@400;700;900&"
    "family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400;1,600&"
    "display=swap"
)

CSS = """
<style>
@import url('{fonts}');

:root {{
    --ink-black:      #1C1410;
    --parchment:      #F4E8D0;
    --parchment-dark: #E0D0B0;
    --burgundy:       #6B2C2C;
    --gold:           #C9A961;
    --gold-bright:    #E8C87A;
    --gold-dark:      #8B6F2E;
}}

html, body {{
    background-color: var(--ink-black) !important;
    color: var(--parchment) !important;
    font-family: 'Cormorant Garamond', serif !important;
}}

h1, h2, h3 {{
    font-family: 'Cinzel', serif !important;
    color: var(--gold) !important;
    letter-spacing: 0.08em;
}}

[data-testid="stApp"] {{
    background-color: var(--ink-black) !important;
}}

[data-testid="stMainBlockContainer"] {{
    max-width: 1100px;
    padding: 2rem 2rem 4rem;
}}

/* Baroque gold divider */
hr {{
    border: none;
    border-top: 1px solid var(--gold-dark);
    margin: 1.5rem 0;
}}

/* Image frames */
.uncanny-frame {{
    border: 3px solid var(--gold);
    box-shadow:
        0 0 0 1px var(--gold-dark),
        0 0 20px rgba(201,169,97,0.2);
    border-radius: 2px;
}}

/* Prompt display box */
.prompt-box {{
    background: rgba(201,169,97,0.08);
    border: 1px solid var(--gold-dark);
    border-radius: 4px;
    padding: 0.75rem 1rem;
    font-style: italic;
    color: var(--parchment-dark);
    font-size: 0.95rem;
    margin: 0.5rem 0;
}}

/* Streamlit buttons */
[data-testid="stButton"] > button {{
    background: var(--burgundy) !important;
    color: var(--parchment) !important;
    border: 1px solid var(--gold-dark) !important;
    font-family: 'Cinzel', serif !important;
    letter-spacing: 0.1em;
    font-size: 0.85rem;
    padding: 0.5rem 1.5rem;
    border-radius: 2px;
}}
[data-testid="stButton"] > button:hover {{
    background: #8B3A3A !important;
    border-color: var(--gold) !important;
}}

/* Slider */
[data-testid="stSlider"] label {{
    color: var(--parchment) !important;
    font-family: 'Cormorant Garamond', serif !important;
}}

/* File uploader */
[data-testid="stFileUploader"] {{
    border: 1px dashed var(--gold-dark) !important;
    border-radius: 4px;
    background: rgba(201,169,97,0.04) !important;
}}

/* Hide Streamlit header/footer */
#MainMenu, header, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"] {{
    display: none !important;
}}
</style>
"""


@st.cache_data(show_spinner=False)
def _css() -> str:
    return CSS.format(fonts=GOOGLE_FONTS_URL)


def inject():
    st.markdown(_css(), unsafe_allow_html=True)
