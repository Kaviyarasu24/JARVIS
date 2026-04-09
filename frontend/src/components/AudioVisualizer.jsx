import { useState, useEffect, useRef } from 'react'

const BAR_COUNT = 20

export default function AudioVisualizer({ agentState }) {
  const [bars, setBars] = useState(() => new Array(BAR_COUNT).fill(3))
  const frameRef = useRef(null)

  useEffect(() => {
    const isSpeaking = agentState === 'speaking'
    const isProcessing = agentState === 'processing'
    const isActive = isSpeaking || isProcessing

    const animate = () => {
      setBars((prev) =>
        prev.map((_, i) => {
          if (!isActive) return 3
          // Simulated waveform — varying heights
          const base = isSpeaking ? 14 : 8
          const variance = isSpeaking ? 10 : 5
          return base + Math.sin(Date.now() * 0.008 + i * 0.7) * variance +
                 Math.random() * (variance * 0.4)
        })
      )
      frameRef.current = requestAnimationFrame(animate)
    }

    if (isActive) {
      animate()
    } else {
      cancelAnimationFrame(frameRef.current)
      setBars(new Array(BAR_COUNT).fill(3))
    }

    return () => cancelAnimationFrame(frameRef.current)
  }, [agentState])

  const statusLabel =
    agentState === 'speaking' ? 'SPEAKING' :
    agentState === 'processing' ? 'PROCESSING' :
    agentState === 'listening' ? 'LISTENING' :
    'STANDBY'

  return (
    <div className="panel-section">
      <div className="panel-label">AUDIO OUTPUT ●</div>
      <div className="audio-viz">
        {bars.map((h, i) => (
          <div
            key={i}
            className={`audio-bar ${agentState === 'speaking' || agentState === 'processing' ? 'lit' : ''}`}
            style={{ height: `${Math.max(3, h)}px` }}
          />
        ))}
      </div>
      <div className="panel-detail">
        <span className={`status-dot ${agentState}`} />
        {statusLabel}
      </div>
    </div>
  )
}
