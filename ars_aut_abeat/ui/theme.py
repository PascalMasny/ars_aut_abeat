import streamlit as st

GOOGLE_FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Cinzel:wght@400;700;900&"
    "family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400;1,600&"
    "family=Pinyon+Script&"
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
    --burgundy-dark:  #3D1818;
    --gold:           #C9A961;
    --gold-bright:    #E8C87A;
    --gold-dark:      #8B6F2E;
    --sage:           #6B7B5E;
    --off-white:      #FAF5EC;
}}

html, body {{
    background-color: var(--ink-black) !important;
    color: var(--parchment) !important;
    font-family: 'Cormorant Garamond', serif !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    height: 100vh !important;
}}

/* Hide ALL Streamlit chrome */
#MainMenu, header, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"],
[data-testid="stHeader"] {{
    display: none !important;
}}

/* Nuke every layer of Streamlit padding. Backgrounds transparent so
   the fixed webrtc video can show through. */
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="stAppViewContainer"] > section > div,
[data-testid="stMain"] {{
    padding: 0 !important;
    margin: 0 !important;
    gap: 0 !important;
    max-width: 100vw !important;
    width: 100vw !important;
    background: transparent !important;
}}

/* Content column — transparent so the camera shows through */
[data-testid="stMainBlockContainer"],
[data-testid="block-container"] {{
    padding: 0 !important;
    margin: 0 auto !important;
    gap: 0 !important;
    max-width: 100vw !important;
    width: 100% !important;
    background: transparent !important;
}}

[data-testid="stVerticalBlock"],
[data-testid="stVerticalBlockBorderWrapper"] {{
    padding: 0 !important;
    margin: 0 !important;
    gap: 0 !important;
    width: 100% !important;
    background: transparent !important;
}}

/* ─── WebRTC camera — visible during setup, collapsed once camera is running.
   When `body.camera-running` is set by app.py, the component is hidden.       */
body.camera-running [data-testid="stCustomComponentV1"]:nth-of-type(1) {{
    width: 0 !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    position: absolute !important;
}}
/* Setup-state styling: pin the picker to bottom-center, frame it in gold */
body:not(.camera-running) [data-testid="stCustomComponentV1"]:nth-of-type(1) {{
    position: fixed !important;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%) !important;
    width: min(56rem, 92vw) !important;
    height: 88vh !important;
    z-index: 10002 !important;
    background: rgba(28,20,16,0.96) !important;
    border: 2px solid #C9A961 !important;
    border-radius: 6px !important;
    padding: 1.2rem !important;
    box-shadow: 0 0 40px rgba(201,169,97,0.35) !important;
    overflow: visible !important;
    display: flex !important;
    flex-direction: column !important;
}}
body:not(.camera-running) [data-testid="stCustomComponentV1"]:nth-of-type(1) > * {{
    flex: 1 1 auto !important;
    height: 100% !important;
    min-height: 0 !important;
}}
body:not(.camera-running) [data-testid="stCustomComponentV1"]:nth-of-type(1) iframe {{
    width: 100% !important;
    height: 100% !important;
    min-height: 560px !important;
    background: #0a0806 !important;
    display: block !important;
    border: 0 !important;
}}

/* ─── Overlay text on top of the video feed ─── */

/* Full-viewport overlay container for IDLE text */
.mirror-overlay {{
    position: fixed;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    width: min(100vw, calc(100vh * 112 / 199));
    height: 100vh;
    z-index: 10;
    pointer-events: none;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    align-items: center;
    padding: 2vh 1rem;
}}

/* Vignette over the full-screen video */
.mirror-overlay::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(ellipse at center,
        transparent 30%,
        rgba(28,20,16,0.35) 60%,
        rgba(28,20,16,0.85) 100%);
    pointer-events: none;
}}

/* Gilt frame border around the entire viewport */
.mirror-overlay::after {{
    content: '';
    position: absolute;
    top: 8px; left: 8px; right: 8px; bottom: 8px;
    border: 3px solid var(--gold);
    box-shadow:
        0 0 0 1px var(--gold-dark),
        inset 0 0 0 1px var(--gold-dark),
        0 0 30px rgba(201,169,97,0.15),
        inset 0 0 30px rgba(201,169,97,0.08);
    pointer-events: none;
}}

.mirror-overlay > * {{
    position: relative;
    z-index: 1;
}}

/* Top title area */
.mirror-top {{
    text-align: center;
    padding-top: 2vh;
}}

/* Bottom plaque area */
.mirror-bottom {{
    text-align: center;
    padding-bottom: 2vh;
}}

/* HOW IT WORKS — right sidebar on wide screens, stacked on narrow */
.howitworks-panel {{
    position: absolute;
    right: clamp(1rem, 3vw, 2.5rem);
    top: 50%;
    transform: translateY(-50%);
    width: min(30vw, 360px);
    min-width: 220px;
    padding: clamp(0.8rem, 1.6vw, 1.4rem) clamp(1rem, 2vw, 1.8rem);
    background: rgba(28,20,16,0.78);
    border: 2px solid rgba(201,169,97,0.4);
    border-radius: 8px;
    backdrop-filter: blur(6px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    pointer-events: none;
}}
.howitworks-title {{
    font-family: 'Cinzel', serif; font-weight: 700;
    font-size: clamp(0.85rem, 1.1vw, 1.15rem);
    letter-spacing: 0.18em;
    color: var(--gold);
    text-align: center;
    margin-bottom: 0.7rem;
}}
.howitworks-step {{
    font-family: 'Cormorant Garamond', serif;
    font-size: clamp(0.95rem, 1.1vw, 1.2rem);
    color: var(--parchment-dark);
    line-height: 1.5;
    margin: 0.3rem 0;
}}
.howitworks-step strong {{
    color: var(--gold-bright);
    font-weight: 700;
    margin-right: 0.4em;
}}

/* Narrow screens: inline the panel into the vertical flow */
@media (max-width: 820px) {{
    .howitworks-panel {{
        position: static;
        transform: none;
        width: min(92vw, 520px);
        margin: 1vh auto;
    }}
    .mirror-overlay {{
        justify-content: space-around;
        padding: 1.5vh 0.75rem;
    }}
    .mirror-top, .mirror-bottom {{
        padding: 0;
    }}
}}

/* Autorefresh component — tiny, hide it */
[data-testid="stCustomComponentV1"]:nth-of-type(2) {{
    height: 0 !important;
    overflow: hidden !important;
}}

/* Full-screen overlay for non-IDLE phases — 16:9 centered */
.gallery-overlay {{
    position: fixed !important;
    top: 0; left: 50%;
    transform: translateX(-50%);
    width: min(100vw, calc(100vh * 112 / 199));
    height: 100vh;
    background: var(--ink-black);
    z-index: 9999;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    padding: clamp(0.75rem, 2vw, 2rem);
    /* Black bars on sides if screen wider than 16:9 */
    box-shadow: -50vw 0 0 50vw var(--ink-black), 50vw 0 0 50vw var(--ink-black);
}}

/* ─── Live emotion bars overlaid on top of the morphing iframe ────────────── */
.morphing-emotion-overlay {{
    position: fixed;
    bottom: 0; left: 50%;
    transform: translateX(-50%);
    width: min(100vw, calc(100vh * 112 / 199));
    z-index: 10000;
    background: linear-gradient(transparent, rgba(28,20,16,0.88) 35%, rgba(28,20,16,0.97));
    /* Slimmer top padding so the bars sit closer to the bottom edge and the
       artwork (anchored toward the top of the frame) has more clear space. */
    padding: 1vh 6vw 2vh;
    pointer-events: none;
}}

/* ─── Morphing animation player — fullscreen iframe injected during MORPHING ─ */
[data-testid="stCustomComponentV1"]:nth-of-type(3) {{
    height: 0 !important;
    overflow: visible !important;
    position: relative !important;
}}
[data-testid="stCustomComponentV1"]:nth-of-type(3) iframe {{
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    border: none !important;
    z-index: 9999 !important;
}}

/* VIEWING split: artwork + emotions side-by-side on wide, stacked on narrow */
.viewing-split {{
    display: flex;
    gap: clamp(1rem, 4vw, 4rem);
    align-items: center;
    justify-content: center;
    width: 100%;
    flex: 1;
    min-height: 0;
}}
.viewing-art {{ flex: 1.2; max-width: 55%; }}
.viewing-emotions {{ flex: 0.8; max-width: 38%; }}

@media (max-width: 820px), (orientation: portrait) {{
    .viewing-split {{
        flex-direction: column;
        gap: 1rem;
        overflow: auto;
    }}
    .viewing-art, .viewing-emotions {{
        max-width: 95%;
        width: 100%;
        flex: none;
    }}
}}

/* Emotion overlay — gradient panel at bottom of artwork */
.emotion-overlay-panel {{
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(transparent, rgba(28,20,16,0.88) 30%, rgba(28,20,16,0.95));
    padding: clamp(0.6rem,1.5vh,1.2rem) clamp(0.8rem,2vw,1.5rem);
    z-index: 2;
}}

/* Responsive wax seal */
.seal-medallion {{
    width: clamp(90px, 14vw, 160px);
    height: clamp(90px, 14vw, 160px);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-family: 'Cinzel', serif; font-weight: 900;
    font-size: clamp(0.9rem, 1.6vw, 1.6rem);
    letter-spacing: 0.06em;
    transform: rotate(-6deg);
    box-shadow: 0 6px 24px rgba(0,0,0,0.5);
}}

.gallery-root {{
    width: 100vw;
    height: 100vh;
    background: var(--ink-black);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    position: fixed;
    top: 0;
    left: 0;
    overflow: hidden;
}}

/* --- Typography --- */
.title-cinzel {{
    font-family: 'Cinzel', serif;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--gold);
}}

.body-garamond {{
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.2rem;
    color: var(--parchment);
    line-height: 1.7;
}}

.script-pinyon {{
    font-family: 'Pinyon Script', cursive;
    color: var(--gold-bright);
}}

/* --- Gilded frame --- */
.gilded-frame {{
    border: 4px solid var(--gold);
    box-shadow:
        0 0 0 2px var(--gold-dark),
        0 0 0 8px var(--ink-black),
        0 0 0 10px var(--gold),
        0 0 30px rgba(201,169,97,0.3);
    padding: 8px;
    position: relative;
    background: var(--ink-black);
}}

/* --- Parchment scroll --- */
.parchment-scroll {{
    background: var(--parchment);
    color: var(--ink-black);
    border-radius: 4px;
    padding: 1.2rem 1.8rem;
    box-shadow:
        inset 0 0 40px rgba(0,0,0,0.2),
        0 8px 32px rgba(0,0,0,0.6);
    font-family: 'Cormorant Garamond', serif;
    animation: unfurl 0.6s ease-out;
    position: relative;
}}

.parchment-scroll::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='300' height='300' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
    pointer-events: none;
    border-radius: 4px;
}}

@keyframes unfurl {{
    from {{ opacity: 0; transform: translateY(-12px) scaleY(0.96); }}
    to   {{ opacity: 1; transform: translateY(0) scaleY(1); }}
}}

/* --- Wax seal --- */
.wax-seal {{
    width: 120px;
    height: 120px;
    border-radius: 50%;
    background: radial-gradient(circle at 40% 35%, #8B2222, var(--burgundy-dark));
    border: 3px solid var(--gold);
    box-shadow: 0 4px 16px rgba(0,0,0,0.5), inset 0 2px 8px rgba(0,0,0,0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Cinzel', serif;
    font-weight: 900;
    font-size: 1.1rem;
    letter-spacing: 0.08em;
    color: var(--gold-bright);
    text-shadow: 0 1px 3px rgba(0,0,0,0.5);
    transform: rotate(-6deg);
    animation: stamp 0.4s cubic-bezier(0.36, 0.07, 0.19, 0.97);
}}

@keyframes stamp {{
    0%   {{ transform: rotate(-6deg) scale(1.3); opacity: 0.6; }}
    60%  {{ transform: rotate(-6deg) scale(0.95); }}
    80%  {{ transform: rotate(-6deg) scale(1.02); }}
    100% {{ transform: rotate(-6deg) scale(1); opacity: 1; }}
}}

/* --- Filigree divider --- */
.filigree {{
    text-align: center;
    color: var(--gold);
    font-size: 1.1rem;
    letter-spacing: 0.3em;
    margin: 0.4rem 0;
    opacity: 0.7;
}}

/* --- Vignette overlay --- */
.vignette {{
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(ellipse at center,
        transparent 40%,
        rgba(28,20,16,0.6) 70%,
        rgba(28,20,16,0.95) 100%
    );
    pointer-events: none;
    z-index: 2;
}}

/* --- Fade transitions --- */
.fade-in {{
    animation: fadeIn 0.8s ease-out;
}}

@keyframes fadeIn {{
    from {{ opacity: 0; }}
    to   {{ opacity: 1; }}
}}

.slide-up {{
    animation: slideUp 0.6s ease-out;
}}

@keyframes slideUp {{
    from {{ opacity: 0; transform: translateY(20px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}

/* --- Emotion bar --- */
.emotion-bar-container {{
    margin: 0.3rem 0;
}}

.emotion-bar-label {{
    font-family: 'Cinzel', serif;
    font-size: 0.75rem;
    letter-spacing: 0.08em;
    color: var(--gold-dark);
    display: flex;
    justify-content: space-between;
    margin-bottom: 2px;
}}

.emotion-bar-track {{
    height: 6px;
    background: rgba(201,169,97,0.15);
    border-radius: 3px;
    overflow: hidden;
}}

.emotion-bar-fill {{
    height: 100%;
    background: linear-gradient(90deg, var(--gold-dark), var(--gold-bright));
    border-radius: 3px;
    transition: width 0.3s ease;
}}

/* --- Countdown --- */
.roman-countdown {{
    font-family: 'Cinzel', serif;
    font-size: 4rem;
    font-weight: 900;
    color: var(--gold);
    text-align: center;
    text-shadow: 0 0 30px rgba(201,169,97,0.5);
    animation: pulse 1s ease-in-out infinite;
}}

@keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.7; }}
}}

/* --- Medallion --- */
.medallion-ring {{
    border: 3px solid var(--gold);
    border-radius: 50%;
    padding: 1rem 2rem;
    display: inline-block;
    box-shadow: 0 0 20px rgba(201,169,97,0.4);
    animation: medalAppear 0.5s ease-out;
}}

@keyframes medalAppear {{
    from {{ transform: scale(0.8); opacity: 0; }}
    to   {{ transform: scale(1); opacity: 1; }}
}}

/* --- Artwork image --- */
.artwork-container {{
    animation: artReveal 1.2s ease-out;
}}

@keyframes artReveal {{
    from {{ opacity: 0; transform: scale(0.98); }}
    to   {{ opacity: 1; transform: scale(1); }}
}}

/* --- Stars --- */
.stars {{
    color: var(--gold);
    font-size: 1.4rem;
    letter-spacing: 0.1em;
}}

/* ── Attract screen ─────────────────────────────────────────────────────────
   Slides in from below, same 16:9 centred viewport as .gallery-overlay.
   Python controls visibility by rendering one block vs the other — the CSS
   animation fires automatically on mount (no JS needed).                    */
.attract-overlay {{
    position: fixed !important;
    top: 0; left: 50%;
    transform: translateX(-50%);
    width: min(100vw, calc(100vh * 112 / 199));
    height: 100vh;
    background: var(--ink-black);
    z-index: 9999;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    padding: clamp(1rem, 2.5vw, 2.5rem) clamp(1.5rem, 4vw, 4rem);
    box-shadow: -50vw 0 0 50vw var(--ink-black), 50vw 0 0 50vw var(--ink-black);
    animation: attractSlideIn 0.65s cubic-bezier(0.22, 0.61, 0.36, 1) both;
}}

.attract-overlay::after {{
    content: '';
    position: absolute;
    top: 8px; left: 8px; right: 8px; bottom: 8px;
    border: 3px solid var(--gold);
    box-shadow:
        0 0 0 1px var(--gold-dark),
        inset 0 0 0 1px var(--gold-dark),
        0 0 40px rgba(201,169,97,0.18),
        inset 0 0 40px rgba(201,169,97,0.06);
    pointer-events: none;
}}

@keyframes attractSlideIn {{
    from {{ opacity: 0; transform: translateX(-50%) translateY(44px); }}
    to   {{ opacity: 1; transform: translateX(-50%) translateY(0);    }}
}}

.attract-soul-counter {{
    font-family: 'Cinzel', serif;
    font-weight: 900;
    font-size: clamp(1.6rem, 4.5vw, 4rem);
    letter-spacing: 0.18em;
    color: var(--gold);
    text-align: center;
    text-shadow: 0 0 40px rgba(201,169,97,0.45);
    margin: 0.5rem 0;
    animation: soulPulse 3s ease-in-out infinite;
}}

@keyframes soulPulse {{
    0%, 100% {{ opacity: 1;    text-shadow: 0 0 40px rgba(201,169,97,0.45); }}
    50%       {{ opacity: 0.75; text-shadow: 0 0 80px rgba(201,169,97,0.25); }}
}}

</style>
""".format(fonts=GOOGLE_FONTS_URL)


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)
