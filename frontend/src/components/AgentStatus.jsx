const STATUS_LABELS = {
  standby: 'Standby',
  listening: 'Listening...',
  processing: 'Processing...',
  speaking: 'Responding...',
}

export default function AgentStatus({ agentState }) {
  const label = STATUS_LABELS[agentState] || 'Standby'

  return (
    <div className="panel-section">
      <div className="panel-label">AGENT</div>
      <div className="panel-value">JARVIS</div>
      <div className="panel-detail">
        <span className={`status-dot ${agentState}`} />
        {label}
      </div>
    </div>
  )
}
