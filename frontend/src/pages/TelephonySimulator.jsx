import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  simulateInboundCall,
  initiateOutboundCall,
  getTelephonyCalls,
  getVoiceStatus,
  getTelephonyStatus,
  transcribeAudio,
} from '../services/api'
import { useHealth } from '../hooks/useHealth'
import {
  blobToBase64,
  createSpeechRecognition,
  isSpeechRecognitionSupported,
  recordAudioBlob,
  speakTextWithBackend,
} from '../hooks/useSpeech'
import './BotSimulator.css'

const initialInboundForm = {
  caller: '+91 ',
  text: 'Hi, can you tell me about the Python course fee?',
  language: 'en',
  audio_source: '',
}

const initialOutboundForm = {
  to_number: '+91 ',
  campaign_message: '',
  language: 'en',
  agent_name: 'Bridgeon Admissions',
}

export default function TelephonySimulator() {
  const { error: healthError } = useHealth()
  const [activeTab, setActiveTab] = useState('inbound') // inbound | outbound

  // Inbound state
  const [inboundForm, setInboundForm] = useState(initialInboundForm)
  const [inboundResult, setInboundResult] = useState(null)
  const [inboundStatus, setInboundStatus] = useState('ready')

  // Outbound state
  const [outboundForm, setOutboundForm] = useState(initialOutboundForm)
  const [outboundResult, setOutboundResult] = useState(null)
  const [outboundStatus, setOutboundStatus] = useState('ready')

  // Shared state
  const [calls, setCalls] = useState([])
  const [error, setError] = useState(null)
  const [inputMode, setInputMode] = useState('text')
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [voiceStatus, setVoiceStatus] = useState(null)
  const [telephonyStatus, setTelephonyStatus] = useState(null)
  const [ttsProvider, setTtsProvider] = useState('browser')

  useEffect(() => {
    loadCallHistory()
    getVoiceStatus()
      .then(setVoiceStatus)
      .catch(() => setVoiceStatus(null))
    getTelephonyStatus()
      .then(setTelephonyStatus)
      .catch(() => setTelephonyStatus(null))
  }, [])

  const loadCallHistory = async () => {
    setError(null)
    try {
      const data = await getTelephonyCalls()
      setCalls(data)
    } catch (err) {
      setError(err.message || 'Failed to load telephony history.')
    }
  }

  // ── Voice input helpers ──────────────────────────────────────────────────
  const handleListen = async () => {
    setError(null)

    if (voiceStatus?.sarvam_configured || voiceStatus?.openai_configured) {
      setIsListening(true)
      try {
        const blob = await recordAudioBlob(15000)
        const audioBase64 = await blobToBase64(blob)
        const result = await transcribeAudio(audioBase64, inboundForm.language)
        setInboundForm(prev => ({ ...prev, text: result.transcript }))
      } catch (err) {
        setError(err.message || 'Server voice capture failed.')
      } finally {
        setIsListening(false)
      }
      return
    }

    if (!isSpeechRecognitionSupported()) {
      setError('Voice input not supported. Use Chrome/Edge or enable Sarvam AI in .env.')
      return
    }

    const recognition = createSpeechRecognition(inboundForm.language)
    if (!recognition) return

    setIsListening(true)
    recognition.onresult = (event) => {
      setInboundForm(prev => ({ ...prev, text: event.results[0][0].transcript }))
      setIsListening(false)
    }
    recognition.onerror = () => {
      setError('Could not capture voice. Check microphone permissions.')
      setIsListening(false)
    }
    recognition.onend = () => setIsListening(false)
    recognition.start()
  }

  const handleSpeakResponse = async (text, language) => {
    setIsSpeaking(true)
    const result = await speakTextWithBackend(text, language)
    setTtsProvider(result.provider)
    if (!result.ok) {
      setError('TTS unavailable. Add SARVAM_API_KEY to backend/.env.')
    }
    setIsSpeaking(false)
  }

  // ── Inbound call submit ──────────────────────────────────────────────────
  const handleInboundSubmit = async (event) => {
    event.preventDefault()
    setInboundStatus('pending')
    setError(null)

    const payload = {
      caller: inboundForm.caller,
      language: inboundForm.language,
    }

    if (inputMode === 'text') {
      if (!inboundForm.text.trim()) {
        setError('Enter what the caller said, or use voice input.')
        setInboundStatus('ready')
        return
      }
      payload.text = inboundForm.text
    } else if (inboundForm.audio_source.trim()) {
      payload.audio_source = inboundForm.audio_source
    } else if (inboundForm.text.trim()) {
      payload.text = inboundForm.text
    } else {
      setError('Provide caller speech via voice capture, text, or an audio source token.')
      setInboundStatus('ready')
      return
    }

    try {
      const response = await simulateInboundCall(payload)
      setInboundResult(response)
      await loadCallHistory()
      handleSpeakResponse(response.bot_response, response.language)
    } catch (err) {
      setError(err.message || 'Unable to simulate call. Is the backend running on port 8000?')
      setInboundResult(null)
    } finally {
      setInboundStatus('ready')
    }
  }

  // ── Outbound call submit ─────────────────────────────────────────────────
  const handleOutboundSubmit = async (event) => {
    event.preventDefault()
    setOutboundStatus('pending')
    setError(null)

    if (!outboundForm.to_number.trim() || outboundForm.to_number.trim() === '+91 ') {
      setError('Enter a valid phone number for the outbound call.')
      setOutboundStatus('ready')
      return
    }

    try {
      const payload = {
        to_number: outboundForm.to_number.trim(),
        language: outboundForm.language,
        agent_name: outboundForm.agent_name,
      }
      if (outboundForm.campaign_message.trim()) {
        payload.campaign_message = outboundForm.campaign_message.trim()
      }
      const response = await initiateOutboundCall(payload)
      setOutboundResult(response)
      await loadCallHistory()
    } catch (err) {
      setError(err.message || 'Failed to initiate outbound call.')
      setOutboundResult(null)
    } finally {
      setOutboundStatus('ready')
    }
  }

  const recentCall = useMemo(() => calls[0], [calls])
  const isExotelActive = telephonyStatus?.exotel_configured || false
  const isSarvamActive = voiceStatus?.sarvam_configured || false

  return (
    <div className="bot-sim">
      <header className="bot-sim__header">
        <div className="bot-sim__brand">
          <div className="bot-sim__brand-icon">📞</div>
          <div>
            <div className="bot-sim__brand-name">
              Bridgeon <span className="gradient-text">Telephony</span>
            </div>
            <div className="bot-sim__eyebrow">Exotel + Sarvam AI · Production</div>
          </div>
        </div>
        <div className="bot-sim__actions">
          <Link to="/call" className="btn btn--primary" style={{ fontSize: '0.85rem' }}>📞 Real-Time Call</Link>
          <Link to="/bot" className="btn btn--ghost" style={{ fontSize: '0.85rem' }}>💬 Chat Bot</Link>
          <Link to="/admin" className="btn btn--ghost" style={{ fontSize: '0.85rem' }}>⚙️ Admin</Link>
          <Link to="/" className="btn btn--ghost" style={{ fontSize: '0.85rem' }}>← Home</Link>
        </div>
      </header>

      {/* Status bar */}
      <div className="bot-sim__info-bar">
        <div className="bot-sim__info-item">
          <span>Backend</span>
          <code style={{ color: healthError ? 'var(--clr-danger)' : 'var(--clr-teal)' }}>
            {healthError ? '🔴 Offline' : '🟢 Connected'}
          </code>
        </div>
        <div className="bot-sim__info-item">
          <span>Sarvam AI (STT/TTS)</span>
          <code style={{ color: isSarvamActive ? 'var(--clr-teal)' : '#f59e0b' }}>
            {isSarvamActive ? '🟢 Active' : '🟡 Not configured'}
          </code>
        </div>
        <div className="bot-sim__info-item">
          <span>Exotel (Calls)</span>
          <code style={{ color: isExotelActive ? 'var(--clr-teal)' : '#f59e0b' }}>
            {isExotelActive ? '🟢 Active' : '🟡 Simulation mode'}
          </code>
        </div>
        <div className="bot-sim__info-item">
          <span>Last Call ID</span>
          <code>{recentCall ? recentCall.call_id : 'None yet'}</code>
        </div>
        <div className="bot-sim__info-item">
          <span>TTS</span>
          <code>{ttsProvider === 'openai' ? 'OpenAI' : ttsProvider === 'sarvam' ? 'Sarvam AI' : 'Browser'}</code>
        </div>
      </div>

      {/* Setup notice when Exotel not configured */}
      {!isExotelActive && (
        <div className="bot-sim__setup-notice">
          <strong>⚙️ Setup Required for Real Calls</strong>
          <p style={{ margin: 0, opacity: 0.85, fontSize: '0.875rem' }}>
            To enable real phone calls, add these to <code>backend/.env</code>:
          </p>
          <code style={{ display: 'block', background: 'rgba(0,0,0,0.3)', padding: '0.75rem', borderRadius: '6px', fontSize: '0.8rem', lineHeight: 1.7 }}>
            SARVAM_API_KEY=your-key &nbsp;# from dashboard.sarvam.ai (free)<br/>
            EXOTEL_ACCOUNT_SID=your-sid<br/>
            EXOTEL_API_KEY=your-api-key &nbsp;# from exotel.com<br/>
            EXOTEL_API_TOKEN=your-api-token<br/>
            EXOTEL_PHONE_NUMBER=+91XXXXXXXXXX<br/>
            BACKEND_PUBLIC_URL=https://your-ngrok-url.ngrok.app
          </code>
          <p style={{ margin: 0, opacity: 0.7, fontSize: '0.8rem' }}>
            In simulation mode, calls are processed locally without dialing real numbers.
          </p>
        </div>
      )}

      {(error || healthError) && (
        <div className="bot-sim__error" role="alert">
          <strong>Error:</strong> {error || healthError}
        </div>
      )}


      {/* Tab switcher */}
      <div className="telephony-tabs glass" style={{
        display: 'flex',
        gap: '0',
        margin: '1.5rem 0 0',
        borderRadius: '12px',
        overflow: 'hidden',
        border: '1px solid rgba(255,255,255,0.1)',
      }}>
        <button
          className={activeTab === 'inbound' ? 'btn btn--primary' : 'btn btn--ghost'}
          style={{ flex: 1, borderRadius: '0', padding: '0.875rem' }}
          onClick={() => setActiveTab('inbound')}
        >
          📥 Inbound Call
        </button>
        <button
          className={activeTab === 'outbound' ? 'btn btn--primary' : 'btn btn--ghost'}
          style={{ flex: 1, borderRadius: '0', padding: '0.875rem' }}
          onClick={() => setActiveTab('outbound')}
        >
          📤 Outbound Call
        </button>
        <button
          className={activeTab === 'history' ? 'btn btn--primary' : 'btn btn--ghost'}
          style={{ flex: 1, borderRadius: '0', padding: '0.875rem' }}
          onClick={() => setActiveTab('history')}
        >
          📋 Call History
        </button>
      </div>

      <main className="bot-sim__main">

        {/* ── INBOUND CALL TAB ─────────────────────────────────────────────── */}
        {activeTab === 'inbound' && (
          <div className="bot-sim__panel glass">
            <div className="bot-sim__panel-header">
              <h2>📥 Receive Inbound Call</h2>
              <span className="badge badge--loading">
                {inboundStatus === 'pending' ? 'Processing…' : isExotelActive ? '🟢 Exotel active' : '⚡ Simulation'}
              </span>
            </div>

            {isExotelActive && (
              <div style={{ padding: '0.75rem 1rem', background: 'rgba(34,197,94,0.1)', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.875rem' }}>
                <strong>🟢 Real inbound calls active.</strong> Configure your Exotel App's ExoML URL to:<br/>
                <code style={{ display: 'block', marginTop: '0.35rem', wordBreak: 'break-all' }}>
                  {`${window.location.origin.replace('5173', '8000')}/api/v1/telephony/inbound/webhook`}
                </code>
              </div>
            )}

            <p style={{ opacity: 0.7, marginBottom: '1rem', fontSize: '0.875rem' }}>
              {isExotelActive
                ? 'When someone calls your Exotel number, the bot answers automatically. Use this form to test the bot response.'
                : 'Simulate an inbound call. When Exotel is configured, real callers will be handled automatically via webhook.'}
            </p>

            <form className="bot-sim__input-row telephony-form" onSubmit={handleInboundSubmit}>
              <label>
                Caller Phone Number
                <input
                  type="text"
                  value={inboundForm.caller}
                  onChange={e => setInboundForm({ ...inboundForm, caller: e.target.value })}
                  placeholder="+91 98xxxx xxxx"
                  required
                />
              </label>

              <label>
                Caller Language
                <select
                  value={inboundForm.language}
                  onChange={e => setInboundForm({ ...inboundForm, language: e.target.value })}
                >
                  <option value="en">English</option>
                  <option value="ml">Malayalam</option>
                </select>
              </label>

              <label>
                Input Mode
                <select value={inputMode} onChange={e => {
                  setInputMode(e.target.value)
                  setInboundForm(prev => ({
                    ...prev,
                    text: e.target.value === 'text' ? prev.text : '',
                    audio_source: '',
                  }))
                }}>
                  <option value="text">📝 Type caller speech</option>
                  <option value="voice">🎤 Speak via microphone (Sarvam AI STT)</option>
                  <option value="audio">🎵 Audio source token</option>
                </select>
              </label>

              {inputMode === 'text' && (
                <label>
                  What the caller said
                  <input
                    type="text"
                    value={inboundForm.text}
                    onChange={e => setInboundForm({ ...inboundForm, text: e.target.value })}
                    placeholder="e.g. I want to know about Python course fees"
                    required
                  />
                </label>
              )}

              {inputMode === 'voice' && (
                <label>
                  Caller speech (microphone → Sarvam AI STT)
                  <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.35rem' }}>
                    <input
                      type="text"
                      value={inboundForm.text}
                      onChange={e => setInboundForm({ ...inboundForm, text: e.target.value })}
                      placeholder="Click Listen and speak, or type here"
                    />
                    <button
                      type="button"
                      className="btn btn--ghost"
                      onClick={handleListen}
                      disabled={isListening || inboundStatus === 'pending'}
                    >
                      {isListening ? '🎤 Listening…' : '🎤 Listen'}
                    </button>
                  </div>
                </label>
              )}

              {inputMode === 'audio' && (
                <label>
                  Audio Source Token
                  <input
                    type="text"
                    value={inboundForm.audio_source}
                    onChange={e => setInboundForm({ ...inboundForm, audio_source: e.target.value })}
                    placeholder="audio-token-abc123"
                    required
                  />
                </label>
              )}

              <button
                className="btn btn--primary"
                type="submit"
                disabled={inboundStatus === 'pending' || Boolean(healthError)}
              >
                {inboundStatus === 'pending' ? '📞 Processing…' : '📞 Simulate Inbound Call'}
              </button>
            </form>

            {inboundResult && (
              <div className="bot-sim__result glass">
                <h3>📞 Call Completed</h3>
                <div className="call-details">
                  <p><strong>Call ID:</strong> <code>{inboundResult.call_id}</code></p>
                  <p><strong>Caller:</strong> {inboundResult.caller}</p>
                  <p><strong>Language:</strong> {inboundResult.language === 'ml' ? 'Malayalam' : 'English'}</p>
                  <p><strong>Outcome:</strong> <span style={{ color: 'var(--clr-teal)' }}>{inboundResult.outcome}</span></p>

                  <div className="call-section">
                    <h4>🎤 Caller Speech (STT Output)</h4>
                    <p className="transcript">{inboundResult.transcript}</p>
                  </div>

                  <div className="call-section">
                    <h4>🤖 Bot Response</h4>
                    <p className="response">{inboundResult.bot_response}</p>
                    <button
                      type="button"
                      className="btn btn--ghost"
                      style={{ marginTop: '0.75rem' }}
                      onClick={() => handleSpeakResponse(inboundResult.bot_response, inboundResult.language)}
                      disabled={isSpeaking}
                    >
                      {isSpeaking ? '🔊 Speaking…' : '🔊 Play Sarvam AI voice'}
                    </button>
                  </div>

                  {inboundResult.audio_uri && inboundResult.audio_uri.startsWith('data:') && (
                    <div className="call-section">
                      <h4>🔊 Audio Playback</h4>
                      <audio controls src={inboundResult.audio_uri} style={{ width: '100%', marginTop: '0.5rem' }}>
                        Your browser does not support audio.
                      </audio>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── OUTBOUND CALL TAB ─────────────────────────────────────────────── */}
        {activeTab === 'outbound' && (
          <div className="bot-sim__panel glass">
            <div className="bot-sim__panel-header">
              <h2>📤 Place Outbound Call</h2>
              <span className="badge" style={{
                background: isExotelActive ? 'rgba(34,197,94,0.2)' : 'rgba(245,158,11,0.2)',
                color: isExotelActive ? '#22c55e' : '#f59e0b',
              }}>
                {isExotelActive ? '🟢 Real call via Exotel' : '⚡ Simulation mode'}
              </span>
            </div>

            <p style={{ opacity: 0.7, marginBottom: '1.25rem', fontSize: '0.875rem' }}>
              {isExotelActive
                ? 'This will dial the target phone number via Exotel. The bot will speak the campaign message when the recipient answers.'
                : 'Exotel not configured — this will run in simulation mode. Add Exotel credentials to backend/.env for real calls.'}
            </p>

            <form className="bot-sim__input-row telephony-form" onSubmit={handleOutboundSubmit}>
              <label>
                Target Phone Number
                <input
                  type="tel"
                  value={outboundForm.to_number}
                  onChange={e => setOutboundForm({ ...outboundForm, to_number: e.target.value })}
                  placeholder="+91 98xxxx xxxx"
                  required
                />
              </label>

              <label>
                Call Language
                <select
                  value={outboundForm.language}
                  onChange={e => setOutboundForm({ ...outboundForm, language: e.target.value })}
                >
                  <option value="en">English</option>
                  <option value="ml">Malayalam</option>
                </select>
              </label>

              <label>
                Agent Name (shown to recipient)
                <input
                  type="text"
                  value={outboundForm.agent_name}
                  onChange={e => setOutboundForm({ ...outboundForm, agent_name: e.target.value })}
                  placeholder="e.g. Bridgeon Admissions"
                />
              </label>

              <label>
                Opening Campaign Message (optional)
                <textarea
                  value={outboundForm.campaign_message}
                  onChange={e => setOutboundForm({ ...outboundForm, campaign_message: e.target.value })}
                  rows={3}
                  placeholder="Leave empty to use the default greeting from settings. Or customize: 'Hello! This is Priya from Bridgeon Skillversity. We wanted to share an exciting opportunity with you...'"
                />
              </label>

              <button
                className="btn btn--primary"
                type="submit"
                disabled={outboundStatus === 'pending' || Boolean(healthError)}
              >
                {outboundStatus === 'pending'
                  ? '📤 Dialing…'
                  : isExotelActive ? '📤 Place Real Call via Exotel' : '📤 Simulate Outbound Call'}
              </button>
            </form>

            {outboundResult && (
              <div className="bot-sim__result glass">
                <h3>
                  {outboundResult.status === 'dialing' ? '📤 Call Initiated!' :
                   outboundResult.status === 'simulated' ? '⚡ Call Simulated' : '📤 Outbound Call'}
                </h3>
                <div className="call-details">
                  <p><strong>Call ID:</strong> <code>{outboundResult.call_id}</code></p>
                  <p><strong>Target Number:</strong> {outboundResult.caller}</p>
                  <p><strong>Language:</strong> {outboundResult.language === 'ml' ? 'Malayalam' : 'English'}</p>
                  <p><strong>Status:</strong>{' '}
                    <span style={{ color: outboundResult.status === 'dialing' ? 'var(--clr-teal)' : '#f59e0b' }}>
                      {outboundResult.status === 'dialing' ? '🟢 Dialing via Exotel…' :
                       outboundResult.status === 'simulated' ? '⚡ Simulated (no real call)' : outboundResult.status}
                    </span>
                  </p>

                  <div className="call-section">
                    <h4>🤖 Bot's Opening Message</h4>
                    <p className="response">{outboundResult.bot_response}</p>
                    <button
                      type="button"
                      className="btn btn--ghost"
                      style={{ marginTop: '0.75rem' }}
                      onClick={() => handleSpeakResponse(outboundResult.bot_response, outboundResult.language)}
                      disabled={isSpeaking}
                    >
                      {isSpeaking ? '🔊 Speaking…' : '🔊 Preview with Sarvam AI voice'}
                    </button>
                  </div>

                  {outboundResult.status === 'dialing' && (
                    <div style={{ padding: '0.75rem', background: 'rgba(34,197,94,0.08)', borderRadius: '8px', marginTop: '1rem', fontSize: '0.875rem' }}>
                      <strong>📞 Call placed via Exotel.</strong> The recipient's phone is ringing. When they answer, the bot will speak the opening message and begin the conversation.
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── CALL HISTORY TAB ─────────────────────────────────────────────── */}
        {activeTab === 'history' && (
          <div className="bot-sim__panel glass">
            <div className="bot-sim__panel-header">
              <h2>📋 Call History</h2>
              <span className="badge">{calls.length} calls</span>
            </div>
            <div className="call-history">
              {calls.length === 0 && (
                <p style={{ opacity: 0.6, textAlign: 'center', padding: '2rem' }}>
                  No calls yet. Make an inbound or outbound call to see records here.
                </p>
              )}
              {calls.map((call) => (
                <div key={call.call_id} className="call-history__item">
                  <div className="call-item-header">
                    <strong>{call.call_id}</strong>
                    <span className="call-badge">
                      {call.call_metadata?.call_type === 'outbound' ? '📤 Outbound' : '📥 Inbound'} · {call.language === 'ml' ? 'Malayalam' : 'English'}
                    </span>
                  </div>
                  <div className="call-item-details">
                    <span>📱 {call.caller}</span>
                    <span>⏰ {new Date(call.timestamp).toLocaleString()}</span>
                    <span style={{ opacity: 0.7 }}>
                      {call.outcome === 'outbound_initiated' ? '📤 Outbound initiated' :
                       call.outcome === 'lead_captured' ? '✅ Lead captured' :
                       call.outcome === 'escalated' ? '⚠️ Escalated' : call.outcome}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

      </main>
    </div>
  )
}
