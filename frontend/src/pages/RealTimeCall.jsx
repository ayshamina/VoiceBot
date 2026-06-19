import { useEffect, useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import { simulateInboundCall, getVoiceStatus } from '../services/api'
import {
  isSpeechRecognitionSupported,
  createSpeechRecognition,
  speakTextWithBackendPromise,
  speakAudioUriPromise,
  cancelActiveAudio,
} from '../hooks/useSpeech'
import './RealTimeCall.css'

export default function RealTimeCall() {
  // ── State ──────────────────────────────────────────────────────────────────
  const [micAuthorized, setMicAuthorized] = useState(false)
  const [callState, setCallState] = useState('idle') // idle | ringing | connected | speaking | listening | processing | ended
  const [duration, setDuration] = useState(0)
  const [transcripts, setTranscripts] = useState([])
  const [language, setLanguage] = useState('en')
  const [isMuted, setIsMuted] = useState(false)
  const [isSpeakerOn, setIsSpeakerOn] = useState(true)
  const [voiceStatus, setVoiceStatus] = useState(null)
  const [error, setError] = useState(null)
  const [sessionId, setSessionId] = useState(null)
  const [interimTranscript, setInterimTranscript] = useState('')

  // ── Refs ────────────────────────────────────────────────────────────────────
  const recognitionRef = useRef(null)
  const timerRef = useRef(null)
  const stateRef = useRef(callState)
  const transcriptsEndRef = useRef(null)
  const ringtoneAudio = useRef(new Audio('/ringtone.mp3'))
  const connectAudio = useRef(new Audio('/connect.mp3'))
  const hangupAudio = useRef(new Audio('/hangup.mp3'))

  // Keep stateRef in sync
  useEffect(() => { stateRef.current = callState }, [callState])

  const isListeningRef = useRef(false)
  const languageRef = useRef(language)
  const sessionIdRef = useRef(sessionId)

  useEffect(() => { languageRef.current = language }, [language])
  useEffect(() => { sessionIdRef.current = sessionId }, [sessionId])

  // ── Microphone Permission ──────────────────────────────────────────────────
  const requestMicPermission = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        } 
      })
      stream.getTracks().forEach((t) => t.stop())
      setMicAuthorized(true)
      return true
    } catch (e) {
      console.warn('Microphone permission denied', e)
      setError('Microphone permission is required for the call.')
      setMicAuthorized(false)
      return false
    }
  }

  // Request mic on mount
  useEffect(() => { requestMicPermission() }, [])

  // Load voice config on mount
  useEffect(() => {
    getVoiceStatus().then(setVoiceStatus).catch(() => setVoiceStatus(null))
    if (!isSpeechRecognitionSupported()) {
      setError('Your browser does not support speech recognition. Use Chrome or Edge.')
    }
    return () => { stopTimer(); stopRecognition() }
  }, [])

  // Auto-scroll transcript
  useEffect(() => {
    transcriptsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [transcripts])

  // ── Timer ──────────────────────────────────────────────────────────────────
  const startTimer = () => {
    stopTimer()
    setDuration(0)
    timerRef.current = setInterval(() => setDuration((p) => p + 1), 1000)
  }
  const stopTimer = () => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null }
  }
  const formatDuration = (s) => {
    const m = Math.floor(s / 60).toString().padStart(2, '0')
    const sec = (s % 60).toString().padStart(2, '0')
    return `${m}:${sec}`
  }

  // ── Speech Recognition ─────────────────────────────────────────────────────
  const stopRecognition = () => {
    if (recognitionRef.current && isListeningRef.current) {
      try {
        recognitionRef.current.abort()
      } catch (_) {}
      isListeningRef.current = false
    }
  }

  const startRecognition = async () => {
    console.log('[RTC] startRecognition called, state:', stateRef.current)
    if (isMuted) return

    if (!micAuthorized) {
      const ok = await requestMicPermission()
      if (!ok) return
    }

    // Ensure we have a single persistent SpeechRecognition instance
    if (!recognitionRef.current) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      if (!SpeechRecognition) {
        setError('Speech recognition not supported.')
        return
      }

      const rec = new SpeechRecognition()
      rec.continuous = false
      rec.interimResults = true

      rec.onstart = () => {
        console.log('[RTC] recognition.onstart fired')
        isListeningRef.current = true
      }

      rec.onend = () => {
        console.log('[RTC] recognition.onend, state:', stateRef.current)
        isListeningRef.current = false

        // Auto-restart if we are still in listening or speaking state
        const s = stateRef.current
        if (s === 'listening' || s === 'speaking') {
          setTimeout(() => {
            if (stateRef.current === 'listening' || stateRef.current === 'speaking') {
              startRecognition()
            }
          }, 200)
        }
      }

      rec.onspeechstart = () => {
        console.log('[RTC] onspeechstart, state:', stateRef.current)
        if (stateRef.current === 'speaking') {
          console.log('[RTC] Barge-in! Cancelling bot audio.')
          cancelActiveAudio()
          setCallState('listening')
        }
      }

      rec.onresult = async (event) => {
        let finalStr = ''
        let interimStr = ''
        
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalStr += event.results[i][0].transcript
          } else {
            interimStr += event.results[i][0].transcript
          }
        }
        
        setInterimTranscript(interimStr)

        const text = finalStr.trim()
        if (!text) return

        if (stateRef.current === 'speaking') {
          cancelActiveAudio()
        }

        console.log('[RTC] User said:', text)
        setInterimTranscript('')
        stopRecognition() // stop listening while we process
        setCallState('processing')
        setTranscripts((prev) => [...prev, { role: 'user', text }])

        try {
          await handleBotTurn(text)
        } catch (err) {
          setError(err.message || 'Error processing response.')
          setCallState('listening')
          startRecognition()
        }
      }

      rec.onerror = (event) => {
        if (event.error !== 'no-speech' && event.error !== 'aborted') {
          console.error('[RTC] recognition error:', event.error)
        }
      }

      recognitionRef.current = rec
    }

    // Dynamically update the language lang code on the persistent instance
    recognitionRef.current.lang = languageRef.current === 'ml' ? 'ml-IN' : 'en-IN'

    // Start recognition only if it's not already active
    if (!isListeningRef.current) {
      try {
        recognitionRef.current.start()
        console.log('[RTC] recognition.start() succeeded')
      } catch (err) {
        console.error('[RTC] Failed to start recognition:', err)
      }
    }
  }

  // ── Mute Toggle ────────────────────────────────────────────────────────────
  const toggleMute = () => {
    setIsMuted((prev) => {
      const newMuted = !prev
      if (newMuted) {
        stopRecognition()
      } else if (stateRef.current === 'listening' || stateRef.current === 'speaking') {
        setTimeout(() => startRecognition(), 100)
      }
      return newMuted
    })
  }

  // ── Call Flow ──────────────────────────────────────────────────────────────
  const startCall = async () => {
    setError(null)
    setTranscripts([])
    setCallState('ringing')
    ringtoneAudio.current.loop = true
    ringtoneAudio.current.play().catch(() => {})
    startTimer()

    const newSessionId = `rtc-${Math.random().toString(36).substring(2, 11)}`
    setSessionId(newSessionId)

    try {
      const response = await simulateInboundCall({
        caller: 'Web Browser Client',
        text: '__START__',
        language,
        session_id: newSessionId,
      })

      ringtoneAudio.current.pause()
      ringtoneAudio.current.currentTime = 0
      connectAudio.current.play().catch(() => {})
      setCallState('connected')

      await playBotResponse(response.bot_response, response.audio_uri)
    } catch (err) {
      setError('Call setup failed. Make sure the backend is running.')
      ringtoneAudio.current.pause()
      hangUp()
    }
  }

  const handleBotTurn = async (userText) => {
    try {
      const response = await simulateInboundCall({
        caller: 'Web Browser Client',
        text: userText,
        language,
        session_id: sessionId,
      })

      await playBotResponse(response.bot_response, response.audio_uri)

      // Call NEVER auto-ends — only the user can hang up by pressing the red button.
      // The bot stays alive in 'open' state answering any further questions.
    } catch (err) {
      setError('Unable to reach server. Call disconnected.')
      hangUp()
    }
  }

  const playBotResponse = async (text, audioUri) => {
    setCallState('speaking')
    setTranscripts((prev) => [...prev, { role: 'bot', text }])

    // We cannot listen while the bot is speaking, otherwise the laptop microphone 
    // will pick up the bot's own voice from the speakers and interrupt itself!
    // So we wait until the audio finishes before listening again.

    // Play audio
    if (isSpeakerOn) {
      if (audioUri && audioUri.startsWith('data:')) {
        await speakAudioUriPromise(audioUri)
      } else {
        await speakTextWithBackendPromise(text, language)
      }
    } else {
      await new Promise((r) => setTimeout(r, Math.max(1500, text.length * 50)))
    }

    // After bot speech finishes, set state to listening
    await new Promise(resolve => setTimeout(resolve, 0));
    setCallState('listening');
    
    // Now that speaking is done, we can safely listen to the user
    startRecognition();
  }

  const hangUp = (completedGracefully = false) => {
    stopTimer()
    stopRecognition()
    cancelActiveAudio()
    setCallState('ended')
    hangupAudio.current.play().catch(() => {})
  }

  const resetCall = () => {
    setCallState('idle')
    setDuration(0)
    setTranscripts([])
    setError(null)
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className={`rtc rtc--${callState} ${callState === 'ringing' ? 'rtc--ringing' : ''}`}>
      {/* Decorative Blur Blobs */}
      <div className="rtc__bg-blob rtc__bg-blob--1" aria-hidden="true" />
      <div className="rtc__bg-blob rtc__bg-blob--2" aria-hidden="true" />

      {/* Header */}
      <header className="rtc__header">
        <div className="rtc__logo">
          <div className="rtc__logo-icon" style={{ width: 34, height: 34, borderRadius: 10, background: 'var(--grad-brand)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.1rem', boxShadow: 'var(--shadow-glow)' }}>🤖</div>
          <span>Bridgeon <span className="rtc__logo-gradient">Buddy</span></span>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <Link to="/bot" className="rtc__btn-back">💬 Chat Bot</Link>
          <Link to="/" className="rtc__btn-back">← Home</Link>
        </div>
      </header>

      {/* Main Content */}
      <div className="rtc__content">
        {/* Status */}
        <div className="rtc__status-panel">
          <h1 className="rtc__caller-name">Bridgeon Voice Assistant</h1>
          <div className="rtc__call-duration">
            {callState === 'idle' ? 'Ready to Call' : formatDuration(duration)}
          </div>
          <span className="rtc__status-badge">
            {callState === 'idle' && 'Idle'}
            {callState === 'ringing' && 'Ringing…'}
            {callState === 'connected' && 'Connected'}
            {callState === 'speaking' && '🔊 Bot Speaking'}
            {callState === 'listening' && (isMuted ? '🔇 Muted' : '🎙️ Listening…')}
            {callState === 'processing' && '🧠 Thinking…'}
            {callState === 'ended' && 'Call Ended'}
          </span>
        </div>

        {/* Orb */}
        <div className="rtc__orb-container">
          {callState !== 'idle' && callState !== 'ended' && (
            <>
              <div className="rtc__orb-pulse rtc__orb-pulse--1" />
              <div className="rtc__orb-pulse rtc__orb-pulse--2" />
            </>
          )}
          <div className="rtc__orb">
            {callState === 'idle' && '📞'}
            {callState === 'ringing' && '📞'}
            {callState === 'connected' && '✅'}
            {callState === 'speaking' && '🔊'}
            {callState === 'listening' && (isMuted ? '🔇' : '🎙️')}
            {callState === 'processing' && '🧠'}
            {callState === 'ended' && '🛑'}
          </div>
        </div>

        {/* Wave Visualizer */}
        {(callState === 'listening' || callState === 'speaking') && (
          <div className="rtc__waves" aria-hidden="true">
            <div className="rtc__wave-bar" />
            <div className="rtc__wave-bar" />
            <div className="rtc__wave-bar" />
            <div className="rtc__wave-bar" />
            <div className="rtc__wave-bar" />
            <div className="rtc__wave-bar" />
            <div className="rtc__wave-bar" />
          </div>
        )}

        {/* Transcript */}
        <div className="rtc__transcript-box glass">
          {transcripts.length === 0 ? (
            <div className="rtc__transcript-placeholder">
              <p>No active transcription.</p>
              <p style={{ fontSize: '0.8rem', opacity: 0.7 }}>
                Tap the call button below to start.
              </p>
            </div>
          ) : (
            transcripts.map((msg, i) => (
              <div key={i} className={`rtc__dialogue rtc__dialogue--${msg.role}`}>
                {msg.text}
              </div>
            ))
          )}
          {interimTranscript && (
            <div className="rtc__dialogue rtc__dialogue--user rtc__dialogue--interim">
              <i>{interimTranscript}</i>
            </div>
          )}
          <div ref={transcriptsEndRef} />
        </div>

        {/* Keyboard Input Fallback (Allows typing responses if SpeechRecognition is blocked/failing) */}
        {(callState === 'listening' || callState === 'speaking' || callState === 'processing') && (
          <form 
            onSubmit={(e) => {
              e.preventDefault();
              const text = e.target.elements.chatInput.value.trim();
              if (text) {
                e.target.elements.chatInput.value = '';
                cancelActiveAudio(); // interrupt bot if typing
                stopRecognition();
                setCallState('processing');
                setTranscripts((prev) => [...prev, { role: 'user', text }]);
                handleBotTurn(text);
              }
            }}
            className="rtc__text-input-form glass"
            style={{
              display: 'flex',
              gap: '0.5rem',
              width: '100%',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '30px',
              padding: '0.4rem 0.6rem 0.4rem 1.2rem',
              backdropFilter: 'blur(10px)',
              boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
            }}
          >
            <input
              name="chatInput"
              type="text"
              placeholder="Or type your response here..."
              style={{
                flex: 1,
                background: 'transparent',
                border: 'none',
                color: '#fff',
                fontSize: '0.85rem',
                outline: 'none',
              }}
              autoComplete="off"
            />
            <button 
              type="submit" 
              style={{
                background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
                border: 'none',
                color: '#fff',
                padding: '0.4rem 1.1rem',
                borderRadius: '20px',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
                boxShadow: '0 2px 8px rgba(124, 58, 237, 0.3)',
              }}
            >
              Send
            </button>
          </form>
        )}
      </div>

      {/* Controls — only 3 buttons: Mute, Call/Hangup, Speaker */}
      <div className="rtc__controls">
        {error && (
          <div className="bot-sim__error glass" style={{ margin: '0 0 1rem', width: '100%' }}>
            <strong>Notice:</strong> {error}
          </div>
        )}

        <div className="rtc__main-buttons">
          {/* Mute */}
          <button
            type="button"
            className={`rtc__btn-secondary ${isMuted ? 'rtc__btn-secondary--muted' : ''}`}
            onClick={toggleMute}
            disabled={callState === 'idle' || callState === 'ended'}
            title={isMuted ? 'Unmute' : 'Mute'}
          >
            {isMuted ? '🔇' : '🎙️'}
          </button>

          {/* Call / Hangup */}
          {callState === 'idle' || callState === 'ended' ? (
            <button
              type="button"
              className="rtc__btn-start"
              onClick={callState === 'ended' ? resetCall : startCall}
              title="Start call"
            >
              📞
            </button>
          ) : (
            <button
              type="button"
              className="rtc__btn-hangup"
              onClick={() => hangUp(false)}
              title="Hang up"
            >
              📞
            </button>
          )}

          {/* Speaker */}
          <button
            type="button"
            className={`rtc__btn-secondary ${isSpeakerOn ? 'rtc__btn-secondary--active' : ''}`}
            onClick={() => setIsSpeakerOn(!isSpeakerOn)}
            disabled={callState === 'idle' || callState === 'ended'}
            title={isSpeakerOn ? 'Speaker off' : 'Speaker on'}
          >
            {isSpeakerOn ? '🔊' : '🔈'}
          </button>
        </div>

        {/* Minimal settings — just language */}
        <div className="rtc__settings-bar">
          <label>
            Language:{' '}
            <select
              className="rtc__select"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              disabled={callState !== 'idle' && callState !== 'ended'}
            >
              <option value="en">English (en-IN)</option>
              <option value="ml">Malayalam (ml-IN)</option>
            </select>
          </label>
          <div style={{ width: '1px', height: '12px', background: 'rgba(255,255,255,0.1)' }} />
          <div>
            Voice:{' '}
            <span style={{ color: '#fff', fontWeight: 500 }}>
              {voiceStatus?.stt === 'sarvam' ? 'Sarvam AI' : voiceStatus?.stt === 'openai' ? 'OpenAI' : 'Browser'}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
