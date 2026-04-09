import { useEffect, useState, useRef } from 'react'

const DISPLAY_DURATION = 8000
const FADE_DURATION = 600
const MAX_VISIBLE = 3

export default function SubtitleChat({ messages }) {
  const [visible, setVisible] = useState([])
  const timersRef = useRef({})

  useEffect(() => {
    if (messages.length === 0) return

    const latest = messages[messages.length - 1]

    // Avoid duplicate
    if (timersRef.current[latest.id]) return

    setVisible((prev) => {
      const next = [...prev, { ...latest, fading: false }]
      return next.slice(-MAX_VISIBLE)
    })

    // Start fade-out timer
    const fadeTimer = setTimeout(() => {
      setVisible((prev) =>
        prev.map((m) => (m.id === latest.id ? { ...m, fading: true } : m))
      )

      // Remove after fade animation
      setTimeout(() => {
        setVisible((prev) => prev.filter((m) => m.id !== latest.id))
        delete timersRef.current[latest.id]
      }, FADE_DURATION)
    }, DISPLAY_DURATION)

    timersRef.current[latest.id] = fadeTimer
  }, [messages])

  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      Object.values(timersRef.current).forEach(clearTimeout)
    }
  }, [])

  return (
    <div className="subtitle-container">
      {visible.map((msg) => (
        <div
          key={msg.id}
          className={`subtitle-message ${msg.fading ? 'fading' : ''}`}
        >
          <span className="subtitle-prefix">
            {msg.role === 'user' ? 'YOU' : 'JARVIS'}:
          </span>{' '}
          {msg.text}
        </div>
      ))}
    </div>
  )
}
