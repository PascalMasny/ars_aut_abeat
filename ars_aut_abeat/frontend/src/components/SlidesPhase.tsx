import { useEffect, useRef, useState } from 'react'

const AUTO_INTERVAL_S = 10

const SLIDES = [
  {
    tag: 'DIE FRAGE',
    title: 'Ab wann ist etwas\nnicht mehr Kunst?',
    body: null,
    closing: null,
  },
  {
    tag: 'DAS UNCANNY VALLEY',
    title: 'Das Tal des Unheimlichen',
    body: 'Der Robotiker Masahiro Mori beschrieb 1970 ein Phänomen: Je menschenähnlicher ein Objekt wird, desto sympathischer wirkt es — bis zu einem Punkt. Dann kippt die Wahrnehmung abrupt ins Unheimliche.\n\nDieses Tal nennt er das Uncanny Valley.',
    closing: 'Gilt dasselbe für Kunst?',
  },
  {
    tag: 'KI UND KREATIVITÄT',
    title: 'Kann eine Maschine\nbedeutsam schaffen?',
    body: 'Eine KI iteriert. Sie optimiert. Sie ahmt nach — ohne je etwas zu meinen.\n\nKunst entsteht aus Intention, aus Schmerz, aus Blick. Was bleibt, wenn man das herausnimmt und nur die Form lässt?',
    closing: 'Ist das noch Kunst — oder nur Oberfläche?',
  },
  {
    tag: 'DAS EXPERIMENT',
    title: 'Was hier passiert',
    body: 'Zuerst siehst du das Original — 8 Sekunden lang. Die Kamera liest dein Gesicht und speichert deine Baseline: dein Ausdruck vor echter Kunst.\n\nDann folgen zehn Bilder. Eine KI hat das Gemälde zehn Mal neu erschaffen — jede Iteration entfernt sich weiter vom Original. Alle drei Sekunden ein neues Bild.',
    closing: 'Deine Abweichung von der Baseline ist der Datenpunkt.',
  },
  {
    tag: 'DAS URTEIL',
    title: 'Der Bruchpunkt',
    body: null,
    closing: null,
    verdicts: [
      { label: 'DER BRUCHPUNKT', sub: 'Hier stirbt die Kunst', desc: 'Das Bild mit deiner stärksten Reaktion ist dein Bruchpunkt. Das Bild davor: noch Kunst. Ab hier: keine mehr. Du ziehst die Linie — nicht die Maschine.' },
      { label: 'GEFALLEN · SCHWELLE', sub: 'Wie tief bist du gefallen?', desc: 'Gefallen: starke Reaktion, tief ins Tal gestürzt. Schwelle: messbar, aber mild — du spürst etwas.' },
      { label: 'UNERSCHÜTTERT', sub: 'Es blieb Kunst', desc: 'Kein Bild hat dich bewegt. Für dich hat es nie aufgehört, Kunst zu sein — oder du hast ein perfektes Pokerface.' },
    ],
  },
  {
    tag: 'JETZT',
    title: 'Gleich steigt jemand\nin das Tal hinab.',
    body: 'Einer aus diesem Raum wird gleich vor die Kamera treten. Das Gemälde wird sich verändern. Das Urteil wird fallen.\n\nBeobachtet genau.',
    closing: 'Was werdet ihr fühlen?',
  },
]

interface Props {
  onClose: () => void
}

export function SlidesPhase({ onClose }: Props) {
  const [index, setIndex] = useState(0)
  const [auto, setAuto] = useState(false)
  const [progress, setProgress] = useState(0)
  const intervalRef = useRef<number | null>(null)
  const progressRef = useRef<number | null>(null)
  const startRef = useRef<number>(Date.now())

  const goTo = (i: number) => {
    setIndex(Math.max(0, Math.min(SLIDES.length - 1, i)))
    setProgress(0)
    startRef.current = Date.now()
  }

  const prev = () => goTo(index - 1)
  const next = () => {
    if (index < SLIDES.length - 1) goTo(index + 1)
    else onClose()
  }

  // Auto-advance
  useEffect(() => {
    if (!auto) {
      if (intervalRef.current) clearInterval(intervalRef.current)
      if (progressRef.current) clearInterval(progressRef.current)
      setProgress(0)
      return
    }
    startRef.current = Date.now()
    setProgress(0)

    progressRef.current = window.setInterval(() => {
      const elapsed = (Date.now() - startRef.current) / 1000
      setProgress(Math.min(elapsed / AUTO_INTERVAL_S, 1))
    }, 50)

    intervalRef.current = window.setInterval(() => {
      setIndex(prev => {
        const next = prev + 1
        if (next >= SLIDES.length) {
          onClose()
          return prev
        }
        startRef.current = Date.now()
        setProgress(0)
        return next
      })
    }, AUTO_INTERVAL_S * 1000)

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
      if (progressRef.current) clearInterval(progressRef.current)
    }
  }, [auto, onClose])

  // Keyboard nav
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.code === 'ArrowRight' || e.code === 'Space') { e.preventDefault(); next() }
      if (e.code === 'ArrowLeft')  { e.preventDefault(); prev() }
      if (e.code === 'Escape')     { e.preventDefault(); onClose() }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [index])

  const slide = SLIDES[index]

  return (
    <div style={{
      position: 'absolute', inset: 0, zIndex: 20,
      background: 'var(--ink)',
      display: 'flex', flexDirection: 'column',
    }}>
      {/* Progress bar (auto mode) */}
      {auto && (
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '3px', background: 'rgba(201,169,97,0.15)', zIndex: 30 }}>
          <div style={{ height: '100%', width: `${progress * 100}%`, background: 'var(--gold)', transition: 'width 0.05s linear' }} />
        </div>
      )}

      {/* Slide counter */}
      <div style={{
        position: 'absolute', top: '18px', left: '50%', transform: 'translateX(-50%)',
        fontFamily: "'Cinzel', serif", fontSize: 'clamp(0.6rem,1.2vh,1.1rem)',
        letterSpacing: '0.3em', color: 'var(--gold-dark)', zIndex: 25,
      }}>
        {index + 1} · {SLIDES.length}
      </div>

      {/* Main content */}
      <div style={{
        flex: 1, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        padding: 'clamp(2rem,6vh,5rem) clamp(3rem,8vw,8rem)',
        gap: 'clamp(1rem,2.5vh,2.5rem)', textAlign: 'center',
      }}>
        {/* Tag */}
        <div style={{
          fontFamily: "'Cormorant Garamond', serif", fontStyle: 'italic',
          fontSize: 'clamp(0.9rem,1.8vh,1.8rem)', letterSpacing: '0.3em',
          color: 'var(--gold-dark)',
        }}>
          {slide.tag}
        </div>

        {/* Divider */}
        <div style={{ color: 'var(--gold)', opacity: 0.4, letterSpacing: '0.3em', fontSize: 'clamp(0.8rem,1.5vh,1.4rem)' }}>
          ❧ · · · ❧
        </div>

        {/* Title */}
        <div style={{
          fontFamily: "'Cinzel', serif", fontWeight: 700,
          fontSize: 'clamp(2rem,5.5vh,5.5rem)', letterSpacing: '0.08em',
          color: 'var(--gold-bright)', lineHeight: 1.2,
          whiteSpace: 'pre-line',
          textShadow: '0 4px 30px rgba(201,169,97,0.3)',
        }}>
          {slide.title}
        </div>

        {/* Body text */}
        {slide.body && (
          <div style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontSize: 'clamp(1.2rem,2.5vh,2.5rem)', lineHeight: 1.7,
            color: 'var(--parchment-d)', maxWidth: '72ch',
            whiteSpace: 'pre-line',
          }}>
            {slide.body}
          </div>
        )}

        {/* Verdict cards (slide 5) */}
        {slide.verdicts && (
          <div style={{ display: 'flex', gap: 'clamp(1rem,2vw,2rem)', marginTop: '1vh', width: '100%', justifyContent: 'center' }}>
            {slide.verdicts.map(v => (
              <div key={v.label} style={{
                flex: '1 1 0', maxWidth: '28ch',
                border: '1px solid var(--gold-dark)', padding: 'clamp(0.8rem,2vh,2rem)',
                display: 'flex', flexDirection: 'column', gap: '0.6em', textAlign: 'center',
              }}>
                <div style={{ fontFamily: "'Cinzel', serif", fontWeight: 900, fontSize: 'clamp(1.2rem,2.8vh,2.8rem)', color: 'var(--gold)', letterSpacing: '0.12em' }}>{v.label}</div>
                <div style={{ fontFamily: "'Cormorant Garamond', serif", fontStyle: 'italic', fontSize: 'clamp(0.9rem,1.8vh,1.8rem)', color: 'var(--gold-dark)' }}>{v.sub}</div>
                <div style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: 'clamp(0.85rem,1.6vh,1.6rem)', color: 'var(--parchment-d)', lineHeight: 1.5 }}>{v.desc}</div>
              </div>
            ))}
          </div>
        )}

        {/* Closing */}
        {slide.closing && (
          <div style={{
            fontFamily: "'Cormorant Garamond', serif", fontStyle: 'italic',
            fontSize: 'clamp(1rem,2.2vh,2.2rem)', color: 'var(--gold-dark)',
            letterSpacing: '0.1em',
          }}>
            {slide.closing}
          </div>
        )}
      </div>

      {/* Bottom controls */}
      <div style={{
        position: 'absolute', bottom: '18px', left: 0, right: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        gap: '12px', zIndex: 25,
      }}>
        {/* Prev */}
        <button onClick={prev} disabled={index === 0} style={btnStyle(index === 0)}>←</button>

        {/* Dot indicators */}
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {SLIDES.map((_, i) => (
            <div key={i} onClick={() => goTo(i)} style={{
              width: i === index ? '20px' : '8px', height: '8px',
              borderRadius: '4px', cursor: 'pointer',
              background: i === index ? 'var(--gold)' : 'var(--gold-dark)',
              opacity: i === index ? 1 : 0.4,
              transition: 'all 0.3s',
            }} />
          ))}
        </div>

        {/* Next / Close */}
        <button onClick={next} style={btnStyle(false)}>
          {index === SLIDES.length - 1 ? '✕' : '→'}
        </button>

        {/* Auto toggle */}
        <button onClick={() => setAuto(a => !a)} style={{
          ...btnStyle(false),
          marginLeft: '16px',
          background: auto ? 'rgba(201,169,97,0.18)' : 'rgba(28,20,16,0.75)',
          color: auto ? 'var(--gold)' : 'var(--gold-dark)',
          border: `1px solid ${auto ? 'var(--gold)' : 'var(--gold-dark)'}`,
          fontSize: 'clamp(0.5rem,0.9vh,0.8rem)',
          letterSpacing: '0.15em',
          padding: '5px 12px',
        }}>
          {auto ? '⏸ AUTO' : '▶ AUTO'}
        </button>
      </div>

      {/* Close X top-right */}
      <button onClick={onClose} style={{
        position: 'absolute', top: '14px', right: '18px', zIndex: 30,
        background: 'transparent', border: 'none',
        color: 'var(--gold-dark)', fontFamily: "'Cinzel', serif",
        fontSize: 'clamp(0.7rem,1.3vh,1.2rem)', cursor: 'pointer',
        letterSpacing: '0.15em', padding: '4px 8px',
      }}>
        ✕ CLOSE
      </button>
    </div>
  )
}

function btnStyle(disabled: boolean): React.CSSProperties {
  return {
    background: 'rgba(28,20,16,0.75)',
    border: '1px solid var(--gold-dark)',
    color: disabled ? 'rgba(139,111,46,0.3)' : 'var(--gold)',
    fontFamily: "'Cinzel', serif",
    fontSize: 'clamp(0.7rem,1.3vh,1.2rem)',
    padding: '6px 14px',
    cursor: disabled ? 'default' : 'pointer',
    borderRadius: '3px',
    letterSpacing: '0.1em',
  }
}
