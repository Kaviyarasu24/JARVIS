import { useState, useCallback } from 'react'

export default function CommandInput({ onSend, onVoice, listening }) {
  const [text, setText] = useState('')

  const handleSubmit = useCallback(
    (e) => {
      e?.preventDefault()
      if (!text.trim()) return
      onSend(text.trim())
      setText('')
    },
    [text, onSend]
  )

  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Enter') handleSubmit()
    },
    [handleSubmit]
  )

  return (
    <div className="command-bar">
      <button
        className={`voice-btn ${listening ? 'active' : ''}`}
        onClick={onVoice}
        title={listening ? 'Stop listening' : 'Voice command'}
      >
        🎤
      </button>
      <input
        className="command-input"
        type="text"
        placeholder="Enter directive..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        autoFocus
      />
      <button className="command-send" onClick={handleSubmit}>
        SEND
      </button>
    </div>
  )
}
