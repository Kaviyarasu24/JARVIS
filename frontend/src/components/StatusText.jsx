const STATUS_LABELS = {
  standby: 'STANDBY',
  listening: 'LISTENING',
  processing: 'PROCESSING',
  speaking: 'SPEAKING',
}

export default function StatusText({ agentState }) {
  const label = STATUS_LABELS[agentState] || 'STANDBY'

  return (
    <div className="status-text">
      <span>JARVIS</span>
      <span className="arrow">→</span>
      <span>{label}</span>
    </div>
  )
}
