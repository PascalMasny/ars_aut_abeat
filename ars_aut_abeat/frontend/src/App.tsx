import { useCallback, useEffect, useState } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import { CameraBackground } from './components/CameraBackground'
import { IdlePhase } from './components/IdlePhase'
import { BaselinePhase } from './components/BaselinePhase'
import { GalleryPhase } from './components/GalleryPhase'
import { RevealPhase } from './components/RevealPhase'
import { SlidesPhase } from './components/SlidesPhase'

const WS_URL =
  window.location.protocol === 'https:'
    ? `wss://${window.location.host}/ws`
    : `ws://${window.location.host}/ws`

export default function App() {
  const { state, sendFrame } = useWebSocket(WS_URL)
  const [showSlides, setShowSlides] = useState(false)

  const handleFrame = useCallback((blob: Blob) => {
    sendFrame(blob)
  }, [sendFrame])

  const toggleMode = useCallback(() => {
    const next = state.show_mode ? 'self' : 'show'
    fetch('/api/mode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: next }),
    })
  }, [state.show_mode])

  // Space/Enter triggers a run in show mode (not while slides open)
  useEffect(() => {
    if (!state.show_mode || showSlides) return
    const handler = (e: KeyboardEvent) => {
      if ((e.code === 'Space' || e.code === 'Enter') && state.phase === 'IDLE') {
        e.preventDefault()
        fetch('/api/trigger', { method: 'POST' })
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [state.show_mode, state.phase, showSlides])

  return (
    <div className="installation">
      <div className="viewport">
        <div className="gilt-border" />

        <CameraBackground onFrame={handleFrame} capturing />

        {state.phase === 'IDLE'     && <IdlePhase     state={state} />}
        {state.phase === 'BASELINE' && <BaselinePhase state={state} />}
        {state.phase === 'GALLERY'  && <GalleryPhase  state={state} />}
        {state.phase === 'REVEAL'   && <RevealPhase   state={state} />}

        {showSlides && <SlidesPhase onClose={() => setShowSlides(false)} />}

        {/* Bottom-right controls */}
        <div style={{
          position: 'absolute', bottom: '18px', right: '22px',
          zIndex: 50, display: 'flex', gap: '8px',
        }}>
          <button onClick={() => setShowSlides(s => !s)} style={ctrlBtn(showSlides)}>
            {showSlides ? '◉ SLIDES' : '◎ SLIDES'}
          </button>
          <button onClick={toggleMode} style={ctrlBtn(state.show_mode)}>
            {state.show_mode ? '◉ SHOW' : '◎ SELF'}
          </button>
        </div>
      </div>
    </div>
  )
}

function ctrlBtn(active: boolean): React.CSSProperties {
  return {
    background: active ? 'rgba(201,169,97,0.18)' : 'rgba(28,20,16,0.75)',
    border: `1px solid ${active ? 'var(--gold)' : 'var(--gold-dark)'}`,
    color: active ? 'var(--gold)' : 'var(--gold-dark)',
    fontFamily: "'Cinzel', serif",
    fontSize: 'clamp(0.55rem, 1vh, 0.85rem)',
    letterSpacing: '0.15em',
    padding: '5px 12px',
    cursor: 'pointer',
    borderRadius: '3px',
    transition: 'all 0.2s',
  }
}
