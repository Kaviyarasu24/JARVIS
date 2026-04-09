import { useState, useEffect, useMemo } from 'react'

export default function SessionInfo({ connected }) {
  const [time, setTime] = useState(new Date())

  const sessionId = useMemo(
    () => '#' + Math.random().toString(16).slice(2, 10).toUpperCase(),
    []
  )

  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(interval)
  }, [])

  const dateStr = time.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })

  const timeStr = time.toLocaleTimeString('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })

  return (
    <div className="panel-section">
      <div className="panel-label">SESSION</div>
      <div className="panel-value">{sessionId}</div>
      <div className="panel-detail">
        {dateStr} &nbsp; {timeStr}
      </div>
      <div className="panel-detail" style={{ marginTop: 2 }}>
        <span
          className="status-dot"
          style={{
            background: connected ? '#44ff88' : '#ff4444',
            boxShadow: connected
              ? '0 0 8px #44ff88, 0 0 12px rgba(68, 255, 136, 0.4)'
              : '0 0 8px #ff4444, 0 0 12px rgba(255, 68, 68, 0.4)',
          }}
        />
        <span style={{
          color: connected ? '#44ff88' : '#ff4444',
          textShadow: connected ? '0 0 8px rgba(68, 255, 136, 0.5)' : '0 0 8px rgba(255, 68, 68, 0.5)',
          fontWeight: 600
        }}>
          {connected ? 'CONNECTED' : 'OFFLINE'}
        </span>
      </div>
    </div>
  )
}
