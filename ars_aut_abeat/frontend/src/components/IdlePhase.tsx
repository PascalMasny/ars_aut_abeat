import type { ServerState } from '../hooks/useWebSocket'

interface Props {
  state: ServerState
}

export function IdlePhase({ state }: Props) {
  if (state.attract_mode) {
    return (
      <div className="phase-layout">
        <div className="phase-left">
          <div className="vignette" />
        </div>
        <div className="phase-right">
          <div className="attract-title">VALLIS · SIMVLACRI</div>
          <div className="attract-tagline">The Valley of Likeness</div>
          <div className="divider">❧ · · · ❧</div>
          <div className="attract-concept">
            In 1970, roboticist Masahiro Mori described the <em>uncanny valley</em> —
            the point where a human likeness becomes too real and tips into revulsion.
            This installation measures your descent in real time.
          </div>
          <div>
            {state.soul_count === 0 ? (
              <div style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontStyle: 'italic',
                fontSize: 'clamp(1.03rem,2.18vh,1.69rem)',
                color: 'var(--gold-dark)',
                textAlign: 'center',
              }}>
                Be the first to enter
              </div>
            ) : (
              <div className="attract-soul-counter">
                ✦ &nbsp; {state.soul_count} &nbsp;
                {state.soul_count === 1 ? 'SOUL' : 'SOULS'} HAVE ENTERED THE VALLEY &nbsp; ✦
              </div>
            )}
          </div>
          {state.attract_graph ? (
            <img
              className="attract-graph"
              src={`data:image/png;base64,${state.attract_graph}`}
              alt="aggregate data"
            />
          ) : (
            <div style={{
              fontFamily: "'Cormorant Garamond', serif",
              fontStyle: 'italic',
              color: 'var(--gold-dark)',
              textAlign: 'center',
              fontSize: 'clamp(0.97rem,1.94vh,1.45rem)',
            }}>
              Awaiting the first soul…
            </div>
          )}
          <div className="divider">❧ · · · ❧</div>
          <div className="attract-cta">RAISE BOTH HANDS TO ENTER THE VALLEY</div>
        </div>
      </div>
    )
  }

  const { face_present, hands_raised } = state
  let statusIcon = '◎'
  let statusText = 'APPROACH · BE SEEN'
  let statusColor = 'var(--gold-dark)'
  let hint = 'Stand before the glass and raise both hands when ready.'

  if (hands_raised) {
    statusIcon = '✦'
    statusText = 'CONSENT ACKNOWLEDGED — HOLD'
    statusColor = 'var(--gold-bright)'
    hint = 'Entering the valley…'
  } else if (face_present) {
    statusIcon = '◉'
    statusText = 'VISITOR DETECTED'
    statusColor = 'var(--gold)'
    hint = 'Raise both hands to accept and begin.'
  }

  return (
    <div className="phase-layout">
      <div className="phase-left">
        <div className="vignette" />
        <div className="mirror-top">
          <div className="mirror-title">VALLIS · SIMVLACRI</div>
          <div className="mirror-divider">❧ · · ❧</div>
        </div>
      </div>
      <div className="phase-right">
        <div className="idle-right">
          <div className="mirror-status" style={{ color: statusColor }}>
            <span>{statusIcon}</span>
            {statusText}
            <span>{statusIcon}</span>
          </div>
          <div className="mirror-hint">{hint}</div>
          <div className="divider">❧ · · ❧</div>
          <div className="mirror-script">Vallis Simulacri</div>
          <div className="mirror-subtitle">THE VALLEY OF LIKENESS</div>
        </div>
      </div>
    </div>
  )
}
