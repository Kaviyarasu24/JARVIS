import { useRef, useEffect, useState, useCallback } from 'react'

const NOTIFY_URL = 'ws://127.0.0.1:8765/ws/notify'

export default function useNotifications(onNotification) {
  const wsRef = useRef(null)
  const [notifyConnected, setNotifyConnected] = useState(false)
  const reconnectTimer = useRef(null)

  const connect = useCallback(() => {
    const ws = new WebSocket(NOTIFY_URL)
    wsRef.current = ws

    ws.onopen = () => setNotifyConnected(true)

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'notification' && onNotification) {
          onNotification(data)
        }
      } catch (err) {
        console.error('[Notify] Parse error:', err)
      }
    }

    ws.onclose = () => {
      setNotifyConnected(false)
      reconnectTimer.current = setTimeout(connect, 3000)
    }

    ws.onerror = () => ws.close()
  }, [onNotification])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  return { notifyConnected }
}
