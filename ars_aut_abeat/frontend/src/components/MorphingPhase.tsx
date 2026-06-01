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

const frameCache = new Map<string, HTMLImageElement>()

function warmFrame(slug: string, idx: number): HTMLImageElement {
  const key = `${slug}:${idx}`
  if (!frameCache.has(key)) {
    const img = new Image()
    img.src = `/frames/${slug}/${String(idx).padStart(4, '0')}.png`
    frameCache.set(key, img)
  }
  return frameCache.get(key)!
}

function isReady(img: HTMLImageElement) {
  return img.complete && img.naturalWidth > 0
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

  useLayoutEffect(() => {
    if (!slug || !imgARef.current) return
    const f0 = warmFrame(slug, 0)
    warmFrame(slug, 1)
    const apply = () => { if (imgARef.current) imgARef.current.src = f0.src }
    if (isReady(f0)) apply()
    else f0.addEventListener('load', apply, { once: true })
  }, [slug])

  useEffect(() => {
    if (!slug) return

    let curIdx = -1
    let nextIdx = -1

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

      for (let a = 0; a <= 3; a++) warmFrame(slug, Math.min(ci + a, totalFrames))

      const fA = warmFrame(slug, ci)
      const fB = warmFrame(slug, ni)

      const imgA = imgARef.current
      const imgB = imgBRef.current
      if (!imgA || !imgB) return

      if (ci !== curIdx && isReady(fA)) {
        curIdx = ci
        imgA.src = fA.src
      }
      if (ni !== nextIdx && isReady(fB)) {
        nextIdx = ni
        imgB.src = fB.src
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

  const visibleEmotions = EMOTION_ORDER.filter((k) => k in emotions)

  return (
    <div className="phase-layout">
      <div className="phase-left" style={{ background: '#0a0806' }}>
        <img ref={imgARef} className="morphing-img" alt="" />
        <img ref={imgBRef} className="morphing-img" style={{ opacity: 0 }} alt="" />
        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${progress.toFixed(2)}%` }} />
        </div>
      </div>
      <div className="phase-right">
        <div className="morphing-top">
          <div className="morphing-title">{artwork.title}</div>
          <div className="morphing-frame-label">{frameLabel}</div>
        </div>
        <div className="morphing-emotion-section">
          <div className="emotion-section-label">YOUR EMOTIONS</div>
          {visibleEmotions.length > 0 ? (
            visibleEmotions.map((key) => {
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
              fontSize: 'clamp(0.8rem,1.6vh,1.2rem)',
            }}>
              Reading…
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
