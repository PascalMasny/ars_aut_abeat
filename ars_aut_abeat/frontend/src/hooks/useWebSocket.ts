import { useEffect, useRef, useState, useCallback } from 'react'

export interface Artwork {
  slug: string
  title: string
  artist: string
  total_frames: number
}

export interface Collective {
  soul_count: number
  dominant_latin: string
  verdict: string
  concordance: number
}

export interface ServerState {
  phase: 'IDLE' | 'INTRO' | 'MORPHING' | 'RECAP'
  phase_elapsed: number
  phase_duration: number
  phase_started_at: number
  attract_mode: boolean
  soul_count: number
  emotions: Record<string, number>
  face_present: boolean
  hands_raised: boolean
  artwork: Artwork | null
  verdict: string
  personal_lines: [string, number][]
  collective: Collective | null
  recap_graph: string | null
  attract_graph: string | null
}

const DEFAULT_STATE: ServerState = {
  phase: 'IDLE',
  phase_elapsed: 0,
  phase_duration: 0,
  phase_started_at: Date.now() / 1000,
  attract_mode: false,
  soul_count: 0,
  emotions: {},
  face_present: false,
  hands_raised: false,
  artwork: null,
  verdict: '',
  personal_lines: [],
  collective: null,
  recap_graph: null,
  attract_graph: null,
}

interface UseWebSocketResult {
  state: ServerState
  connected: boolean
  sendFrame: (blob: Blob) => void
}

export function useWebSocket(url: string): UseWebSocketResult {
  const [state, setState] = useState<ServerState>(DEFAULT_STATE)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<number | null>(null)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(url)
    ws.binaryType = 'arraybuffer'
    wsRef.current = ws

    ws.onopen = () => setConnected(true)

    ws.onmessage = (evt) => {
      if (typeof evt.data === 'string') {
        try {
          setState(JSON.parse(evt.data))
        } catch {}
      }
    }

    ws.onclose = () => {
      setConnected(false)
      reconnectTimer.current = window.setTimeout(connect, 2000)
    }

    ws.onerror = () => ws.close()
  }, [url])

  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  const sendFrame = useCallback((blob: Blob) => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) return
    blob.arrayBuffer().then((buf) => ws.send(buf))
  }, [])

  return { state, connected, sendFrame }
}
