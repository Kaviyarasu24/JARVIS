import { useCallback } from 'react'
import useWebSocket from './hooks/useWebSocket'
import useVoice from './hooks/useVoice'
import useNotifications from './hooks/useNotifications'
import './styles/particles.css'
import './styles/components.css'

export default function App() {
  const { agentStatus, sendCommand } = useWebSocket()

  // Voice setup kept active in background
  const handleVoiceResult = useCallback(
    (transcript) => {
      sendCommand(transcript)
    },
    [sendCommand]
  )

  useVoice(handleVoiceResult)

  // Notification WebSocket
  useNotifications(
    useCallback(
      (data) => {
        // Keeps connection alive
      },
      []
    )
  )

  return (
    <div className="app-container">
      {/* ── Titlebar ─────────────────────────────────────────────────── */}
      <div className="titlebar">
        {/* Title and controls removed */}
      </div>

      {/* ── Main Area ────────────────────────────────────────────────── */}
      <div className="main-area">
        {/* Center stage is now completely empty */}
        <div className="center-stage">
        </div>
      </div>
    </div>
  )
}
