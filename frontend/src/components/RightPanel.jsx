import AudioVisualizer from './AudioVisualizer'
import VolumeControl from './VolumeControl'
import SessionInfo from './SessionInfo'
import AgentStatus from './AgentStatus'

export default function RightPanel({ agentState, connected }) {
  return (
    <div className="right-panel">
      <AudioVisualizer agentState={agentState} />
      <VolumeControl />
      <SessionInfo connected={connected} />
      <AgentStatus agentState={agentState} />
    </div>
  )
}
