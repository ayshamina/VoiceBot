import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { chatBot, resetChatSession, getVoiceStatus } from '../services/api'
import { useHealth } from '../hooks/useHealth'
import {
  createSpeechRecognition,
  isSpeechRecognitionSupported,
  speakTextWithBackendPromise,
  cancelActiveAudio,
} from '../hooks/useSpeech'
import './BotSimulator.css'

const createSessionId = () => {
  if (window.crypto?.randomUUID) return window.crypto.randomUUID()
  return `session-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}

const QUICK_REPLIES = [
  '🎓 Tell me about courses',
  '💰 What are the fees?',
  '📅 When does the batch start?',
  '📞 I want a callback',
  '🌐 Do you teach online?',
]

const initialMessages = [{ id: 'intro', role: 'system', text: 'Starting bot session…' }]

export default function BotSimulator() {
  const { error: healthError } = useHealth()
  const [sessionId, setSessionId]     = useState(() => createSessionId())
  const [messages, setMessages]       = useState(initialMessages)
  const [input, setInput]             = useState('')
  const [status, setStatus]           = useState('pending')
  const [error, setError]             = useState(null)
  const [started, setStarted]         = useState(false)
  const [leadId, setLeadId]           = useState(null)
  const [languageMode, setLanguageMode] = useState('en')
  const [botLanguage, setBotLanguage] = useState('en')
  const [isListening, setIsListening] = useState(false)
  const [isSpeakerOn, setIsSpeakerOn] = useState(true)
  const chatEndRef   = useRef(null)
  const startedRef   = useRef(false)
  const recognitionRef = useRef(null)
  const langInitRef  = useRef(false)

  const lastBotMessage = useMemo(
    () => messages.filter(m => m.role === 'bot').slice(-1)[0],
    [messages],
  )

  const appendMessage = (role, text) => {
    setMessages(prev => [
      ...prev.filter(m => m.id !== 'intro'),
      { id: `${role}-${prev.length}-${Date.now()}`, role, text },
    ])
  }

  const startSession = async (session = sessionId, langMode = languageMode) => {
    setStatus('pending')
    setError(null)
    try {
      const resolvedLang = langMode === 'auto' ? 'en' : langMode
      const res = await chatBot({ text: '__START__', session_id: session, language: resolvedLang })
      setStarted(true)
      appendMessage('bot', res.response_text)
      setBotLanguage(resolvedLang)
      if (isSpeakerOn) speakTextWithBackendPromise(res.response_text, resolvedLang)
    } catch (err) {
      setError(err.message || 'Unable to start bot simulation. Is the backend running?')
      setStarted(false)
    } finally {
      setStatus('idle')
    }
  }

  useEffect(() => {
    getVoiceStatus().catch(() => null)
    return () => {
      if (recognitionRef.current) { try { recognitionRef.current.abort() } catch (e) {} }
      cancelActiveAudio()
    }
  }, [])

  useEffect(() => {
    if (startedRef.current) return
    startedRef.current = true
    startSession()
  }, [])

  useEffect(() => {
    if (!langInitRef.current) { langInitRef.current = true; return }
    cancelActiveAudio()
    const nextSession = createSessionId()
    setSessionId(nextSession)
    setMessages([{ id: 'intro', role: 'system', text: `Switching to ${languageMode === 'ml' ? 'Malayalam' : 'English'}…` }])
    setInput('')
    setStarted(false)
    setLeadId(null)
    setBotLanguage(languageMode === 'auto' ? 'en' : languageMode)
    startedRef.current = false
    startSession(nextSession, languageMode)
    startedRef.current = true
  }, [languageMode])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleListen = async () => {
    setError(null)
    const lang = languageMode === 'auto' ? botLanguage : languageMode
    if (isListening) {
      if (recognitionRef.current) { try { recognitionRef.current.abort() } catch (e) {} ; recognitionRef.current = null }
      setIsListening(false)
      return
    }
    if (!isSpeechRecognitionSupported()) {
      setError('Voice input not supported. Please use Chrome or Edge.')
      return
    }
    const recognition = createSpeechRecognition(lang)
    if (!recognition) return
    setIsListening(true)
    recognitionRef.current = recognition
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results).map(r => r[0].transcript).join('')
      setInput(transcript)
      setIsListening(false)
      recognitionRef.current = null
    }
    recognition.onerror = (event) => {
      if (event.error !== 'no-speech' && event.error !== 'aborted') setError('Could not capture voice. Check mic permissions.')
      setIsListening(false)
      recognitionRef.current = null
    }
    recognition.onend = () => { setIsListening(false); recognitionRef.current = null }
    recognition.start()
  }

  const handleSend = async (event, overrideText) => {
    if (event) event.preventDefault()
    const userText = (overrideText || input).trim()
    if (!userText || status === 'pending') return
    cancelActiveAudio()
    if (!started) await startSession()
    appendMessage('user', userText)
    setInput('')
    setStatus('pending')
    setError(null)
    try {
      const resolvedLang = languageMode === 'auto' ? 'en' : languageMode
      const res = await chatBot({ text: userText, session_id: sessionId, language: resolvedLang })
      appendMessage('bot', res.response_text)
      if (res.lead_id) setLeadId(res.lead_id)
      setBotLanguage(resolvedLang)
      if (isSpeakerOn) speakTextWithBackendPromise(res.response_text, resolvedLang)
    } catch (err) {
      setError(err.message || 'Bot request failed.')
    } finally {
      setStatus('idle')
    }
  }

  const handleReset = async () => {
    if (status === 'pending') return
    setStatus('pending')
    setError(null)
    try {
      cancelActiveAudio()
      await resetChatSession({ session_id: sessionId })
      const next = createSessionId()
      setSessionId(next)
      setMessages([{ id: 'intro', role: 'system', text: 'Starting new session…' }])
      setInput('')
      setStarted(false)
      setLeadId(null)
      setBotLanguage(languageMode === 'auto' ? 'en' : languageMode)
      startedRef.current = false
      await startSession(next, languageMode)
      startedRef.current = true
    } catch (err) {
      setError(err.message || 'Could not reset the session.')
      setStatus('idle')
    }
  }

  return (
    <div className="bot-sim">
      {/* ── Header ──────────────────────────────────────────────────── */}
      <header className="bot-sim__header">
        <div className="bot-sim__brand">
          <div className="bot-sim__brand-icon">🤖</div>
          <div>
            <div className="bot-sim__brand-name">
              Bridgeon <span className="gradient-text">Buddy</span>
            </div>
            <div className="bot-sim__eyebrow">Chat Bot Simulator · v4.0</div>
          </div>
        </div>

        <div className="bot-sim__actions">
          {/* Language toggle */}
          <div className="bot-sim__lang-toggle">
            <button
              className={`bot-sim__lang-btn ${languageMode === 'en' ? 'active' : ''}`}
              onClick={() => setLanguageMode('en')}
            >🇺🇸 EN</button>
            <button
              className={`bot-sim__lang-btn ${languageMode === 'ml' ? 'active' : ''}`}
              onClick={() => setLanguageMode('ml')}
            >🇮🇳 ML</button>
          </div>

          {/* Speaker toggle */}
          <button
            className="btn btn--ghost"
            onClick={() => { const v = !isSpeakerOn; setIsSpeakerOn(v); if (!v) cancelActiveAudio() }}
            title={isSpeakerOn ? 'Mute bot voice' : 'Unmute bot voice'}
            style={{ fontSize: '1.1rem', padding: '0.5rem 0.75rem' }}
          >
            {isSpeakerOn ? '🔊' : '🔇'}
          </button>

          <button className="btn btn--ghost" onClick={handleReset} disabled={status === 'pending'} style={{ fontSize: '0.85rem' }}>
            🔄 New Session
          </button>
          <Link to="/telephony" className="btn btn--ghost" style={{ fontSize: '0.85rem' }}>📞 Voice Sim</Link>
          <Link to="/" className="btn btn--ghost" style={{ fontSize: '0.85rem' }}>← Home</Link>
        </div>
      </header>

      {/* ── Info bar ────────────────────────────────────────────────── */}
      <div className="bot-sim__info-bar">
        <div className="bot-sim__info-item">
          <span>Backend</span>
          <code style={{ color: healthError ? 'var(--clr-danger)' : '#34d399' }}>
            {healthError ? '🔴 Offline' : '🟢 Connected'}
          </code>
        </div>
        <div className="bot-sim__info-item">
          <span>Session</span>
          <code>{sessionId.slice(0, 16)}…</code>
        </div>
        <div className="bot-sim__info-item">
          <span>Language</span>
          <code>{botLanguage === 'ml' ? '🇮🇳 Malayalam' : '🇺🇸 English'}</code>
        </div>
        {leadId && (
          <div className="bot-sim__info-item">
            <span>Lead</span>
            <code style={{ color: '#34d399' }}>✅ Saved #{leadId}</code>
          </div>
        )}
        <div className="bot-sim__info-item" style={{ marginLeft: 'auto' }}>
          <span className={`badge ${status === 'pending' ? 'badge--warning' : started ? 'badge--ok' : 'badge--info'}`}>
            {status === 'pending' ? '⏳ Processing…' : started ? '🟢 Live session' : '🔵 Connecting…'}
          </span>
        </div>
      </div>

      {/* ── Error ───────────────────────────────────────────────────── */}
      {(error || healthError) && (
        <div className="bot-sim__error" role="alert">
          <strong>⚠️ Error:</strong>{' '}
          {error || healthError}
          {healthError && (
            <p style={{ marginTop: '0.5rem', fontSize: '0.85rem', opacity: 0.8 }}>
              Start backend: <code>cd backend && uvicorn main:app --reload</code>
            </p>
          )}
        </div>
      )}

      {/* ── Chat area ───────────────────────────────────────────────── */}
      <main className="bot-sim__main">
        <div className="bot-sim__panel">
          {/* Panel header */}
          <div className="bot-sim__panel-header">
            <div className="bot-sim__panel-avatar">
              <div className="bot-sim__avatar-orb">
                🤖
                <div className="bot-sim__avatar-status" />
              </div>
              <div>
                <div className="bot-sim__avatar-name">Bridgeon Buddy</div>
                <div className="bot-sim__avatar-sub">AI Voice Assistant · {botLanguage === 'ml' ? 'Malayalam' : 'English'}</div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              {status === 'pending' && (
                <div style={{ display: 'flex', gap: 4 }}>
                  <div className="typing-dot" style={{ background: 'var(--clr-brand-light)' }} />
                  <div className="typing-dot" style={{ background: 'var(--clr-brand-light)', animationDelay: '0.2s' }} />
                  <div className="typing-dot" style={{ background: 'var(--clr-brand-light)', animationDelay: '0.4s' }} />
                </div>
              )}
            </div>
          </div>

          {/* Chat log */}
          <div className="chat-log">
            {messages.map((msg) => (
              <div key={msg.id} className={`message message--${msg.role}`}>
                {msg.role !== 'system' && (
                  <div className="message__avatar">
                    {msg.role === 'bot' ? '🤖' : '👤'}
                  </div>
                )}
                <div className="message__bubble">{msg.text}</div>
              </div>
            ))}
            {status === 'pending' && started && (
              <div className="message message--bot">
                <div className="message__avatar">🤖</div>
                <div className="message__bubble">
                  <div className="typing-dots">
                    <div className="typing-dot" />
                    <div className="typing-dot" />
                    <div className="typing-dot" />
                  </div>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Lead saved */}
          {leadId && (
            <div className="bot-sim__lead-banner">
              ✅ Lead successfully captured — ID #{leadId}
            </div>
          )}

          {/* Quick replies */}
          <div className="bot-sim__quick-replies">
            {QUICK_REPLIES.map((chip) => (
              <button
                key={chip}
                className="bot-sim__quick-chip"
                onClick={() => handleSend(null, chip)}
                disabled={status === 'pending'}
              >
                {chip}
              </button>
            ))}
          </div>

          {/* Input row */}
          <form className="bot-sim__input-row" onSubmit={handleSend}>
            <button
              type="button"
              className={`bot-sim__mic-btn ${isListening ? 'recording' : ''}`}
              onClick={handleListen}
              disabled={status === 'pending' || Boolean(healthError)}
              title={isListening ? 'Listening… click to stop' : 'Voice input'}
            >
              {isListening ? '⏹️' : '🎙️'}
            </button>
            <input
              type="text"
              placeholder={languageMode === 'ml' ? 'ഒരു സന്ദേശം ടൈപ്പ് ചെയ്യൂ…' : 'Type your message… e.g. Tell me about MERN courses'}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={status === 'pending' || Boolean(healthError)}
              aria-label="Chat input"
              autoComplete="off"
            />
            <button
              type="submit"
              className="bot-sim__send-btn"
              disabled={!input.trim() || status === 'pending' || Boolean(healthError)}
              title="Send message"
            >
              ➤
            </button>
          </form>
        </div>
      </main>
    </div>
  )
}
