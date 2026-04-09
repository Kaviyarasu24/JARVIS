import { useRef, useState, useCallback } from 'react'

export default function useVoice(onResult) {
  const [listening, setListening] = useState(false)
  const recognitionRef = useRef(null)

  const startListening = useCallback(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      console.warn('[Voice] Web Speech API not supported')
      return
    }

    if (recognitionRef.current) {
      recognitionRef.current.abort()
    }

    const recognition = new SpeechRecognition()
    recognition.lang = 'en-IN'
    recognition.continuous = false
    recognition.interimResults = false
    recognition.maxAlternatives = 1
    recognitionRef.current = recognition

    recognition.onstart = () => setListening(true)

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      if (transcript && onResult) {
        onResult(transcript)
      }
    }

    recognition.onerror = (event) => {
      console.warn('[Voice] Error:', event.error)
      setListening(false)
    }

    recognition.onend = () => {
      setListening(false)
      recognitionRef.current = null
    }

    recognition.start()
  }, [onResult])

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
    }
  }, [])

  const toggleListening = useCallback(() => {
    if (listening) {
      stopListening()
    } else {
      startListening()
    }
  }, [listening, startListening, stopListening])

  return { listening, toggleListening }
}
