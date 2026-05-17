import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import type { ServerState } from '../hooks/useWebSocket'

interface Props {
  state: ServerState
}

const EMOTION_ORDER = ['happy', 'sad', 'angry', 'surprise', 'fear', 'disgust', 'neutral']
const EMOTION_LATIN: Record<string, string> = {
  happy: 'Happy', sad: 'Sad', angry: 'Angry',
  surprise: 'Surprise', fear: 'Fear', disgust: 'Disgust', neutral: 'Neutral',
}

export function MorphingPhase({ state }: Props) {
  const { artwork, emotions, phase_started_at, phase_duration } = state
  const rafRef = useRef<number | null>(null)
  const imgARef = useRef<HTMLImageElement | null>(null)
  const imgBRef = useRef<HTMLImageElement | null>(null)
  const [frameLabel, setFrameLabel] = useState('FRAME 000')
  const [progress, setProgress] = useState(0)

  const totalFrames = artwork?.total_frames ?? 100
  const slug = artwork?.slug ?? ''

  // Pin frame 0 synchronously before first paint — eliminates the one-frame
  // gap where imgA has no src and the camera would show through.
  useLayoutEffect(() => {
    if (!slug || !imgARef.current) return
    imgARef.current.src = `/frames/${slug}/0000.png`
  }, [slug])

  // rAF crossfade loop — driven by wall-clock time anchored to phase_started_at.
  useEffect(() => {
    if (!slug) return

    let curIdx = -1
    let nextIdx = -1

    // Piecewise easing: frames 0–5 (original → first AI distortions) occupy
    // the first 50% of total duration (~15 s each frame ≈ 3 s visible).
    // Frames 5–100 race through the remaining 50% so the full degradation arc
    // is seen without the end feeling rushed.
    const SLOW_FRAMES = 5
    const SLOW_SPLIT  = 0.50

    const tick = () => {
      const elapsed = Date.now() / 1000 - phase_started_at
      const p = Math.min(elapsed / phase_duration, 1.0)
      const raw =
        p < SLOW_SPLIT
          ? (p / SLOW_SPLIT) * SLOW_FRAMES
          : SLOW_FRAMES + ((p - SLOW_SPLIT) / (1 - SLOW_SPLIT)) * (totalFrames - SLOW_FRAMES)
      const ci = Math.min(Math.floor(raw), totalFrames)
      const ni = Math.min(ci + 1, totalFrames)
      const blend = raw - Math.floor(raw)

      const imgA = imgARef.current
      const imgB = imgBRef.current
      if (!imgA || !imgB) return

      if (ci !== curIdx) {
        curIdx = ci
        imgA.src = `/frames/${slug}/${String(ci).padStart(4, '0')}.png`
      }
      if (ni !== nextIdx) {
        nextIdx = ni
        imgB.src = `/frames/${slug}/${String(ni).padStart(4, '0')}.png`
      }

      imgA.style.opacity = String((1 - blend).toFixed(3))
      imgB.style.opacity = String(blend.toFixed(3))

      setProgress(p * 100)
      setFrameLabel(`FRAME ${String(ci).padStart(3, '0')} / ${totalFrames}`)

      if (p < 1.0) {
        rafRef.current = requestAnimationFrame(tick)
      }
    }

    rafRef.current = requestAnimationFrame(tick)
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current) }
  }, [slug, totalFrames, phase_started_at, phase_duration])

  if (!artwork) return null

  return (
    <div className="morphing-container">
      {/* imgA gets its initial src set via useLayoutEffect before first paint */}
      <img ref={imgARef} className="morphing-img" alt="" />
      <img ref={imgBRef} className="morphing-img" style={{ opacity: 0 }} alt="" />

      <div className="gilt-border" />

      <div className="morphing-top">
        <div className="morphing-title">{artwork.title}</div>
        <div className="morphing-frame-label">{frameLabel}</div>
      </div>

      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${progress.toFixed(2)}%` }} />
      </div>

      <div className="morphing-emotion-overlay">
        <div className="emotion-section-label">YOUR EMOTIONS</div>
        {EMOTION_ORDER.filter((k) => k in emotions).length > 0 ? (
          EMOTION_ORDER.filter((k) => k in emotions).map((key) => {
            const pct = Math.round(emotions[key] * 1000) / 10
            return (
              <div className="emotion-bar-row" key={key}>
                <div className="emotion-bar-header">
                  <span>{EMOTION_LATIN[key]}</span>
                  <span>{pct}%</span>
                </div>
                <div className="emotion-bar-track">
                  <div className="emotion-bar-fill" style={{ width: `${pct}%` }} />
                </div>
              </div>
            )
          })
        ) : (
          <div style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontStyle: 'italic',
            color: 'var(--gold-dark)',
            textAlign: 'center',
          }}>
            Reading…
          </div>
        )}
      </div>
    </div>
  )
}
