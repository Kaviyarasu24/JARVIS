import { useState, useCallback } from 'react'

const API_BASE = 'http://127.0.0.1:8765'

export default function VolumeControl() {
  const [volume, setVolume] = useState(80)
  const [muted, setMuted] = useState(false)

  const handleVolumeChange = useCallback(async (e) => {
    const level = parseInt(e.target.value, 10)
    setVolume(level)
    try {
      await fetch(`${API_BASE}/api/volume`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ level }),
      })
    } catch (err) {
      console.warn('[Volume] API error:', err)
    }
  }, [])

  const handleMute = useCallback(async () => {
    setMuted((prev) => !prev)
    try {
      await fetch(`${API_BASE}/api/mute`, { method: 'POST' })
    } catch (err) {
      console.warn('[Mute] API error:', err)
    }
  }, [])

  return (
    <div className="panel-section">
      <div className="panel-label">VOLUME CONTROL</div>
      <div className="volume-row">
        <input
          type="range"
          className="volume-slider"
          min="0"
          max="100"
          value={volume}
          onChange={handleVolumeChange}
        />
        <span className="volume-pct">{volume}%</span>
      </div>
      <div>
        <button className="mute-btn" onClick={handleMute}>
          {muted ? 'UNMUTE' : 'CH MUTE'}
        </button>
      </div>
    </div>
  )
}
