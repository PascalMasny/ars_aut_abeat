import { useCallback } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import { CameraBackground } from './components/CameraBackground'
import { IdlePhase } from './components/IdlePhase'
import { IntroPhase } from './components/IntroPhase'
import { MorphingPhase } from './components/MorphingPhase'
import { RecapPhase } from './components/RecapPhase'

const WS_URL =
  window.location.protocol === 'https:'
    ? `wss://${window.location.host}/ws`
    : `ws://${window.location.host}/ws`

export default function App() {
  const { state, sendFrame } = useWebSocket(WS_URL)

  const handleFrame = useCallback((blob: Blob) => {
    sendFrame(blob)
  }, [sendFrame])

  return (
    <div className="installation">
      <div className="viewport">
        <CameraBackground onFrame={handleFrame} capturing />

        {state.phase === 'IDLE'     && <IdlePhase     state={state} />}
        {state.phase === 'INTRO'    && <IntroPhase    state={state} />}
        {state.phase === 'MORPHING' && <MorphingPhase state={state} />}
        {state.phase === 'RECAP'    && <RecapPhase    state={state} />}
      </div>
    </div>
  )
}
