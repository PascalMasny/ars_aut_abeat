import { useEffect } from 'react'
import type { ServerState } from '../hooks/useWebSocket'

interface Props {
  state: ServerState
}

export function IntroPhase({ state }: Props) {
  const { artwork } = state

  useEffect(() => {
    if (!artwork) return
    const { slug, total_frames } = artwork
    for (let i = 0; i <= total_frames; i++) {
      const img = new Image()
      img.src = `/frames/${slug}/${String(i).padStart(4, '0')}.png`
    }
  }, [artwork?.slug])  // eslint-disable-line react-hooks/exhaustive-deps

  if (!artwork) return null

  const firstFrameUrl = `/frames/${artwork.slug}/0000.png`

  return (
    <div className="phase-layout">
      <div className="phase-left">
        <img className="intro-artwork" src={firstFrameUrl} alt={artwork.title} />
        <div className="intro-top">
          <div className="intro-label">THIS IS</div>
          <div className="intro-title">{artwork.title}</div>
        </div>
      </div>
      <div className="phase-right">
        <div className="intro-right">
          <div className="intro-body">
            We will now give this picture to an{' '}
            <span className="intro-em">AI</span>.
            It will try to recreate the same picture —{' '}
            <span className="intro-count">over 50 times</span>.
          </div>
          <div className="intro-closing">Let us see what the AI does.</div>
        </div>
      </div>
    </div>
  )
}
