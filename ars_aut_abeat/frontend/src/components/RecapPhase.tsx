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
    <div className="recap-overlay">
      <div className="gilt-border" />

      <div className="recap-header">
        <div className="recap-section-label">YOUR EMOTIONAL DESCENT</div>
        <div className="recap-artwork-name">{artwork.title}</div>
      </div>

      <div className="recap-thumbnails">
        <div>
          <div className="recap-thumb-label">ORIGINAL</div>
          <div className="recap-thumb-frame">
            <img src={firstUrl} alt="original" />
          </div>
        </div>
        <div>
          <div className="recap-thumb-label">AFTER 100 ITERATIONS</div>
          <div className="recap-thumb-frame">
            <img src={lastUrl} alt="final frame" />
          </div>
        </div>
      </div>

      <div style={{ width: '100%', flexShrink: 0, marginBottom: '1.5vh' }}>
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
          }}>
            No emotion data recorded.
          </div>
        )}
      </div>

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
  )
}
