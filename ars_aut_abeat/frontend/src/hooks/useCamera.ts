import { useEffect, useRef, useState, useCallback } from 'react'

interface UseCameraResult {
  videoRef: React.RefObject<HTMLVideoElement | null>
  ready: boolean
  error: string | null
  startCapture: (onFrame: (blob: Blob) => void) => void
  stopCapture: () => void
}

export function useCamera(): UseCameraResult {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const intervalRef = useRef<number | null>(null)
  const [ready, setReady] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const canvas = document.createElement('canvas')
    canvas.width = 640
    canvas.height = 480
    canvasRef.current = canvas

    navigator.mediaDevices
      .getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          frameRate: { ideal: 15, max: 20 },
          facingMode: 'user',
        },
        audio: false,
      })
      .then((stream) => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          videoRef.current.onloadedmetadata = () => {
            videoRef.current?.play()
            setReady(true)
          }
        }
      })
      .catch((err) => {
        setError(err.message ?? 'Camera access denied')
      })

    return () => {
      if (videoRef.current?.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream
        stream.getTracks().forEach((t) => t.stop())
      }
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [])

  const startCapture = useCallback((onFrame: (blob: Blob) => void) => {
    if (intervalRef.current) clearInterval(intervalRef.current)
    intervalRef.current = window.setInterval(() => {
      const video = videoRef.current
      const canvas = canvasRef.current
      if (!video || !canvas || video.readyState < 2) return
      const ctx = canvas.getContext('2d')
      if (!ctx) return
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
      canvas.toBlob(
        (blob) => { if (blob) onFrame(blob) },
        'image/jpeg',
        0.7
      )
    }, 100) // 10 Hz
  }, [])

  const stopCapture = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  return { videoRef, ready, error, startCapture, stopCapture }
}
