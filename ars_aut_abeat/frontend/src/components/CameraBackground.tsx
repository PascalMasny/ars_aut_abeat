import { useEffect } from 'react'
import { useCamera } from '../hooks/useCamera'

interface Props {
  onFrame: (blob: Blob) => void
  capturing: boolean
}

export function CameraBackground({ onFrame, capturing }: Props) {
  const { videoRef, ready, error, startCapture, stopCapture } = useCamera()

  useEffect(() => {
    if (ready && capturing) {
      startCapture(onFrame)
    } else {
      stopCapture()
    }
  }, [ready, capturing, onFrame, startCapture, stopCapture])

  if (error) {
    return (
      <div className="camera-setup">
        <h1>THE VALLEY OF LIKENESS</h1>
        <p>Camera access required. Please allow camera permission and reload.</p>
        <p style={{ color: 'var(--gold-dark)', fontSize: '2rem' }}>{error}</p>
      </div>
    )
  }

  return (
    <div className="camera-bg">
      <video ref={videoRef} autoPlay muted playsInline />
    </div>
  )
}
