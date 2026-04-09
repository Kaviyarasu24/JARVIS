import { useRef, useState, useCallback, useEffect } from 'react'

const WS_URL = 'ws://127.0.0.1:8765/ws/chat'
const RECONNECT_DELAY = 2000

export default function useWebSocket() {
  const wsRef = useRef(null)
  const [connected, setConnected] = useState(false)
  const [agentStatus, setAgentStatus] = useState('standby')
  const [messages, setMessages] = useState([])
  const reconnectTimer = useRef(null)

  const addMessage = useCallback((role, text) => {
    setMessages((prev) => [
      ...prev,
      { id: Date.now() + Math.random(), role, text, time: new Date() },
    ])
  }, [])

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      console.log('[WS] Connected')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'status') {
          setAgentStatus(data.status)
        } else if (data.type === 'response') {
          addMessage('jarvis', data.text)
        } else if (data.type === 'notification') {
          addMessage('jarvis', data.message)
        }
      } catch (err) {
        console.error('[WS] Parse error:', err)
      }
    }

    ws.onclose = () => {
      setConnected(false)
      setAgentStatus('standby')
      console.log('[WS] Disconnected — reconnecting...')
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY)
    }

    ws.onerror = (err) => {
      console.error('[WS] Error:', err)
      ws.close()
    }
  }, [addMessage])

  const sendCommand = useCallback(
    (text) => {
      if (!text.trim()) return
      addMessage('user', text.trim())
      setAgentStatus('processing')
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ text: text.trim() }))
      }
    },
    [addMessage]
  )

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  return { connected, agentStatus, messages, sendCommand, setAgentStatus }
}
