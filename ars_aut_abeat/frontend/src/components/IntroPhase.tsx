import type { ServerState } from '../hooks/useWebSocket'

interface Props {
  state: ServerState
}

export function IntroPhase({ state }: Props) {
  const { artwork } = state
  if (!artwork) return null

  const firstFrameUrl = `/frames/${artwork.slug}/0000.png`

  return (
    <div className="intro-overlay">
      <img className="intro-artwork" src={firstFrameUrl} alt={artwork.title} />
      <div className="gilt-border" />

      <div className="intro-top">
        <div className="intro-label">THIS IS</div>
        <div className="intro-title">{artwork.title}</div>
      </div>

      <div className="intro-bottom">
        <div className="intro-body">
          We will now give this picture to an{' '}
          <span className="intro-em">AI</span>.
          It will try to recreate the same picture —{' '}
          <span className="intro-count">over 100 times</span>.
        </div>
        <div className="intro-closing">Let us see what the AI does.</div>
      </div>
    </div>
  )
}
