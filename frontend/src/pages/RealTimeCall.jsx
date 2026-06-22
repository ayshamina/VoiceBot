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
  // ── VoIP Call State ────────────────────────────────────────────────────
  const [micAuthorized, setMicAuthorized] = useState(false)
  const [callState, setCallState] = useState('idle') // idle | ringing | connected | speaking | listening | processing | ended
  const [duration, setDuration] = useState(0)
  const [transcripts, setTranscripts] = useState([])
  const [language, setLanguage] = useState('auto')
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
  const botSpokenTextRef = useRef('')

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
      setError('Microphone permission is required for browser calls.')
      setMicAuthorized(false)
      return false
    }
  }

  // Request mic on mount
  useEffect(() => { requestMicPermission() }, [])

  // Load voice config and check recognition support on mount
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

  // ── VoIP Call Timer ─────────────────────────────────────────────────────────
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

  // ── VoIP Speech Recognition ────────────────────────────────────────────────
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
        const interimText = interimStr.trim()
        const activeText = text || interimText
        
        if (!activeText) return

        // Auto-interruption logic: check if user spoke actual words while bot is talking
        if (stateRef.current === 'speaking') {
          const heard = activeText.toLowerCase()
          const botText = botSpokenTextRef.current || ''
          
          // Prevent bot from cutting off due to speaker echo of its own voice
          const heardWords = heard.split(/[^a-zA-Z\u0d00-\u0d7f]+/).filter(w => w.length > 2)
          let isEcho = false
          if (heardWords.length > 0) {
            const matches = heardWords.filter(w => botText.includes(w))
            if (botText.includes(heard) || (matches.length / heardWords.length) >= 0.4) {
              isEcho = true
            }
          }

          if (activeText.length > 2 && !isEcho) {
            console.log('[RTC] Auto-interrupted bot speech with heard text:', activeText)
            cancelActiveAudio()
            setCallState('listening')
            return // Stop execution; let user finish their sentence in listening state
          } else if (isEcho) {
            console.log('[RTC] Ignored echo of bot speech:', activeText)
            return // Skip processing this speech result
          }
        }

        // Only process final transcriptions
        if (!text) return

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
          setError(`Speech recognition error: ${event.error}. Please verify microphone access.`)
        }
      }

      recognitionRef.current = rec
    }

    recognitionRef.current.lang = (languageRef.current === 'ml' || languageRef.current === 'auto') ? 'ml-IN' : 'en-IN'

    if (!isListeningRef.current) {
      try {
        recognitionRef.current.start()
        console.log('[RTC] recognition.start() succeeded')
      } catch (err) {
        console.error('[RTC] Failed to start recognition:', err)
      }
    }
  }

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

  // ── VoIP Call Flow ──────────────────────────────────────────────────────────
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

      await playBotResponse(response.bot_response, response.audio_uri, response.language)
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

      await playBotResponse(response.bot_response, response.audio_uri, response.language)
    } catch (err) {
      setError('Unable to reach server. Call disconnected.')
      hangUp()
    }
  }

  const playBotResponse = async (text, audioUri, responseLanguage) => {
    setCallState('speaking')
    botSpokenTextRef.current = text.toLowerCase()
    setTranscripts((prev) => [...prev, { role: 'bot', text }])

    if (responseLanguage && responseLanguage !== language) {
      setLanguage(responseLanguage)
      languageRef.current = responseLanguage
    }

    // Start recognition immediately to listen for user interruption / barge-in
    startRecognition()

    if (isSpeakerOn) {
      if (audioUri && audioUri.startsWith('data:')) {
        await speakAudioUriPromise(audioUri)
      } else {
        await speakTextWithBackendPromise(text, responseLanguage || language)
      }
    } else {
      await new Promise((r) => setTimeout(r, Math.max(1500, text.length * 50)))
    }

    // If the session was not manually interrupted and is still in speaking state, return to listening
    if (stateRef.current === 'speaking') {
      setCallState('listening')
      startRecognition()
    }
  }

  const hangUp = () => {
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
          <div className="rtc__logo-icon">🤖</div>
          <span>Bridgeon <span className="rtc__logo-gradient">Buddy</span></span>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <Link to="/admin" className="rtc__btn-back">⚙️ Admin Panel</Link>
        </div>
      </header>

      {/* Center Layout for Single Calling Option */}
      <div className="rtc__layout-container rtc__layout-container--single">
        
        <section className="rtc__left-panel rtc__left-panel--single glass animate-fade-in-up">
          
          <div className="rtc__operator-header" style={{ width: '100%', textAlign: 'center', borderBottom: 'none' }}>
            <h3>🔴 Live AI Calling Assistant</h3>
            <p className="rtc__operator-subtitle" style={{ fontSize: '0.85rem' }}>
              Bilingual Voice Bot using ElevenLabs · Sarvam AI · LLMs
            </p>
          </div>

          {/* Call Status Display */}
          <div className="rtc__status-panel">
            <h2 className="rtc__caller-name">Bridgeon Voice Assistant</h2>
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

          {/* Call Orb */}
          <div className="rtc__orb-container">
            {callState !== 'idle' && callState !== 'ended' && (
              <>
                <div className="rtc__orb-pulse rtc__orb-pulse--1" />
                <div className="rtc__orb-pulse rtc__orb-pulse--2" />
              </>
            )}
            <div 
              className={`rtc__orb ${callState === 'speaking' ? 'rtc__orb--clickable' : ''}`}
              onClick={() => {
                if (callState === 'speaking') {
                  console.log('[RTC] Manual interrupt via Orb click')
                  cancelActiveAudio()
                  setCallState('listening')
                  startRecognition()
                }
              }}
              title={callState === 'speaking' ? 'Click to interrupt bot' : ''}
            >
              <span className="rtc__orb-emoji">
                {callState === 'idle' && '📞'}
                {callState === 'ringing' && '📞'}
                {callState === 'connected' && '✅'}
                {callState === 'speaking' && '🔊'}
                {callState === 'listening' && (isMuted ? '🔇' : '🎙️')}
                {callState === 'processing' && '🧠'}
                {callState === 'ended' && '🛑'}
              </span>
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

          {/* Transcripts Panel */}
          <div className="rtc__transcript-box">
            {transcripts.length === 0 ? (
              <div className="rtc__transcript-placeholder">
                <span className="placeholder-icon">🎙️</span>
                <p>No active transcription.</p>
                <p style={{ fontSize: '0.82rem', opacity: 0.7 }}>
                  Click the green phone icon below to start a live voice session.
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

          {/* Controls */}
          <div className="rtc__controls" style={{ paddingBottom: '0.5rem' }}>
            {error && (
              <div className="bot-sim__error" style={{ marginBottom: '1rem', width: '100%' }}>
                <strong>Notice:</strong> {error}
              </div>
            )}

            {(callState === 'connected' || callState === 'speaking' || callState === 'listening') && (
              <div style={{ fontSize: '0.78rem', color: '#64748b', textAlign: 'center', marginBottom: '0.8rem', width: '100%', opacity: 0.85 }}>
                🎧 <i>Tip: Use headphones to get the best voice interruption experience.</i>
              </div>
            )}

            <div className="rtc__main-buttons">
              <button
                type="button"
                className={`rtc__btn-secondary ${isMuted ? 'rtc__btn-secondary--muted' : ''}`}
                onClick={toggleMute}
                disabled={callState === 'idle' || callState === 'ended'}
                title={isMuted ? 'Unmute microphone' : 'Mute microphone'}
              >
                {isMuted ? '🔇' : '🎙️'}
              </button>

              {callState === 'idle' || callState === 'ended' ? (
                <button
                  type="button"
                  className="rtc__btn-start"
                  onClick={callState === 'ended' ? resetCall : startCall}
                  title="Start voice session"
                >
                  📞
                </button>
              ) : (
                <button
                  type="button"
                  className="rtc__btn-hangup"
                  onClick={hangUp}
                  title="Hang up call"
                >
                  📞
                </button>
              )}

              <button
                type="button"
                className={`rtc__btn-secondary ${isSpeakerOn ? 'rtc__btn-secondary--active' : ''}`}
                onClick={() => setIsSpeakerOn(!isSpeakerOn)}
                disabled={callState === 'idle' || callState === 'ended'}
                title={isSpeakerOn ? 'Speaker output off' : 'Speaker output on'}
              >
                {isSpeakerOn ? '🔊' : '🔈'}
              </button>
            </div>

            <div className="rtc__settings-bar">
              <div>
                Language: <span style={{ color: '#fff', fontWeight: 600 }}>🤖 Bilingual Auto-Detect</span>
              </div>
              <div className="rtc__dot-divider" />
              <div>
                Voice Backend: <span style={{ color: '#fff', fontWeight: 600 }}>
                  {voiceStatus?.elevenlabs_configured ? 'ElevenLabs' : voiceStatus?.sarvam_configured ? 'Sarvam AI' : 'Browser/LLM'}
                </span>
              </div>
            </div>
          </div>

        </section>

      </div>
    </div>
  )
}
