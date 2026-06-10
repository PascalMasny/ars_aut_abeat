import type { ServerState } from '../hooks/useWebSocket'

interface Props {
  state: ServerState
}

const SEAL_COLORS: Record<string, string> = {
  VALLIS: '#8B2222',
  LIMEN:  '#8B9E6B',
  FIRMA:  '#C9A961',
}

export function RecapPhase({ state }: Props) {
  const { artwork, verdict, recap_graph } = state
  if (!artwork) return null

  const slug = artwork.slug
  const total = artwork.total_frames
  const firstUrl = `/frames/${slug}/0000.png`
  const lastUrl  = `/frames/${slug}/${String(total).padStart(4, '0')}.png`
  const sc = SEAL_COLORS[verdict] ?? '#C9A961'

  return (
    <div className="phase-layout">
      <div className="phase-left">
        <div className="recap-left">
          <div className="recap-thumbnails">
            <div>
              <div className="recap-thumb-label">ORIGINAL</div>
              <div className="recap-thumb-frame">
                <img src={firstUrl} alt="original" />
              </div>
            </div>
            <div>
              <div className="recap-thumb-label">AFTER 50 ITERATIONS</div>
              <div className="recap-thumb-frame">
                <img src={lastUrl} alt="final frame" />
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="phase-right">
        <div className="recap-header">
          <div className="recap-section-label">YOUR EMOTIONAL DESCENT</div>
          <div className="recap-artwork-name">{artwork.title}</div>
        </div>

        {recap_graph ? (
          <img
            className="recap-graph"
            src={`data:image/png;base64,${recap_graph}`}
            alt="emotion graph"
          />
        ) : (
          <div style={{
            color: 'var(--gold-dark)',
            fontStyle: 'italic',
            textAlign: 'center',
            padding: '1rem',
            fontFamily: "'Cormorant Garamond', serif",
            fontSize: 'clamp(1.2rem,3vh,2.8rem)',
          }}>
            No emotion data recorded.
          </div>
        )}

        <div className="recap-seal-row">
          <div
            className="seal-medallion"
            style={{
              border: `5px solid ${sc}`,
              background: `radial-gradient(circle at 40% 35%, ${sc}66, ${sc}22)`,
              color: sc,
            }}
          >
            {verdict}
          </div>
        </div>
      </div>
    </div>
  )
}
