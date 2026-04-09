import { useCallback } from 'react'
import ParticleSphere from './components/ParticleSphere'
import SubtitleChat from './components/SubtitleChat'
import RightPanel from './components/RightPanel'
import CommandInput from './components/CommandInput'
import StatusText from './components/StatusText'
import useWebSocket from './hooks/useWebSocket'
import useVoice from './hooks/useVoice'
import useNotifications from './hooks/useNotifications'
import './styles/particles.css'
import './styles/components.css'

export default function App() {
  const { connected, agentStatus, messages, sendCommand, setAgentStatus } =
    useWebSocket()

  // Voice input — on result send as command
  const handleVoiceResult = useCallback(
    (transcript) => {
      sendCommand(transcript)
    },
    [sendCommand]
  )

  const { listening, toggleListening } = useVoice(handleVoiceResult)

  // When voice starts, set agent status to listening
  const handleVoiceToggle = useCallback(() => {
    if (!listening) {
      setAgentStatus('listening')
    }
    toggleListening()
  }, [listening, toggleListening, setAgentStatus])

  // Notification WebSocket — messages appear as subtitles
  useNotifications(
    useCallback(
      (data) => {
        // Notifications are already added via the chat WebSocket messages array
        // This hook ensures the connection stays alive
      },
      []
    )
  )

  // Window controls (Electron)
  const electron = window.electronAPI

  return (
    <div className="app-container">
      {/* ── Titlebar ─────────────────────────────────────────────────── */}
      <div className="titlebar">
        <div className="titlebar-title">JARVIS &nbsp;·&nbsp; V2</div>
        {electron && (
          <div className="titlebar-controls">
            <button
              className="titlebar-btn"
              onClick={() => electron.minimize()}
              title="Minimize"
            />
            <button
              className="titlebar-btn"
              onClick={() => electron.maximize()}
              title="Maximize"
            />
            <button
              className="titlebar-btn close"
              onClick={() => electron.close()}
              title="Close"
            />
          </div>
        )}
      </div>

      {/* ── Main Area ────────────────────────────────────────────────── */}
      <div className="main-area">
        {/* Center: Particle Sphere + Subtitles + Input */}
        <div className="center-stage">
          <ParticleSphere agentState={agentStatus} />
          <SubtitleChat messages={messages} />
          <CommandInput
            onSend={sendCommand}
            onVoice={handleVoiceToggle}
            listening={listening}
          />
          <StatusText agentState={agentStatus} />
        </div>

        {/* Right: Floating panels */}
        <RightPanel agentState={agentStatus} connected={connected} />
      </div>
    </div>
  )
}
