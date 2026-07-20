# How to run the installation at an exhibition

Get from a cold machine to a running installation, present it to an audience, and
recover from the failures that actually happen on site.

## Prerequisites

- The catalog is on disk. Verify: `find uncanny_maker/catalog_iterations_10 -name '0010.png' | wc -l` returns a non-zero count. If it returns 0, see [`HOWTO_REGENERATE_CATALOG.md`](HOWTO_REGENERATE_CATALOG.md) — that is a ~3 hour job, not a same-morning fix.
- `./install.sh` has been run once on this machine (Ubuntu) or `pip install -r requirements.txt` plus `npm install` (macOS).
- Camera connected, display connected, machine on mains power.

## Steps

### 1. Start it

```bash
cd ars_aut_abeat
./start.sh
```

This builds the frontend if `frontend/dist/` is missing, starts uvicorn on
`0.0.0.0:8000`, waits for the server to answer, then opens Brave (falling back to
Chrome, then Chromium) in kiosk mode.

Force a rebuild after any frontend edit — `start.sh` skips the build when `dist/`
already exists, so an edited component will otherwise not appear:

```bash
./start.sh --build
```

Other flags: `--port 9000`, `--no-browser` (server only).

### 2. Wait for the models

MediaPipe downloads two `.task` files (~20 MB each) into the system temp dir on
first run per machine. The page loads immediately but face detection stays dead
for 10–30 s. **Wait for the emotion bars to move before letting a visitor near
it.** Subsequent starts reuse the cached files and are instant.

Confirm readiness: stand in front of the camera in IDLE, raise both hands, and
check that the hands-raised prompt reacts.

### 3. Choose the interaction mode

Top-right of the screen:

| Control | Effect |
|---------|--------|
| `◎ SELF` / `◉ SHOW` | Toggles `POST /api/mode`. **SELF** = visitors trigger by raising both hands for 1.5 s. **SHOW** = the hands trigger is disabled and only the presenter can start a run. |
| `◎ SLIDES` / `◉ SLIDES` | Opens the in-app German presentation deck, auto-advancing every 10 s. |

In **SHOW** mode press **Space** or **Enter** to start a run (ignored unless the
phase is IDLE and the slides overlay is closed). This is the mode to use when
presenting to a seated audience — it stops the piece from firing every time
someone in the room stretches.

### 4. Run it

Once triggered the sequence is fully automatic and takes **74 seconds**:
BASELINE 19 s → GALLERY 30 s → REVEAL 25 s → back to IDLE.

There is no abort control. To cut a run short, reload the page — but note the
state machine is a server-side singleton, so a reload does **not** reset it; the
run continues from wherever it is. Restart the server to force IDLE.

## Verification

A healthy installation, checked in IDLE:

- Mirror view of the room is visible and moving
- The attract screen (donut chart + emotion bars) appears for 15 s of every 30 s cycle
- Raising both hands shows the trigger prompt, and the run starts after 1.5 s
- During GALLERY the emotion bars on the right move as expressions change
- REVEAL shows three pictures and a reaction curve, not a blank panel

```bash
curl -s localhost:8000/api/trigger -X POST    # {"triggered":false} in SELF mode — expected
```

## Troubleshooting

**Screen is black / "no artwork"; nothing happens on hands raised**
`CatalogManager` loaded zero artworks, so `pick_next()` returns `None` and the
state machine cannot leave IDLE. It requires *both* `uncanny_maker/catalog/{stem}.jpg`
and `catalog_iterations_10/{stem}/0010.png`. Check both directories are non-empty
and restart.

**Pictures 404, artwork title shows correctly**
`/frames` is mounted at import time only if `catalog_iterations_10/` exists.
If the pictures arrived after the server started, restart the server.

**Emotion bars stay flat at zero**
Emotion sampling is enabled only during BASELINE and GALLERY (`set_emotion_sampling`
in `ws_handler.py`) — flat bars in IDLE are correct. If they stay flat during
GALLERY, the FaceLandmarker model failed to download; check network and restart.

**Hands-raised trigger fires constantly**
PoseLandmarker sees a bystander. Pose sampling runs only in IDLE, and the trigger
needs both wrists above their respective shoulders held for 1.5 s. Switch to SHOW
mode for presentations.

**Hands-raised never fires**
Both wrists must be above the shoulders and visible in a 640×480 frame. Step back
so the torso is in shot. A 0.4 s grace period covers brief dropouts, but a wrist
leaving the frame for longer resets the timer.

**Everyone gets ARS MANSIT / FIRMA**
Max deviation never reached `BREAKING_MIN_DEVIATION` (0.08) — usually poor lighting
flattening the blendshape signal, or the visitor's face partly out of frame. Light
the face frontally. Do not lower the threshold to manufacture results.

**Page went blank mid-run**
The WebSocket auto-reconnects after 2 s and the singleton state means the run
resumes mid-session rather than restarting. Wait rather than reloading.

**Browser did not open**
`start.sh` prints the URL. Open `http://localhost:8000` manually, then `F11` for
fullscreen. On Wayland the script already forces `--ozone-platform=x11`.

## A note on display orientation

`start.sh`'s header comment describes a *vertically mounted 65-inch display
(portrait)*, while the frontend renders a **16:9 landscape** viewport, letterboxed
on non-16:9 screens (see `App.css`). The frontend is authoritative — plan for
landscape. The comment is stale.

## Privacy posture for a public exhibition

Worth being able to state plainly if a visitor asks:

- No video is written to disk at any point; frames live in memory and are overwritten.
- All analysis runs locally on the installation machine; nothing leaves it.
- The database stores anonymous numbers only — a UUID per visit, averaged emotion
  probabilities, verdict, breaking index. No images, no identity.
- Raising both hands is a deliberate opt-in gesture.

Note that the camera is analysing continuously in IDLE for the hands gesture even
before anyone opts in. Nothing is recorded or stored, but signage should say the
camera is on.

## Related

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — state machine, protocol, scoring
- [`HOWTO_REGENERATE_CATALOG.md`](HOWTO_REGENERATE_CATALOG.md) — rebuilding the images
- [`CONCEPT.md`](CONCEPT.md) — what to say about the piece
