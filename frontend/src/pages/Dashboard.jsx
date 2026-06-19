import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useHealth } from '../hooks/useHealth'
import {
  getDashboardStats,
  getRecentCalls,
  getKnowledgeGaps,
  getDashboardSettings,
  updateDashboardSettings,
  getKnowledgeEntries,
  createKnowledgeEntry,
  updateKnowledgeEntry,
  deleteKnowledgeEntry,
  uploadPDF,
  deleteKnowledgeGap,
  getLeads,
  deleteLead,
  login,
  verifyMFA,
  getAuditLogs,
  getAnalytics,
  addTrainingEntry,
  bulkTrainingImport,
  setOutboundScript,
  setBotPersonality,
  getTrainingStatus,
  voiceTrainBot,
  getVoiceStatus,
  getCampaigns,
  createCampaign,
  updateCampaignStatus,
  deleteCampaign,
  getIntegrationsStatus,
} from '../services/api'


import './Dashboard.css'

export default function Dashboard() {
  const { data: healthData } = useHealth()
  const [activeTab, setActiveTab] = useState('overview') // overview | settings | logs | leads | knowledge | gaps | analytics | audit | training | campaigns

  // ── Auth State ────────────────────────────────────────────────────────────
  const [isAuthenticated, setIsAuthenticated] = useState(!!sessionStorage.getItem('voicebot_admin_token'))
  const [authStep, setAuthStep] = useState('credentials') // credentials | mfa
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [mfaCode, setMfaCode] = useState('')
  const [authError, setAuthError] = useState(null)
  const [authLoading, setAuthLoading] = useState(false)

  // ── API State ─────────────────────────────────────────────────────────────
  const [stats, setStats] = useState(null)
  const [activeCalls, setActiveCalls] = useState([])
  const [recentCalls, setRecentCalls] = useState([])
  const [knowledgeGaps, setKnowledgeGaps] = useState([])
  const [knowledgeEntries, setKnowledgeEntries] = useState([])
  const [leads, setLeads] = useState([])
  const [auditLogs, setAuditLogs] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [editingKnowledge, setEditingKnowledge] = useState(null)
  const [knowledgeForm, setKnowledgeForm] = useState({
    question_en: '',
    answer_en: '',
    question_ml: '',
    answer_ml: '',
    category: 'General',
  })
  const [knowledgeStatus, setKnowledgeStatus] = useState(null)

  const [pdfFile, setPdfFile] = useState(null)
  const [pdfUploadStatus, setPdfUploadStatus] = useState(null) // null | 'uploading' | 'success' | 'error'
  const [pdfUploadMessage, setPdfUploadMessage] = useState('')

  // Phase 9 — full settings with office hours + escalation controls
  const [settings, setSettings] = useState({
    greeting_en: '',
    greeting_ml: '',
    voice_en: '',
    voice_ml: '',
    speaking_speed: '',
    escalation_number: '',
    engine_mode: 'paid',
    office_hours_enabled: false,
    office_hours_start: '09:00',
    office_hours_end: '18:00',
    office_timezone: 'Asia/Kolkata',
    after_hours_message_en: '',
    after_hours_message_ml: '',
    escalation_enabled: true,
    auto_escalate_after_attempts: 3,
  })

  // ── UX State ──────────────────────────────────────────────────────────────
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [saveStatus, setSaveStatus] = useState(null) // null | 'saving' | 'success' | 'error'
  const [selectedCall, setSelectedCall] = useState(null)
  const [trainingGap, setTrainingGap] = useState(null)
  const [trainingForm, setTrainingForm] = useState({ en: '', ml: '', category: 'General' })

  // ── Admin Bot Training State ──────────────────────────────────────────────
  const [trainingStatus, setTrainingStatus] = useState(null)
  const [trainingQA, setTrainingQA] = useState({ question_en: '', answer_en: '', question_ml: '', answer_ml: '', category: 'General' })
  const [trainingQAStatus, setTrainingQAStatus] = useState(null)
  const [bulkText, setBulkText] = useState('')
  const [bulkStatus, setBulkStatus] = useState(null)
  const [outboundScript, setOutboundScript] = useState({ opening_message_en: '', opening_message_ml: '', agent_name: 'Bridgeon Admissions', purpose: 'admissions' })
  const [outboundScriptStatus, setOutboundScriptStatus] = useState(null)
  const [personality, setPersonality] = useState({ bot_name: '', tone: 'friendly', language_style: 'pure_english' })
  const [personalityStatus, setPersonalityStatus] = useState(null)
  const [trainingSubTab, setTrainingSubTab] = useState('qa') // qa | bulk | outbound | personality | voice

  // ── Voice Training State ──────────────────────────────────────────────────
  const [voiceTrainingStep, setVoiceTrainingStep] = useState('idle') // idle | recording-q | recording-a | review
  const [voiceTrainingQ, setVoiceTrainingQ] = useState('')
  const [voiceTrainingA, setVoiceTrainingA] = useState('')
  const [voiceTrainingCategory, setVoiceTrainingCategory] = useState('General')
  const [voiceRecording, setVoiceRecording] = useState(false)
  const [voiceTrainingStatus, setVoiceTrainingStatus] = useState(null) // null | 'transcribing' | 'saving' | 'success' | 'error'
  const [voiceTranscriptLang, setVoiceTranscriptLang] = useState('en') // en | ml
  const [voiceChunks, setVoiceChunks] = useState([])
  const [voiceMediaRecorder, setVoiceMediaRecorder] = useState(null)
  const [voiceSpeechRecognition, setVoiceSpeechRecognition] = useState(null)
  const [voiceStatus, setVoiceStatus] = useState(null)

  // ── Outbound Campaigns State ──────────────────────────────────────────────
  const [campaigns, setCampaigns] = useState([])
  const [integrations, setIntegrations] = useState([])
  const [campaignForm, setCampaignForm] = useState({
    name: '',
    channel: 'voice',
    schedule_time: '',
    retry_attempts: 3,
    script: '',
    consent_required: true,
    dnd_compliance: true,
  })
  const [campaignStatus, setCampaignStatus] = useState(null) // null | 'loading' | 'success' | 'error'




  // ── Logs filter state ─────────────────────────────────────────────────────
  const [searchQuery, setSearchQuery] = useState('')
  const [filterLang, setFilterLang] = useState('all')
  const [filterUser, setFilterUser] = useState('all')

  // ── Data Loading ──────────────────────────────────────────────────────────
  const handleLoginSubmit = async (e) => {
    e.preventDefault()
    setAuthLoading(true)
    setAuthError(null)
    try {
      const res = await login(username, password)
      if (res.status === 'mfa_required') {
        setAuthStep('mfa')
      }
    } catch (err) {
      console.error(err)
      setAuthError('Invalid username or password. (Hint: admin / admin123)')
    } finally {
      setAuthLoading(false)
    }
  }

  const handleMfaSubmit = async (e) => {
    e.preventDefault()
    setAuthLoading(true)
    setAuthError(null)
    try {
      const res = await verifyMFA(username, mfaCode)
      if (res.status === 'success') {
        sessionStorage.setItem('voicebot_admin_token', res.token)
        setIsAuthenticated(true)
      }
    } catch (err) {
      console.error(err)
      setAuthError('Invalid MFA verification code. (Hint: 123456)')
    } finally {
      setAuthLoading(false)
    }
  }

  const handleLogout = () => {
    sessionStorage.removeItem('voicebot_admin_token')
    setIsAuthenticated(false)
    setAuthStep('credentials')
    setUsername('')
    setPassword('')
    setMfaCode('')
  }

  // ── Data Loading ──────────────────────────────────────────────────────────
  const loadData = async () => {
    try {
      setLoading(true)
      const [
        statsRes,
        callsRes,
        gapsRes,
        settingsRes,
        knowledgeRes,
        leadsRes,
        auditLogsRes,
        analyticsRes,
        voiceStatusRes,
        campaignsRes,
        integrationsRes,
      ] = await Promise.all([
        getDashboardStats(),
        getRecentCalls(),
        getKnowledgeGaps(),
        getDashboardSettings(),
        getKnowledgeEntries(),
        getLeads(),
        getAuditLogs(),
        getAnalytics(),
        getVoiceStatus().catch(() => null),
        getCampaigns().catch(() => []),
        getIntegrationsStatus().catch(() => []),
      ])
      setStats(statsRes.stats)
      setActiveCalls(statsRes.active_calls || [])
      setRecentCalls(callsRes)
      setKnowledgeGaps(gapsRes)
      setSettings(prev => ({ ...prev, ...settingsRes }))
      setKnowledgeEntries(knowledgeRes)
      setLeads(leadsRes)
      setAuditLogs(auditLogsRes || [])
      setAnalytics(analyticsRes || null)
      setVoiceStatus(voiceStatusRes)
      setCampaigns(campaignsRes)
      setIntegrations(integrationsRes)

      setError(null)
    } catch (err) {
      console.error('Failed to load dashboard data:', err)
      setError('Could not connect to backend. Please ensure the FastAPI server is running on port 8000.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isAuthenticated) {
      loadData()
    }
  }, [isAuthenticated])

  // ── Engine Toggle ─────────────────────────────────────────────────────────
  const handleEngineToggle = async () => {
    const newMode = settings.engine_mode === 'paid' ? 'open-source' : 'paid'
    const updated = { ...settings, engine_mode: newMode }
    setSettings(updated)
    try {
      await updateDashboardSettings(updated)
      setSaveStatus('success')
      setTimeout(() => setSaveStatus(null), 3000)
    } catch (err) {
      console.error(err)
      setSettings(settings)
      setSaveStatus('error')
    }
  }

  // ── Settings Handlers ─────────────────────────────────────────────────────
  const handleSettingsChange = (e) => {
    const { name, value, type, checked } = e.target
    setSettings(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }))
  }

  const handleSettingsSubmit = async (e) => {
    e.preventDefault()
    setSaveStatus('saving')
    try {
      await updateDashboardSettings(settings)
      setSaveStatus('success')
      setTimeout(() => setSaveStatus(null), 3000)
    } catch (err) {
      console.error(err)
      setSaveStatus('error')
      setTimeout(() => setSaveStatus(null), 4000)
    }
  }

  // ── Outbound Campaign Handlers ────────────────────────────────────────────
  const handleCampaignSubmit = async (e, runImmediately = false) => {
    if (e) e.preventDefault()
    setCampaignStatus('loading')
    try {
      const payload = {
        ...campaignForm,
        status: runImmediately ? 'Running' : 'Scheduled'
      }
      const newCampaign = await createCampaign(payload)
      setCampaigns(prev => [newCampaign, ...prev])
      setCampaignForm({
        name: '',
        channel: 'voice',
        schedule_time: '',
        retry_attempts: 3,
        script: '',
        consent_required: true,
        dnd_compliance: true,
      })
      setCampaignStatus('success')
      setTimeout(() => setCampaignStatus(null), 3000)
      
      // Reload campaigns soon after starting to see stats progression
      if (runImmediately) {
        setTimeout(async () => {
          const freshCampaigns = await getCampaigns().catch(() => [])
          setCampaigns(freshCampaigns)
        }, 1500)
      }
    } catch (err) {
      console.error(err)
      setCampaignStatus('error')
      setTimeout(() => setCampaignStatus(null), 3000)
    }
  }

  const handleUpdateCampaignStatus = async (id, currentStatus) => {
    const nextStatus = currentStatus === 'Running' ? 'Paused' : 'Running'
    try {
      const updated = await updateCampaignStatus(id, nextStatus)
      setCampaigns(prev => prev.map(c => c.id === id ? updated : c))
      
      // Reload soon after resuming to see dynamic progress updates
      if (nextStatus === 'Running') {
        setTimeout(async () => {
          const freshCampaigns = await getCampaigns().catch(() => [])
          setCampaigns(freshCampaigns)
        }, 1500)
      }
    } catch (err) {
      console.error(err)
    }
  }

  const handleDeleteCampaign = async (id) => {
    if (!window.confirm('Are you sure you want to delete this campaign?')) return
    try {
      await deleteCampaign(id)
      setCampaigns(prev => prev.filter(c => c.id !== id))
    } catch (err) {
      console.error(err)
    }
  }


  // ── Knowledge Handlers ────────────────────────────────────────────────────
  const handleKnowledgeFormChange = (e) => {
    const { name, value } = e.target
    setKnowledgeForm(prev => ({ ...prev, [name]: value }))
  }

  const resetKnowledgeForm = () => {
    setKnowledgeForm({ question_en: '', answer_en: '', question_ml: '', answer_ml: '', category: 'General' })
    setEditingKnowledge(null)
    setKnowledgeStatus(null)
  }

  const handlePdfUpload = async (e) => {
    e.preventDefault()
    if (!pdfFile) {
      alert('Please select a PDF file first.')
      return
    }
    setPdfUploadStatus('uploading')
    setPdfUploadMessage('')
    try {
      const res = await uploadPDF(pdfFile)
      setPdfUploadStatus('success')
      setPdfUploadMessage(res.message || 'Successfully ingested PDF document!')
      setPdfFile(null)
      // Reset input element
      const fileInput = document.getElementById('pdf-file-input')
      if (fileInput) fileInput.value = ''
      
      // Reload knowledge entries
      const knowledgeRes = await getKnowledgeEntries()
      setKnowledgeEntries(knowledgeRes)
      
      setTimeout(() => {
        setPdfUploadStatus(null)
        setPdfUploadMessage('')
      }, 5000)
    } catch (err) {
      console.error(err)
      setPdfUploadStatus('error')
      setPdfUploadMessage(err.message || 'Failed to upload PDF. Please check server logs.')
    }
  }

  const handleKnowledgeSubmit = async (e) => {
    e.preventDefault()
    setKnowledgeStatus('saving')
    try {
      const payload = {
        question_en: knowledgeForm.question_en,
        answer_en: knowledgeForm.answer_en,
        question_ml: knowledgeForm.question_ml || knowledgeForm.question_en,
        answer_ml: knowledgeForm.answer_ml || knowledgeForm.answer_en,
        category: knowledgeForm.category,
      }
      const saved = editingKnowledge
        ? await updateKnowledgeEntry(editingKnowledge.id, payload)
        : await createKnowledgeEntry(payload)
      setKnowledgeEntries(prev => editingKnowledge
        ? prev.map(item => item.id === saved.id ? saved : item)
        : [saved, ...prev])
      resetKnowledgeForm()
      setKnowledgeStatus('success')
      setTimeout(() => setKnowledgeStatus(null), 3000)
    } catch (err) {
      console.error('Failed to save knowledge entry:', err)
      setKnowledgeStatus('error')
      setTimeout(() => setKnowledgeStatus(null), 3000)
    }
  }

  const handleEditKnowledge = (entry) => {
    setEditingKnowledge(entry)
    setKnowledgeForm({
      question_en: entry.question_en,
      answer_en: entry.answer_en,
      question_ml: entry.question_ml,
      answer_ml: entry.answer_ml,
      category: entry.category,
    })
  }

  const handleDeleteKnowledge = async (entry) => {
    if (!window.confirm(`Delete FAQ entry: "${entry.question_en}"?`)) return
    try {
      await deleteKnowledgeEntry(entry.id)
      setKnowledgeEntries(prev => prev.filter(item => item.id !== entry.id))
    } catch (err) {
      console.error('Failed to delete knowledge entry:', err)
      setKnowledgeStatus('error')
      setTimeout(() => setKnowledgeStatus(null), 3000)
    }
  }

  // ── Training Modal ────────────────────────────────────────────────────────
  const handleTrainSubmit = async (e) => {
    e.preventDefault()
    const newEntry = {
      question_en: trainingGap.question,
      answer_en: trainingForm.en,
      question_ml: trainingGap.question,
      answer_ml: trainingForm.ml,
      category: trainingForm.category,
    }
    try {
      const saved = await createKnowledgeEntry(newEntry)
      await deleteKnowledgeGap(trainingGap.id)
      setKnowledgeEntries(prev => [saved, ...prev])
      setKnowledgeGaps(prev => prev.filter(g => g.id !== trainingGap.id))
      setTrainingGap(null)
      setTrainingForm({ en: '', ml: '', category: 'General' })
    } catch (err) {
      console.error('Failed to publish knowledge:', err)
      alert('Unable to publish this knowledge entry. Please try again later.')
    }
  }

  // ── Voice Training Handlers ───────────────────────────────────────────────
  const startVoiceRecording = async (target) => {
    setVoiceTrainingStatus(null)
    const isServerSTT = voiceStatus?.sarvam_configured || voiceStatus?.openai_configured

    if (isServerSTT) {
      setVoiceRecording(true)
      const chunks = []
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        const recorder = new MediaRecorder(stream)
        recorder.ondataavailable = (e) => {
          if (e.data && e.data.size > 0) {
            chunks.push(e.data)
          }
        }
        recorder.onstop = async () => {
          const audioBlob = new Blob(chunks, { type: recorder.mimeType || 'audio/webm' })
          stream.getTracks().forEach(track => track.stop())
          await processRecordedAudio(audioBlob, target)
        }
        recorder.start()
        setVoiceMediaRecorder(recorder)
      } catch (err) {
        console.error('Failed to access microphone:', err)
        alert('Could not access microphone. Please check permissions.')
        setVoiceRecording(false)
      }
    } else {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      if (!SpeechRecognition) {
        alert('Speech Recognition is not supported in this browser. Please type your Q&A manually.')
        return
      }
      setVoiceRecording(true)
      const recognition = new SpeechRecognition()
      recognition.lang = voiceTranscriptLang === 'ml' ? 'ml-IN' : 'en-IN'
      recognition.interimResults = true
      recognition.maxAlternatives = 1

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript
        if (target === 'question') {
          setVoiceTrainingQ(transcript)
        } else {
          setVoiceTrainingA(transcript)
        }
      }

      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error)
        if (event.error === 'not-allowed') {
          alert('Microphone access denied. Please check your browser permissions.')
        }
        setVoiceRecording(false)
      }

      recognition.onend = () => {
        setVoiceRecording(false)
      }

      recognition.start()
      setVoiceSpeechRecognition(recognition)
    }
  }

  const stopVoiceRecording = () => {
    setVoiceRecording(false)

    if (voiceSpeechRecognition) {
      try {
        voiceSpeechRecognition.stop()
      } catch (err) {
        console.error(err)
      }
      setVoiceSpeechRecognition(null)
    }

    if (voiceMediaRecorder && voiceMediaRecorder.state !== 'inactive') {
      try {
        voiceMediaRecorder.stop()
      } catch (err) {
        console.error(err)
      }
      setVoiceMediaRecorder(null)
    }
  }

  const processRecordedAudio = async (audioBlob, target) => {
    setVoiceTrainingStatus('transcribing')
    try {
      const reader = new FileReader()
      reader.readAsDataURL(audioBlob)
      reader.onloadend = async () => {
        const base64Audio = reader.result
        try {
          const res = await transcribeAudio(base64Audio, voiceTranscriptLang)
          if (res && res.transcript) {
            if (target === 'question') {
              setVoiceTrainingQ(res.transcript)
            } else {
              setVoiceTrainingA(res.transcript)
            }
            setVoiceTrainingStatus(null)
          } else {
            throw new Error('Empty transcript')
          }
        } catch (serverErr) {
          console.error('Server STT failed:', serverErr)
          setVoiceTrainingStatus('error')
          setTimeout(() => setVoiceTrainingStatus(null), 3000)
        }
      }
    } catch (err) {
      console.error('Failed to process audio blob:', err)
      setVoiceTrainingStatus('error')
    }
  }


  const handleVoiceTrainingSubmit = async (e) => {
    e.preventDefault()
    if (!voiceTrainingQ.trim() || !voiceTrainingA.trim()) {
      alert('Please record or enter both a question and an answer.')
      return
    }
    setVoiceTrainingStatus('saving')
    try {
      const payload = {
        question_en: voiceTrainingQ,
        answer_en: voiceTrainingA,
        question_ml: voiceTranscriptLang === 'ml' ? voiceTrainingQ : '',
        answer_ml: voiceTranscriptLang === 'ml' ? voiceTrainingA : '',
        category: voiceTrainingCategory,
      }
      const saved = await createKnowledgeEntry(payload)
      setKnowledgeEntries(prev => [saved, ...prev])
      setVoiceTrainingStatus('success')
      setVoiceTrainingQ('')
      setVoiceTrainingA('')
      setVoiceTrainingStep('idle')
      setTimeout(() => setVoiceTrainingStatus(null), 3000)
    } catch (err) {
      console.error('Failed to save voice training entry:', err)
      setVoiceTrainingStatus('error')
      setTimeout(() => setVoiceTrainingStatus(null), 3000)
    }
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  const normalize = (value) => String(value ?? '').toLowerCase()
  const formatValue = (value, fallback = 'N/A') => value || fallback
  const getOutcomeClass = (outcome = '') => {
    if (outcome.includes('Lead')) return 'pill--success'
    if (outcome.includes('Escalated')) return 'pill--warning'
    return 'pill--muted'
  }

  const filteredCalls = recentCalls.filter(call => {
    const query = normalize(searchQuery)
    const matchesSearch = normalize(call.caller).includes(query) || normalize(call.intent).includes(query)
    const matchesLang = filterLang === 'all' || normalize(call.language) === normalize(filterLang)
    const matchesUser = filterUser === 'all' || normalize(call.user_type) === normalize(filterUser)
    return matchesSearch && matchesLang && matchesUser
  })

  // ─────────────────────────────────────────────────────────────────────────
  if (!isAuthenticated) {
    return (
      <div className="auth-page">
        <div className="blob blob--1" aria-hidden="true" />
        <div className="blob blob--2" aria-hidden="true" />
        
        <div className="auth-card glass animate-fade-in-up">
          <div className="auth-card__logo">
            <span className="auth-card__logo-icon">🤖</span>
            <h2>Bridgeon <span className="gradient-text">Admin Portal</span></h2>
            <p className="auth-card__subtitle">Bilingual Voice Call Assistant v4.0</p>
          </div>

          {authError && (
            <div className="auth-error-banner" role="alert">
              <span>⚠️</span> {authError}
            </div>
          )}

          {authStep === 'credentials' ? (
            <form onSubmit={handleLoginSubmit} className="auth-form">
              <div className="form-group">
                <label htmlFor="login-username">Admin Username</label>
                <input
                  id="login-username"
                  type="text"
                  placeholder="Enter admin username"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="login-password">Password</label>
                <input
                  id="login-password"
                  type="password"
                  placeholder="Enter admin password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="btn btn--primary auth-btn" disabled={authLoading}>
                {authLoading ? 'Verifying...' : 'Authenticate & Next →'}
              </button>
            </form>
          ) : (
            <form onSubmit={handleMfaSubmit} className="auth-form">
              <div className="auth-mfa-info">
                <p><strong>Multi-Factor Authentication Required</strong></p>
                <p className="form-helper">An OTP has been simulated for your session. Please enter the passcode to authorize access.</p>
              </div>
              <div className="form-group">
                <label htmlFor="login-mfa">6-Digit Verification Code</label>
                <input
                  id="login-mfa"
                  type="text"
                  maxLength={6}
                  placeholder="Enter 6-digit code (e.g. 123456)"
                  value={mfaCode}
                  onChange={e => setMfaCode(e.target.value)}
                  required
                />
              </div>
              <div className="auth-mfa-actions">
                <button type="submit" className="btn btn--primary auth-btn" disabled={authLoading}>
                  {authLoading ? 'Authorizing...' : 'Verify & Enter Portal'}
                </button>
                <button type="button" className="btn btn--ghost auth-btn" onClick={() => setAuthStep('credentials')}>
                  &larr; Back to Login
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="db">
      {/* ── Sidebar ──────────────────────────────────────────────────────── */}
      <aside className="db__sidebar">
        <div className="db__logo">
          <div className="db__logo-icon">🤖</div>
          <span className="db__logo-text">
            Bridgeon <span className="gradient-text">Buddy</span>
          </span>
        </div>

        <nav className="db__nav" aria-label="Dashboard navigation">
          {/* Core */}
          <span className="db__nav-section-label">Core</span>
          {[
            { id: 'overview',   label: '📊', text: 'System Overview' },
            { id: 'analytics',  label: '📈', text: 'Analytics' },
            { id: 'logs',       label: '📞', text: 'Call Logs' },
            { id: 'leads',      label: '🧾', text: 'Leads' },
          ].map(tab => (
            <button
              key={tab.id}
              className={`db__nav-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label} {tab.text}
            </button>
          ))}

          {/* Campaigns */}
          <span className="db__nav-section-label">Outreach</span>
          <button
            className={`db__nav-btn ${activeTab === 'campaigns' ? 'active' : ''}`}
            onClick={() => setActiveTab('campaigns')}
          >
            📣 Campaign Manager
          </button>

          {/* Knowledge */}
          <span className="db__nav-section-label">Knowledge</span>
          {[
            { id: 'knowledge',  label: '📚', text: 'Knowledge Base' },
            { id: 'gaps',       label: '⚠️', text: 'Knowledge Gaps' },
            { id: 'training',   label: '🧠', text: 'Bot Training' },
          ].map(tab => (
            <button
              key={tab.id}
              className={`db__nav-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label} {tab.text}
            </button>
          ))}

          {/* Config */}
          <span className="db__nav-section-label">Config</span>
          {[
            { id: 'settings',   label: '⚙️', text: 'Call Config' },
            { id: 'audit',      label: '🛡️', text: 'Audit Logs' },
          ].map(tab => (
            <button
              key={tab.id}
              className={`db__nav-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label} {tab.text}
            </button>
          ))}

          {/* External */}
          <span className="db__nav-section-label">Tools</span>
          <Link to="/telephony" className="db__nav-btn db__nav-link">📞 Telephony Sim</Link>
          <Link to="/bot" className="db__nav-btn db__nav-link">🎙️ Bot Simulator</Link>
          <Link to="/call" className="db__nav-btn db__nav-link">🔴 Real-Time Call</Link>

          <button onClick={handleLogout} className="db__nav-btn db__logout-btn">
            🚪 Logout
          </button>
        </nav>

        {/* Engine mode quick toggle */}
        <div className="db__sidebar-footer">
          <div className="db__engine-card">
            <span className="db__engine-label">AI Engine Mode</span>
            <div className="db__engine-switch-row">
              <span className={`db__engine-val ${settings.engine_mode === 'paid' ? 'active' : ''}`}>Paid</span>
              <button
                className={`switch-toggle ${settings.engine_mode === 'paid' ? 'switch-toggle--paid' : 'switch-toggle--os'}`}
                onClick={handleEngineToggle}
                aria-label="Toggle AI Engine mode"
              >
                <div className="switch-toggle__knob" />
              </button>
              <span className={`db__engine-val ${settings.engine_mode === 'open-source' ? 'active' : ''}`}>O/S</span>
            </div>
            <p className="db__engine-desc">
              {settings.engine_mode === 'paid'
                ? '🔵 Twilio + OpenAI + Azure'
                : '🟢 FreeSWITCH + Rasa + Coqui'}
            </p>
          </div>
          <Link to="/" className="btn btn--ghost db__back-home">← Back to Site</Link>
        </div>
      </aside>

      {/* ── Main Panel ───────────────────────────────────────────────────── */}
      <main className="db__main">
        {/* Header */}
        <header className="db__header">
          <div className="db__header-title">
            <h1>
              {activeTab === 'overview'   && '📊 System Overview'}
              {activeTab === 'analytics'  && '📈 Analytics & Metrics'}
              {activeTab === 'settings'   && '⚙️ Call Configuration'}
              {activeTab === 'logs'       && '📞 Call Logs & Transcripts'}
              {activeTab === 'leads'      && '🧾 Lead Capture Records'}
              {activeTab === 'knowledge'  && '📚 Knowledge Base'}
              {activeTab === 'gaps'       && '⚠️ Unanswered Questions'}
              {activeTab === 'training'   && '🧠 Bot Training'}
              {activeTab === 'audit'      && '🛡️ Security Audit Trails'}
              {activeTab === 'campaigns'  && '📣 Campaign Manager'}
            </h1>
            <p className="db__header-subtitle">
              Bridgeon Buddy Voice Assistant v4.0 · Admin Control Panel
            </p>
          </div>
          <div className="db__header-status">
            {healthData
              ? <span className="badge badge--ok">🟢 Backend Connected</span>
              : <span className="badge badge--error">🔴 Backend Offline</span>}
          </div>
        </header>

        {error && (
          <div className="db__error-banner glass" role="alert">
            <h3>⚠️ Connection Failure</h3>
            <p>{error}</p>
            <button className="btn btn--primary" onClick={loadData}>Retry Connection</button>
          </div>
        )}

        {loading && !error && (
          <div className="db__loading">
            <div className="spinner" />
            <span>Fetching live dashboard details...</span>
          </div>
        )}

        {saveStatus && (
          <div className={`db__toast ${saveStatus === 'success' ? 'success' : saveStatus === 'saving' ? 'saving' : 'error'}`}>
            {saveStatus === 'saving'  && '⏳ Saving configurations...'}
            {saveStatus === 'success' && '✔ Changes saved successfully!'}
            {saveStatus === 'error'   && '✖ Failed to save configurations.'}
          </div>
        )}

        {!loading && !error && (
          <div className="db__content animate-fade-in-up">

            {/* ─── TAB: OVERVIEW ────────────────────────────────────────── */}
            {activeTab === 'overview' && (
              <>
                <section className="db__stats-grid" aria-label="Key Performance Indicators">
                  <div className="stat-card glass">
                    <span className="stat-card__icon">📞</span>
                    <div className="stat-card__details">
                      <span className="stat-card__val gradient-text">{stats?.total_calls}</span>
                      <span className="stat-card__lbl">Today's Inbound Calls</span>
                    </div>
                  </div>
                  <div className="stat-card glass">
                    <span className="stat-card__icon">📋</span>
                    <div className="stat-card__details">
                      <span className="stat-card__val gradient-text">{stats?.leads_captured}</span>
                      <span className="stat-card__lbl">Leads Captured</span>
                    </div>
                  </div>
                  <div className="stat-card glass">
                    <span className="stat-card__icon">✅</span>
                    <div className="stat-card__details">
                      <span className="stat-card__val gradient-text">{stats?.resolution_rate}%</span>
                      <span className="stat-card__lbl">Resolution Rate</span>
                    </div>
                  </div>
                  <div className="stat-card glass">
                    <span className="stat-card__icon">🔴</span>
                    <div className="stat-card__details">
                      <span className="stat-card__val" style={{ color: 'var(--clr-danger)' }}>{stats?.escalation_rate}%</span>
                      <span className="stat-card__lbl">Escalation Rate</span>
                    </div>
                  </div>
                </section>

                <div className="db__split-grid">
                  {/* Active Calls Monitor */}
                  <section className="glass db__active-calls-panel">
                    <h2>Live Active Call Monitor</h2>
                    {activeCalls.length === 0 ? (
                      <p className="no-calls">No active calls right now.</p>
                    ) : (
                      activeCalls.map(call => (
                        <div key={call.call_id} className="active-call-item">
                          <div className="active-call-header">
                            <span className="active-call-caller">{call.caller}</span>
                            <span className="active-call-badge blink">LIVE</span>
                          </div>
                          <div className="active-call-waveform" aria-hidden="true">
                            <div className="wave-bar bar-1" />
                            <div className="wave-bar bar-2" />
                            <div className="wave-bar bar-3" />
                            <div className="wave-bar bar-4" />
                            <div className="wave-bar bar-5" />
                          </div>
                          <div className="active-call-metadata">
                            <div><strong>Duration:</strong> {call.duration}</div>
                            <div><strong>User Type:</strong> <span className="text-highlight">{call.user_type}</span></div>
                            <div><strong>Intent:</strong> {call.intent}</div>
                            <div><strong>Language:</strong> {call.language}</div>
                          </div>
                        </div>
                      ))
                    )}
                  </section>

                  {/* Top Knowledge Gaps */}
                  <section className="glass db__gaps-preview">
                    <div className="panel-header">
                      <h2>Top Knowledge Gaps</h2>
                      <button className="text-btn" onClick={() => setActiveTab('gaps')}>View All →</button>
                    </div>
                    <div className="gaps-list">
                      {knowledgeGaps.slice(0, 3).map(gap => (
                        <div key={gap.id} className="gap-preview-item">
                          <div className="gap-info">
                            <span className="gap-text">"{gap.question}"</span>
                            <span className="gap-count">{gap.frequency} occurrences</span>
                          </div>
                          <button className="btn btn--primary btn--sm" onClick={() => {
                            setTrainingGap(gap)
                            setTrainingForm({ en: '', ml: '', category: gap.category })
                          }}>Train Bot</button>
                        </div>
                      ))}
                    </div>
                  </section>
                </div>

                {/* Recent Call Logs preview */}
                <section className="glass db__logs-preview">
                  <div className="panel-header">
                    <h2>Recent Call Logs</h2>
                    <button className="text-btn" onClick={() => setActiveTab('logs')}>View Full Logs →</button>
                  </div>
                  <div className="table-responsive">
                    <table className="db__table">
                      <thead>
                        <tr>
                          <th>Call ID</th><th>Caller</th><th>Duration</th>
                          <th>Intent</th><th>Language</th><th>Outcome</th><th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {recentCalls.slice(0, 4).map(call => (
                          <tr key={call.call_id}>
                            <td><code>{call.call_id}</code></td>
                            <td>{call.caller}</td>
                            <td>{call.duration}</td>
                            <td><span className="pill pill--intent">{call.intent}</span></td>
                            <td>{call.language}</td>
                            <td><span className={`pill ${getOutcomeClass(call.outcome)}`}>{formatValue(call.outcome)}</span></td>
                            <td>
                              <button className="btn btn--ghost btn--sm" onClick={() => setSelectedCall(call)}>
                                View Transcript
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              </>
            )}

            {/* ─── TAB: ANALYTICS (Phase 10) ───────────────────────────── */}
            {activeTab === 'analytics' && (
              <>
                <section className="db__analytics-grid">
                  <div className="analytics-card">
                    <span className="analytics-card__icon">📞</span>
                    <span className="analytics-card__label">Total Calls Today</span>
                    <span className="analytics-card__value gradient-text">{stats?.total_calls ?? 0}</span>
                    <span className="analytics-card__sub">{stats?.total_calls_all_time ?? 0} all-time calls logged</span>
                    <div className="analytics-card__bar">
                      <div className="analytics-card__bar-fill analytics-card__bar-fill--teal" style={{ width: `${Math.min((stats?.total_calls ?? 0) * 10, 100)}%` }} />
                    </div>
                  </div>
                  <div className="analytics-card analytics-card--accent">
                    <span className="analytics-card__icon">🧾</span>
                    <span className="analytics-card__label">Leads Captured</span>
                    <span className="analytics-card__value" style={{ color: 'var(--clr-accent-light)' }}>
                      {stats?.leads_captured ?? leads.length}
                    </span>
                    <span className="analytics-card__sub">{stats?.bot_interactions ?? 0} bot interactions tracked</span>
                    <div className="analytics-card__bar">
                      <div className="analytics-card__bar-fill analytics-card__bar-fill--violet" style={{ width: `${Math.min((stats?.leads_captured ?? leads.length) * 8, 100)}%` }} />
                    </div>
                  </div>
                  <div className="analytics-card">
                    <span className="analytics-card__icon">✅</span>
                    <span className="analytics-card__label">Resolution Rate</span>
                    <span className="analytics-card__value gradient-text">{stats?.resolution_rate ?? 0}%</span>
                    <span className="analytics-card__sub">Bot resolved without escalation</span>
                    <div className="analytics-card__bar">
                      <div className="analytics-card__bar-fill analytics-card__bar-fill--teal" style={{ width: `${stats?.resolution_rate ?? 0}%` }} />
                    </div>
                  </div>
                  <div className="analytics-card analytics-card--amber">
                    <span className="analytics-card__icon">🔴</span>
                    <span className="analytics-card__label">Escalation Rate</span>
                    <span className="analytics-card__value" style={{ color: 'var(--clr-danger)' }}>
                      {stats?.escalation_rate ?? 0}%
                    </span>
                    <span className="analytics-card__sub">Forwarded to human agent</span>
                    <div className="analytics-card__bar">
                      <div className="analytics-card__bar-fill analytics-card__bar-fill--red" style={{ width: `${stats?.escalation_rate ?? 0}%` }} />
                    </div>
                  </div>
                </section>

                <div className="db__analytics-row">
                  <div className="analytics-panel glass">
                    <h3>Call Outcome Breakdown</h3>
                    <div className="analytics-bar-list">
                      {(analytics?.outcomes ?? []).map(item => (
                        <div key={item.label} className="analytics-bar-item">
                          <div className="analytics-bar-item__header">
                            <span className="analytics-bar-item__label">{item.label}</span>
                            <span className="analytics-bar-item__pct">{item.pct}%</span>
                          </div>
                          <div className="analytics-bar-item__track">
                            <div className="analytics-bar-item__fill" style={{ width: `${item.pct}%`, background: 'var(--grad-brand)' }} />
                          </div>
                        </div>
                      ))}
                      {!analytics?.outcomes?.length && (
                        <p className="form-helper">No call events yet. Use the bot or telephony simulator to generate live metrics.</p>
                      )}
                    </div>
                  </div>

                  <div className="analytics-panel glass">
                    <h3>Language Distribution</h3>
                    <div className="analytics-lang-pie">
                      <div className="pie-block">
                        <div className="pie-circle pie-circle--teal">{analytics?.languages?.en?.pct ?? 0}%</div>
                        <span className="pie-label">English<br/>Calls</span>
                      </div>
                      <div className="pie-block">
                        <div className="pie-circle pie-circle--violet">{analytics?.languages?.ml?.pct ?? 0}%</div>
                        <span className="pie-label">Malayalam<br/>Calls</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="analytics-panel glass">
                  <h3>Top Caller Intents</h3>
                  <div className="analytics-bar-list">
                    {(analytics?.top_intents ?? []).map((item, i) => (
                      <div key={item.label} className="analytics-bar-item">
                        <div className="analytics-bar-item__header">
                          <span className="analytics-bar-item__label">{item.label}</span>
                          <span className="analytics-bar-item__pct">{item.pct}%</span>
                        </div>
                        <div className="analytics-bar-item__track">
                          <div
                            className="analytics-bar-item__fill"
                            style={{
                              width: `${item.pct}%`,
                              background: i % 2 === 0 ? 'var(--grad-brand)' : 'linear-gradient(90deg,var(--clr-accent),var(--clr-accent-light))'
                            }}
                          />
                        </div>
                      </div>
                    ))}
                    {!analytics?.top_intents?.length && (
                      <p className="form-helper">Intent data will appear after simulated calls and bot conversations.</p>
                    )}
                  </div>
                </div>
              </>
            )}

            {/* ─── TAB: SETTINGS (Phase 9 — all fields) ────────────────── */}
            {activeTab === 'settings' && (
              <form onSubmit={handleSettingsSubmit} className="db__form-container">
                <section className="glass db__form-section">
                  <h2>Greeting Scripts</h2>
                  <p className="form-helper">Customize the greeting the voice assistant plays when answering a call.</p>
                  <div className="form-group">
                    <label htmlFor="greeting_en">English Greeting Text</label>
                    <textarea id="greeting_en" name="greeting_en" value={settings.greeting_en}
                      onChange={handleSettingsChange} rows={3} required />
                  </div>
                  <div className="form-group">
                    <label htmlFor="greeting_ml">Malayalam Greeting Text</label>
                    <textarea id="greeting_ml" name="greeting_ml" value={settings.greeting_ml}
                      onChange={handleSettingsChange} rows={3} required />
                  </div>
                </section>

                <section className="glass db__form-section">
                  <h2>Voice & Speed Engine</h2>
                  <p className="form-helper">Configure TTS synthesizer voices and speaking speed.</p>
                  <div className="form-row">
                    <div className="form-group">
                      <label htmlFor="voice_en">English Synthesizer Voice</label>
                      <select id="voice_en" name="voice_en" value={settings.voice_en} onChange={handleSettingsChange}>
                        <option value="en-IN-Wavenet-A (Female)">en-IN-Wavenet-A (Female)</option>
                        <option value="en-IN-Neural-B (Male)">en-IN-Neural-B (Male)</option>
                        <option value="en-US-Standard-C (Female)">en-US-Standard-C (Female)</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label htmlFor="voice_ml">Malayalam Synthesizer Voice</label>
                      <select id="voice_ml" name="voice_ml" value={settings.voice_ml} onChange={handleSettingsChange}>
                        <option value="ml-IN-Standard-A (Female)">ml-IN-Standard-A (Female)</option>
                        <option value="ml-IN-Neural-B (Female)">ml-IN-Neural-B (Female)</option>
                        <option value="ml-IN-Standard-C (Male)">ml-IN-Standard-C (Male)</option>
                      </select>
                    </div>
                  </div>
                  <div className="form-group">
                    <label htmlFor="speaking_speed">Speaking Speed</label>
                    <select id="speaking_speed" name="speaking_speed" value={settings.speaking_speed} onChange={handleSettingsChange}>
                      <option value="slow">Slow (0.85x — highly understandable)</option>
                      <option value="normal">Normal (1.0x — conversational)</option>
                      <option value="fast">Fast (1.15x — responsive)</option>
                    </select>
                  </div>
                </section>

                <section className="glass db__form-section">
                  <h2>Escalation Path</h2>
                  <p className="form-helper">Configure where calls are forwarded when the bot cannot resolve a query.</p>
                  <div className="form-row">
                    <div className="form-group">
                      <label htmlFor="escalation_number">Escalation Destination Number</label>
                      <input id="escalation_number" name="escalation_number" type="tel"
                        value={settings.escalation_number} onChange={handleSettingsChange} required />
                    </div>
                    <div className="form-group">
                      <label htmlFor="auto_escalate_after_attempts">Escalate After (attempts)</label>
                      <input id="auto_escalate_after_attempts" name="auto_escalate_after_attempts"
                        type="number" min={1} max={10}
                        value={settings.auto_escalate_after_attempts} onChange={handleSettingsChange} />
                    </div>
                  </div>
                  <div className="toggle-row">
                    <div className="toggle-row__label">
                      <span>Auto-Escalation Enabled</span>
                      <span>Automatically transfer call after failed attempts</span>
                    </div>
                    <button
                      type="button"
                      className={`switch-toggle ${settings.escalation_enabled ? 'switch-toggle--paid' : 'switch-toggle--os'}`}
                      onClick={() => setSettings(p => ({ ...p, escalation_enabled: !p.escalation_enabled }))}
                      aria-label="Toggle auto escalation"
                    >
                      <div className="switch-toggle__knob" />
                    </button>
                  </div>
                </section>

                <section className="glass db__form-section">
                  <h2>Office Hours</h2>
                  <p className="form-helper">Restrict bot to working hours. Calls outside these hours get the after-hours message.</p>
                  <div className="toggle-row">
                    <div className="toggle-row__label">
                      <span>Office Hours Enforcement</span>
                      <span>Enable to restrict bot to the time window below</span>
                    </div>
                    <button
                      type="button"
                      className={`switch-toggle ${settings.office_hours_enabled ? 'switch-toggle--paid' : 'switch-toggle--os'}`}
                      onClick={() => setSettings(p => ({ ...p, office_hours_enabled: !p.office_hours_enabled }))}
                      aria-label="Toggle office hours"
                    >
                      <div className="switch-toggle__knob" />
                    </button>
                  </div>
                  <div className="form-row-3">
                    <div className="form-group">
                      <label htmlFor="office_hours_start">Start Time</label>
                      <input id="office_hours_start" name="office_hours_start" type="time"
                        value={settings.office_hours_start} onChange={handleSettingsChange}
                        disabled={!settings.office_hours_enabled} />
                    </div>
                    <div className="form-group">
                      <label htmlFor="office_hours_end">End Time</label>
                      <input id="office_hours_end" name="office_hours_end" type="time"
                        value={settings.office_hours_end} onChange={handleSettingsChange}
                        disabled={!settings.office_hours_enabled} />
                    </div>
                    <div className="form-group">
                      <label htmlFor="office_timezone">Timezone</label>
                      <select id="office_timezone" name="office_timezone" value={settings.office_timezone}
                        onChange={handleSettingsChange} disabled={!settings.office_hours_enabled}>
                        <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
                        <option value="Asia/Dubai">Asia/Dubai (GST)</option>
                        <option value="UTC">UTC</option>
                        <option value="America/New_York">America/New_York (EST)</option>
                      </select>
                    </div>
                  </div>
                  <div className="form-group">
                    <label htmlFor="after_hours_message_en">After-Hours Message (English)</label>
                    <textarea id="after_hours_message_en" name="after_hours_message_en"
                      value={settings.after_hours_message_en} onChange={handleSettingsChange}
                      rows={2} disabled={!settings.office_hours_enabled}
                      placeholder="Message played outside office hours in English..." />
                  </div>
                  <div className="form-group">
                    <label htmlFor="after_hours_message_ml">After-Hours Message (Malayalam)</label>
                    <textarea id="after_hours_message_ml" name="after_hours_message_ml"
                      value={settings.after_hours_message_ml} onChange={handleSettingsChange}
                      rows={2} disabled={!settings.office_hours_enabled}
                      placeholder="Message played outside office hours in Malayalam..." />
                  </div>
                </section>

                <div className="form-actions">
                  <button type="submit" className="btn btn--primary">Save All Settings</button>
                </div>
              </form>
            )}

            {/* ─── TAB: KNOWLEDGE BASE ──────────────────────────────────── */}
            {activeTab === 'knowledge' && (
              <section className="glass db__panel-section">
                <div className="panel-header">
                  <div>
                    <h2>Knowledge Base</h2>
                    <p className="form-helper">Create and manage FAQ responses for the voice bot.</p>
                  </div>
                  <div className="knowledge-status-row">
                    {knowledgeStatus === 'saving'  && <span className="badge badge--info">Saving knowledge...</span>}
                    {knowledgeStatus === 'success' && <span className="badge badge--success">✔ Saved successfully!</span>}
                    {knowledgeStatus === 'error'   && <span className="badge badge--error">Save failed</span>}
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
                  {/* Left: Standard FAQ Form */}
                  <form onSubmit={handleKnowledgeSubmit} className="db__form-container" style={{ margin: 0 }}>
                    <section className="glass db__form-section" style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                      <div>
                        <h3>{editingKnowledge ? 'Edit FAQ Entry' : 'Add New FAQ Entry'}</h3>
                        <p className="form-helper" style={{ marginBottom: '1rem' }}>Enter manual Q&As that you want the bot to know directly.</p>
                        <div className="form-group">
                          <label htmlFor="question_en">English Question</label>
                          <input id="question_en" name="question_en" value={knowledgeForm.question_en}
                            onChange={handleKnowledgeFormChange}
                            placeholder="e.g. What is the course duration for MERN?" required />
                        </div>
                        <div className="form-group">
                          <label htmlFor="question_ml">Malayalam Question (optional)</label>
                          <input id="question_ml" name="question_ml" value={knowledgeForm.question_ml}
                            onChange={handleKnowledgeFormChange} placeholder="Optional Malayalam question" />
                        </div>
                        <div className="form-group">
                          <label htmlFor="answer_en">English Answer</label>
                          <textarea id="answer_en" name="answer_en" value={knowledgeForm.answer_en}
                            onChange={handleKnowledgeFormChange} rows={3}
                            placeholder="Provide the bot's English response..." required />
                        </div>
                        <div className="form-group">
                          <label htmlFor="answer_ml">Malayalam Answer (optional)</label>
                          <textarea id="answer_ml" name="answer_ml" value={knowledgeForm.answer_ml}
                            onChange={handleKnowledgeFormChange} rows={3}
                            placeholder="Optional Malayalam answer" />
                        </div>
                        <div className="form-group">
                          <label htmlFor="category">Knowledge Category</label>
                          <select id="category" name="category" value={knowledgeForm.category} onChange={handleKnowledgeFormChange}>
                            <option value="General">General</option>
                            <option value="Course Info">Course Info</option>
                            <option value="Fees">Fees</option>
                            <option value="Admissions">Admissions</option>
                            <option value="Student Support">Student Support</option>
                          </select>
                        </div>
                      </div>
                      <div className="form-actions" style={{ marginTop: '1rem', padding: 0, border: 'none' }}>
                        <button type="submit" className="btn btn--primary">
                          {editingKnowledge ? 'Update Entry' : 'Add Entry'}
                        </button>
                        {editingKnowledge && (
                          <button type="button" className="btn btn--ghost" onClick={resetKnowledgeForm}>Cancel Edit</button>
                        )}
                      </div>
                    </section>
                  </form>

                  {/* Right: PDF Document Ingestion */}
                  <div className="db__form-container">
                    <section className="glass db__form-section" style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                      <div>
                        <h3>Bulk Document Ingestion (PDF)</h3>
                        <p className="form-helper" style={{ marginBottom: '1.5rem' }}>
                          Upload bulk document entries like company brochures, course syllabus sheets, and refund policy guides. 
                          The agentic RAG system will partition, chunk, embed, and query them.
                        </p>
                        
                        <div className="pdf-upload-box" style={{ 
                          border: '2px dashed var(--clr-border, #ccc)', 
                          borderRadius: '8px', 
                          padding: '2rem', 
                          textAlign: 'center', 
                          background: 'rgba(255, 255, 255, 0.03)',
                          marginBottom: '1rem' 
                        }}>
                          <span style={{ fontSize: '3rem', display: 'block', marginBottom: '1rem' }}>📄</span>
                          <label htmlFor="pdf-file-input" style={{ cursor: 'pointer', display: 'block', fontWeight: 'bold', marginBottom: '0.5rem' }}>
                            {pdfFile ? pdfFile.name : 'Select a PDF Document'}
                          </label>
                          <p className="form-helper" style={{ margin: '0 0 1rem 0' }}>Maximum size: 10MB</p>
                          <input 
                            id="pdf-file-input" 
                            type="file" 
                            accept=".pdf" 
                            style={{ display: 'none' }}
                            onChange={(e) => setPdfFile(e.target.files[0])}
                          />
                          <button 
                            type="button" 
                            className="btn btn--ghost btn--sm" 
                            onClick={() => document.getElementById('pdf-file-input').click()}
                          >
                            Browse Files
                          </button>
                        </div>

                        {pdfUploadStatus && (
                          <div style={{
                            padding: '1rem',
                            borderRadius: '6px',
                            background: pdfUploadStatus === 'success' ? 'rgba(76, 175, 80, 0.1)' : pdfUploadStatus === 'uploading' ? 'rgba(33, 150, 243, 0.1)' : 'rgba(244, 67, 54, 0.1)',
                            border: `1px solid ${pdfUploadStatus === 'success' ? '#4caf50' : pdfUploadStatus === 'uploading' ? '#2196f3' : '#f44336'}`,
                            color: pdfUploadStatus === 'success' ? '#4caf50' : pdfUploadStatus === 'uploading' ? '#2196f3' : '#f44336',
                            marginBottom: '1rem',
                            fontSize: '0.9rem'
                          }}>
                            {pdfUploadStatus === 'uploading' && '⏳ Ingesting PDF document, building semantic index...'}
                            {pdfUploadStatus === 'success' && `✔ ${pdfUploadMessage}`}
                            {pdfUploadStatus === 'error' && `✖ ${pdfUploadMessage}`}
                          </div>
                        )}
                      </div>

                      <div className="form-actions" style={{ padding: 0, border: 'none' }}>
                        <button 
                          type="button" 
                          className="btn btn--primary" 
                          disabled={!pdfFile || pdfUploadStatus === 'uploading'}
                          onClick={handlePdfUpload}
                          style={{ width: '100%' }}
                        >
                          {pdfUploadStatus === 'uploading' ? 'Ingesting...' : 'Ingest Document'}
                        </button>
                      </div>
                    </section>
                  </div>
                </div>

                <div className="knowledge-list">
                  {knowledgeEntries.length === 0 ? (
                    <div className="no-data-panel glass">
                      <h3>No knowledge entries yet.</h3>
                      <p>Use the form above to add your first FAQ answer.</p>
                    </div>
                  ) : (
                    knowledgeEntries.map(entry => (
                      <div key={entry.id} className="knowledge-card glass">
                        <div className="knowledge-card__meta">
                          <strong>{entry.category}</strong>
                          <span>Updated {new Date(entry.updated_at).toLocaleDateString()}</span>
                        </div>
                        <p className="knowledge-card__question">Q: {entry.question_en}</p>
                        <p className="knowledge-card__answer">A: {entry.answer_en}</p>
                        <div className="knowledge-card__actions">
                          <button className="btn btn--ghost btn--sm" onClick={() => handleEditKnowledge(entry)}>Edit</button>
                          <button className="btn btn--danger btn--sm" onClick={() => handleDeleteKnowledge(entry)}>Delete</button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </section>
            )}

            {/* ─── TAB: CALL LOGS ───────────────────────────────────────── */}
            {activeTab === 'logs' && (
              <section className="glass db__panel-section">
                <div className="db__filters-bar">
                  <div className="search-box">
                    <input type="text" placeholder="Search caller or intent..."
                      value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
                  </div>
                  <div className="filter-group">
                    <select value={filterLang} onChange={e => setFilterLang(e.target.value)}>
                      <option value="all">All Languages</option>
                      <option value="english">English</option>
                      <option value="malayalam">Malayalam</option>
                    </select>
                    <select value={filterUser} onChange={e => setFilterUser(e.target.value)}>
                      <option value="all">All User Types</option>
                      <option value="student">Student</option>
                      <option value="prospective">Prospective</option>
                      <option value="unknown">Unknown</option>
                    </select>
                  </div>
                </div>
                <div className="table-responsive">
                  <table className="db__table">
                    <thead>
                      <tr>
                        <th>Call ID</th><th>Caller</th><th>User Type</th><th>Duration</th>
                        <th>Language</th><th>Intent</th><th>Outcome</th><th>Date & Time</th><th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredCalls.length === 0 ? (
                        <tr><td colSpan={9} className="no-data">No matching call logs found.</td></tr>
                      ) : (
                        filteredCalls.map(call => (
                          <tr key={call.call_id}>
                            <td><code>{call.call_id}</code></td>
                            <td>{formatValue(call.caller)}</td>
                            <td><span className="pill pill--user">{formatValue(call.user_type, 'unknown')}</span></td>
                            <td>{formatValue(call.duration)}</td>
                            <td>{formatValue(call.language)}</td>
                            <td><span className="pill pill--intent">{formatValue(call.intent, 'unknown')}</span></td>
                            <td><span className={`pill ${getOutcomeClass(call.outcome)}`}>{formatValue(call.outcome)}</span></td>
                            <td>{call.timestamp ? new Date(call.timestamp).toLocaleString() : 'N/A'}</td>
                            <td>
                              <button className="btn btn--ghost btn--sm" onClick={() => setSelectedCall(call)}>
                                View Transcript
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </section>
            )}

            {/* ─── TAB: LEADS ──────────────────────────────────────────── */}
            {activeTab === 'leads' && (
              <section className="glass db__panel-section">
                <div className="panel-header">
                  <h2>Captured Leads</h2>
                  <p className="form-helper">Review leads collected by the bot conversation flow and verify consent status.</p>
                </div>
                {leads.length === 0 ? (
                  <div className="no-data-panel glass">
                    <h3>No leads captured yet.</h3>
                    <p>Start a bot simulation and submit a qualified lead conversation to populate this list.</p>
                  </div>
                ) : (
                  <div className="table-responsive">
                    <table className="db__table">
                      <thead>
                        <tr>
                          <th>Lead ID</th><th>Name</th><th>Phone</th><th>Course</th>
                          <th>WhatsApp Consent</th><th>Language</th><th>Captured</th><th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {leads.map(lead => (
                          <tr key={lead.id}>
                            <td><code>{lead.id}</code></td>
                            <td>{lead.name}</td>
                            <td>{lead.phone}</td>
                            <td>{lead.course}</td>
                            <td>
                              <span className={`pill ${lead.consent_whatsapp ? 'pill--success' : 'pill--muted'}`}>
                                {lead.consent_whatsapp ? '✓ Yes' : 'No'}
                              </span>
                            </td>
                            <td>{lead.language}</td>
                            <td>{new Date(lead.created_at).toLocaleString()}</td>
                            <td>
                              <button className="btn btn--danger btn--sm" onClick={async () => {
                                if (!window.confirm('Delete this lead record?')) return
                                try {
                                  await deleteLead(lead.id)
                                  setLeads(prev => prev.filter(item => item.id !== lead.id))
                                } catch (err) {
                                  console.error(err)
                                  alert('Failed to delete lead record.')
                                }
                              }}>Delete</button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            )}

            {/* ─── TAB: KNOWLEDGE GAPS ─────────────────────────────────── */}
            {activeTab === 'gaps' && (
              <section className="glass db__panel-section">
                <p className="form-helper">
                  These questions were asked by callers but the bot found no matching FAQ or RAG context.
                  Resolve them by submitting answers below.
                </p>
                <div className="gaps-list">
                  {knowledgeGaps.length === 0 ? (
                    <div className="no-data-panel glass">
                      <h3>🎉 Clean Slate!</h3>
                      <p>All flagged knowledge gaps have been resolved and the bot is fully trained.</p>
                    </div>
                  ) : (
                    knowledgeGaps.map(gap => (
                      <div key={gap.id} className="gap-card glass">
                        <div className="gap-card__header">
                          <span className="gap-card__trigger">"{gap.question}"</span>
                          <span className="badge badge--error">{gap.frequency} times asked</span>
                        </div>
                        <div className="gap-card__body">
                          <div><strong>Category:</strong> {gap.category}</div>
                          <div><strong>First Spotted:</strong> {new Date(gap.first_seen).toLocaleDateString()}</div>
                        </div>
                        <div className="gap-card__actions">
                          <button className="btn btn--primary" onClick={() => {
                            setTrainingGap(gap)
                            setTrainingForm({ en: '', ml: '', category: gap.category })
                          }}>Teach Bot Response</button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </section>
            )}

            {/* ─── TAB: BOT TRAINING (Admin Proactive) ─────────────────── */}
            {activeTab === 'training' && (
              <section className="glass db__panel-section animate-fade-in-up">
                <div className="panel-header" style={{ marginBottom: '1.5rem' }}>
                  <div>
                    <h2>🧠 Admin Bot Training</h2>
                    <p className="form-helper">
                      Proactively train the bot with custom knowledge, outbound scripts, and personality settings.
                      Changes take effect immediately for all new conversations.
                    </p>
                  </div>
                </div>

                {/* Sub-tab navigation */}
                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
                  {[
                    { id: 'qa', label: '📝 Add Q&A' },
                    { id: 'bulk', label: '📦 Bulk Import' },
                    { id: 'outbound', label: '📤 Outbound Script' },
                    { id: 'personality', label: '🎭 Bot Personality' },
                    { id: 'voice', label: '🎙️ Voice Training' },

                  ].map(t => (
                    <button
                      key={t.id}
                      className={`btn ${trainingSubTab === t.id ? 'btn--primary' : 'btn--ghost'} btn--sm`}
                      onClick={() => setTrainingSubTab(t.id)}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>

                {/* ── Sub-tab: Custom Q&A ── */}
                {trainingSubTab === 'qa' && (
                  <div>
                    <h3 style={{ marginBottom: '0.75rem' }}>Add Custom Q&A to Bot Knowledge</h3>
                    <p className="form-helper" style={{ marginBottom: '1rem' }}>
                      Unlike the Knowledge Gaps tab (which shows what users asked), here you can add ANY question and answer proactively — before users even ask.
                    </p>
                    <form onSubmit={async (e) => {
                      e.preventDefault()
                      setTrainingQAStatus('saving')
                      try {
                        await addTrainingEntry(trainingQA)
                        setTrainingQAStatus('success')
                        setTrainingQA({ question_en: '', answer_en: '', question_ml: '', answer_ml: '', category: 'General' })
                        setTimeout(() => setTrainingQAStatus(null), 3000)
                      } catch (err) {
                        console.error(err)
                        setTrainingQAStatus('error')
                        setTimeout(() => setTrainingQAStatus(null), 3000)
                      }
                    }}>
                      <section className="glass db__form-section">
                        <div className="form-row">
                          <div className="form-group">
                            <label htmlFor="tqa-q-en">English Question</label>
                            <input id="tqa-q-en" value={trainingQA.question_en}
                              onChange={e => setTrainingQA(p => ({ ...p, question_en: e.target.value }))}
                              placeholder="e.g. What is the fee for MERN Stack course?" required />
                          </div>
                          <div className="form-group">
                            <label htmlFor="tqa-q-ml">Malayalam Question (optional)</label>
                            <input id="tqa-q-ml" value={trainingQA.question_ml}
                              onChange={e => setTrainingQA(p => ({ ...p, question_ml: e.target.value }))}
                              placeholder="Optional Malayalam question" />
                          </div>
                        </div>
                        <div className="form-row">
                          <div className="form-group">
                            <label htmlFor="tqa-a-en">English Answer (bot will speak this)</label>
                            <textarea id="tqa-a-en" rows={4} value={trainingQA.answer_en}
                              onChange={e => setTrainingQA(p => ({ ...p, answer_en: e.target.value }))}
                              placeholder="e.g. The MERN Stack course fee is ₹35,000 with EMI options available..." required />
                          </div>
                          <div className="form-group">
                            <label htmlFor="tqa-a-ml">Malayalam Answer (optional)</label>
                            <textarea id="tqa-a-ml" rows={4} value={trainingQA.answer_ml}
                              onChange={e => setTrainingQA(p => ({ ...p, answer_ml: e.target.value }))}
                              placeholder="Optional Malayalam answer" />
                          </div>
                        </div>
                        <div className="form-group">
                          <label htmlFor="tqa-cat">Category</label>
                          <select id="tqa-cat" value={trainingQA.category}
                            onChange={e => setTrainingQA(p => ({ ...p, category: e.target.value }))}>
                            <option value="General">General</option>
                            <option value="Course Info">Course Info</option>
                            <option value="Fees">Fees</option>
                            <option value="Admissions">Admissions</option>
                            <option value="Student Support">Student Support</option>
                            <option value="Placement">Placement</option>
                          </select>
                        </div>
                      </section>
                      <div className="form-actions">
                        <button type="submit" className="btn btn--primary" disabled={trainingQAStatus === 'saving'}>
                          {trainingQAStatus === 'saving' ? '⏳ Saving…' : '🧠 Train Bot with this Q&A'}
                        </button>
                        {trainingQAStatus === 'success' && <span className="badge badge--success">✔ Bot trained!</span>}
                        {trainingQAStatus === 'error' && <span className="badge badge--error">✖ Save failed</span>}
                      </div>
                    </form>
                  </div>
                )}

                {/* ── Sub-tab: Bulk Import ── */}
                {trainingSubTab === 'bulk' && (
                  <div>
                    <h3 style={{ marginBottom: '0.75rem' }}>Bulk Import Q&A Pairs</h3>
                    <p className="form-helper" style={{ marginBottom: '1rem' }}>
                      Paste JSON array of Q&A pairs to import multiple entries at once. Max 100 per import.
                    </p>
                    <section className="glass db__form-section">
                      <div className="form-group">
                        <label htmlFor="bulk-json">JSON Q&A Array</label>
                        <textarea id="bulk-json" rows={10}
                          value={bulkText}
                          onChange={e => setBulkText(e.target.value)}
                          placeholder={`[\n  {\n    "question_en": "What courses do you offer?",\n    "answer_en": "We offer MERN Stack, Python, Flutter, Data Science and UI/UX Design.",\n    "category": "Course Info"\n  },\n  {\n    "question_en": "What is the course duration?",\n    "answer_en": "Courses run 8-10 months with daily practical sessions.",\n    "category": "Course Info"\n  }\n]`}
                          style={{ fontFamily: 'monospace', fontSize: '0.82rem' }}
                        />
                      </div>
                    </section>
                    <div className="form-actions">
                      <button
                        className="btn btn--primary"
                        disabled={bulkStatus === 'saving'}
                        onClick={async () => {
                          setBulkStatus('saving')
                          try {
                            const entries = JSON.parse(bulkText)
                            if (!Array.isArray(entries)) throw new Error('Must be a JSON array')
                            await bulkTrainingImport(entries)
                            setBulkStatus('success')
                            setBulkText('')
                            setTimeout(() => setBulkStatus(null), 3000)
                          } catch (err) {
                            console.error(err)
                            setBulkStatus('error')
                            setTimeout(() => setBulkStatus(null), 4000)
                          }
                        }}
                      >
                        {bulkStatus === 'saving' ? '⏳ Importing…' : '📦 Import All Entries'}
                      </button>
                      {bulkStatus === 'success' && <span className="badge badge--success">✔ Import successful!</span>}
                      {bulkStatus === 'error' && <span className="badge badge--error">✖ Import failed — check JSON format</span>}
                    </div>
                  </div>
                )}

                {/* ── Sub-tab: Outbound Script ── */}
                {trainingSubTab === 'outbound' && (
                  <div>
                    <h3 style={{ marginBottom: '0.75rem' }}>Configure Outbound Call Script</h3>
                    <p className="form-helper" style={{ marginBottom: '1rem' }}>
                      This message is what the bot speaks when it places an outbound call and the recipient picks up.
                      Set this before running outbound campaigns.
                    </p>
                    <form onSubmit={async (e) => {
                      e.preventDefault()
                      setOutboundScriptStatus('saving')
                      try {
                        await setOutboundScript(outboundScript)
                        setOutboundScriptStatus('success')
                        setTimeout(() => setOutboundScriptStatus(null), 3000)
                      } catch (err) {
                        console.error(err)
                        setOutboundScriptStatus('error')
                        setTimeout(() => setOutboundScriptStatus(null), 3000)
                      }
                    }}>
                      <section className="glass db__form-section">
                        <div className="form-row">
                          <div className="form-group">
                            <label htmlFor="ob-name">Agent Name</label>
                            <input id="ob-name" value={outboundScript.agent_name}
                              onChange={e => setOutboundScript(p => ({ ...p, agent_name: e.target.value }))}
                              placeholder="e.g. Priya from Bridgeon Admissions" />
                          </div>
                          <div className="form-group">
                            <label htmlFor="ob-purpose">Call Purpose</label>
                            <select id="ob-purpose" value={outboundScript.purpose}
                              onChange={e => setOutboundScript(p => ({ ...p, purpose: e.target.value }))}>
                              <option value="admissions">Admissions Outreach</option>
                              <option value="follow_up">Lead Follow-up</option>
                              <option value="event">Event Invitation</option>
                              <option value="feedback">Feedback Collection</option>
                            </select>
                          </div>
                        </div>
                        <div className="form-group">
                          <label htmlFor="ob-msg-en">Opening Message (English)</label>
                          <textarea id="ob-msg-en" rows={4} value={outboundScript.opening_message_en}
                            onChange={e => setOutboundScript(p => ({ ...p, opening_message_en: e.target.value }))}
                            placeholder="e.g. Hello! This is Priya calling from Bridgeon Skillversity. We're reaching out to share our upcoming MERN Stack batch starting next month..."
                            required />
                        </div>
                        <div className="form-group">
                          <label htmlFor="ob-msg-ml">Opening Message (Malayalam — optional)</label>
                          <textarea id="ob-msg-ml" rows={4} value={outboundScript.opening_message_ml}
                            onChange={e => setOutboundScript(p => ({ ...p, opening_message_ml: e.target.value }))}
                            placeholder="Optional Malayalam opening message..." />
                        </div>
                      </section>
                      <div className="form-actions">
                        <button type="submit" className="btn btn--primary" disabled={outboundScriptStatus === 'saving'}>
                          {outboundScriptStatus === 'saving' ? '⏳ Saving…' : '📤 Save Outbound Script'}
                        </button>
                        {outboundScriptStatus === 'success' && <span className="badge badge--success">✔ Saved!</span>}
                        {outboundScriptStatus === 'error' && <span className="badge badge--error">✖ Save failed</span>}
                      </div>
                    </form>
                  </div>
                )}

                {/* ── Sub-tab: Bot Personality ── */}
                {trainingSubTab === 'personality' && (
                  <div>
                    <h3 style={{ marginBottom: '0.75rem' }}>Bot Personality & Tone</h3>
                    <p className="form-helper" style={{ marginBottom: '1rem' }}>
                      Customize how the bot introduces itself and communicates. Changes apply to new conversations immediately.
                    </p>
                    <form onSubmit={async (e) => {
                      e.preventDefault()
                      setPersonalityStatus('saving')
                      try {
                        await setBotPersonality(personality)
                        setPersonalityStatus('success')
                        setTimeout(() => setPersonalityStatus(null), 3000)
                      } catch (err) {
                        console.error(err)
                        setPersonalityStatus('error')
                        setTimeout(() => setPersonalityStatus(null), 3000)
                      }
                    }}>
                      <section className="glass db__form-section">
                        <div className="form-row">
                          <div className="form-group">
                            <label htmlFor="pers-name">Bot Name</label>
                            <input id="pers-name" value={personality.bot_name}
                              onChange={e => setPersonality(p => ({ ...p, bot_name: e.target.value }))}
                              placeholder="e.g. Priya, Arjun, Alex" />
                          </div>
                          <div className="form-group">
                            <label htmlFor="pers-tone">Communication Tone</label>
                            <select id="pers-tone" value={personality.tone}
                              onChange={e => setPersonality(p => ({ ...p, tone: e.target.value }))}>
                              <option value="friendly">Friendly & Warm</option>
                              <option value="professional">Professional</option>
                              <option value="formal">Formal</option>
                              <option value="casual">Casual & Conversational</option>
                            </select>
                          </div>
                        </div>
                        <div className="form-group">
                          <label htmlFor="pers-lang">Language Style</label>
                          <select id="pers-lang" value={personality.language_style}
                            onChange={e => setPersonality(p => ({ ...p, language_style: e.target.value }))}>
                            <option value="pure_english">Pure English</option>
                            <option value="hinglish">Hinglish (Hindi-English mix)</option>
                            <option value="mixed">Mixed (English + regional where needed)</option>
                          </select>
                        </div>
                      </section>
                      <div className="form-actions">
                        <button type="submit" className="btn btn--primary" disabled={personalityStatus === 'saving'}>
                          {personalityStatus === 'saving' ? '⏳ Saving…' : '🎭 Update Bot Personality'}
                        </button>
                        {personalityStatus === 'success' && <span className="badge badge--success">✔ Personality updated!</span>}
                        {personalityStatus === 'error' && <span className="badge badge--error">✖ Save failed</span>}
                      </div>
                    </form>
                  </div>
                )}

                {/* ── Sub-tab: Voice Training ── */}
                {trainingSubTab === 'voice' && (
                  <div className="voice-train-panel animate-fade-in-up">
                    <div className="voice-train-header" style={{ marginBottom: '1.5rem' }}>
                      <h3 style={{ marginBottom: '0.5rem' }}>🎙️ Voice-to-Train Interactive Mode</h3>
                      <p className="form-helper">
                        Record a new FAQ entry directly using your voice. Speak the question, then speak the answer, and submit.
                      </p>
                    </div>

                    <div className="voice-train-controls glass" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
                      <div className="form-row" style={{ gap: '1.5rem', marginBottom: '1.5rem' }}>
                        <div className="form-group" style={{ flex: 1 }}>
                          <label htmlFor="voice-lang">Language of Speech</label>
                          <select
                            id="voice-lang"
                            value={voiceTranscriptLang}
                            onChange={(e) => setVoiceTranscriptLang(e.target.value)}
                            disabled={voiceRecording || voiceTrainingStep !== 'idle'}
                          >
                            <option value="en">English (US/India)</option>
                            <option value="ml">Malayalam (മലയാളം)</option>
                          </select>
                        </div>
                        <div className="form-group" style={{ flex: 1 }}>
                          <label htmlFor="voice-category">Knowledge Category</label>
                          <select
                            id="voice-category"
                            value={voiceTrainingCategory}
                            onChange={(e) => setVoiceTrainingCategory(e.target.value)}
                            disabled={voiceTrainingStatus === 'saving'}
                          >
                            <option value="General">General</option>
                            <option value="Course Info">Course Info</option>
                            <option value="Fees">Fees</option>
                            <option value="Admissions">Admissions</option>
                            <option value="Student Support">Student Support</option>
                            <option value="Placement">Placement</option>
                          </select>
                        </div>
                      </div>

                      {/* Step Progress Indicator */}
                      <div className="voice-steps-progress">
                        <div className={`step-dot ${voiceTrainingStep === 'idle' ? 'active' : ''}`}>
                          <span>1</span> Speak Question
                        </div>
                        <div className={`step-line ${['recording-a', 'review'].includes(voiceTrainingStep) ? 'completed' : ''}`} />
                        <div className={`step-dot ${voiceTrainingStep === 'recording-a' ? 'active' : ''}`}>
                          <span>2</span> Speak Answer
                        </div>
                        <div className={`step-line ${voiceTrainingStep === 'review' ? 'completed' : ''}`} />
                        <div className={`step-dot ${voiceTrainingStep === 'review' ? 'active' : ''}`}>
                          <span>3</span> Review & Train
                        </div>
                      </div>
                    </div>

                    {/* Step 1: Record Question */}
                    {voiceTrainingStep === 'idle' && (
                      <div className="voice-train-step glass animate-fade-in-up" style={{ padding: '2.5rem' }}>
                        <h4 style={{ marginBottom: '1rem', textAlign: 'center' }}>Step 1: Speak or Type the FAQ Question</h4>
                        <p style={{ opacity: 0.8, marginBottom: '2rem', textAlign: 'center' }}>
                          Click the microphone to speak the question in <strong>{voiceTranscriptLang === 'ml' ? 'Malayalam' : 'English'}</strong>, or type it directly below.
                        </p>

                        <div className="mic-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
                          <button
                            type="button"
                            className={`mic-btn ${voiceRecording ? 'mic-btn--recording' : ''}`}
                            onClick={() => voiceRecording ? stopVoiceRecording() : startVoiceRecording('question')}
                            aria-label={voiceRecording ? 'Stop recording question' : 'Start recording question'}
                          >
                            {voiceRecording ? '⏹️' : '🎙️'}
                          </button>
                          {voiceRecording && (
                            <div className="voice-wave">
                              <span className="wave-bar bar-1" />
                              <span className="wave-bar bar-2" />
                              <span className="wave-bar bar-3" />
                              <span className="wave-bar bar-4" />
                            </div>
                          )}
                          <span style={{ fontSize: '0.88rem', fontWeight: '500', opacity: 0.75 }}>
                            {voiceRecording ? 'Listening... Press square button to finish' : 'Press mic to record question'}
                          </span>
                        </div>

                        <div className="form-group" style={{ marginBottom: '2rem' }}>
                          <label htmlFor="voice-q-input">Question Text</label>
                          <input
                            id="voice-q-input"
                            type="text"
                            value={voiceTrainingQ}
                            onChange={(e) => setVoiceTrainingQ(e.target.value)}
                            placeholder="Type or speak the question..."
                            style={{ width: '100%' }}
                          />
                        </div>

                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
                          <button
                            type="button"
                            className="btn btn--primary"
                            onClick={() => setVoiceTrainingStep('recording-a')}
                            disabled={!voiceTrainingQ.trim()}
                          >
                            Next Step (Record Answer) &rarr;
                          </button>
                          {voiceTrainingQ && (
                            <button
                              type="button"
                              className="btn btn--ghost"
                              onClick={() => setVoiceTrainingQ('')}
                            >
                              Clear
                            </button>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Step 2: Record Answer */}
                    {voiceTrainingStep === 'recording-a' && (
                      <div className="voice-train-step glass animate-fade-in-up" style={{ padding: '2.5rem' }}>
                        <h4 style={{ marginBottom: '1rem', textAlign: 'center' }}>Step 2: Speak or Type the FAQ Answer</h4>
                        <p style={{ opacity: 0.8, marginBottom: '2rem', textAlign: 'center' }}>
                          Click the microphone to speak the bot's response in <strong>{voiceTranscriptLang === 'ml' ? 'Malayalam' : 'English'}</strong>, or type it directly below.
                        </p>

                        <div className="mic-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
                          <button
                            type="button"
                            className={`mic-btn ${voiceRecording ? 'mic-btn--recording' : ''}`}
                            onClick={() => voiceRecording ? stopVoiceRecording() : startVoiceRecording('answer')}
                            aria-label={voiceRecording ? 'Stop recording answer' : 'Start recording answer'}
                          >
                            {voiceRecording ? '⏹️' : '🎙️'}
                          </button>
                          {voiceRecording && (
                            <div className="voice-wave">
                              <span className="wave-bar bar-1" />
                              <span className="wave-bar bar-2" />
                              <span className="wave-bar bar-3" />
                              <span className="wave-bar bar-4" />
                            </div>
                          )}
                          <span style={{ fontSize: '0.88rem', fontWeight: '500', opacity: 0.75 }}>
                            {voiceRecording ? 'Listening... Press square button to finish' : 'Press mic to record answer'}
                          </span>
                        </div>

                        <div className="form-group" style={{ marginBottom: '2rem' }}>
                          <label htmlFor="voice-a-input">Answer Text</label>
                          <textarea
                            id="voice-a-input"
                            value={voiceTrainingA}
                            onChange={(e) => setVoiceTrainingA(e.target.value)}
                            placeholder="Type or speak the answer..."
                            rows={4}
                            style={{ width: '100%', resize: 'vertical' }}
                          />
                        </div>

                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
                          <button
                            type="button"
                            className="btn btn--primary"
                            onClick={() => setVoiceTrainingStep('review')}
                            disabled={!voiceTrainingA.trim()}
                          >
                            Review Q&A Entry &rarr;
                          </button>
                          <button
                            type="button"
                            className="btn btn--ghost"
                            onClick={() => setVoiceTrainingStep('idle')}
                          >
                            &larr; Back to Question
                          </button>
                          {voiceTrainingA && (
                            <button
                              type="button"
                              className="btn btn--ghost"
                              onClick={() => setVoiceTrainingA('')}
                            >
                              Clear
                            </button>
                          )}
                        </div>
                      </div>
                    )}


                    {/* Step 3: Review and Train */}
                    {voiceTrainingStep === 'review' && (
                      <form onSubmit={handleVoiceTrainingSubmit} className="voice-train-step glass animate-fade-in-up" style={{ padding: '2rem' }}>
                        <h4 style={{ marginBottom: '1.5rem' }}>Step 3: Review Transcribed FAQ Entry</h4>
                        <p className="form-helper" style={{ marginBottom: '1.5rem' }}>
                          Review and edit the voice transcriptions before publishing to the knowledge base.
                        </p>

                        <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                          <label htmlFor="voice-q-edit">Question text</label>
                          <input
                            id="voice-q-edit"
                            type="text"
                            value={voiceTrainingQ}
                            onChange={(e) => setVoiceTrainingQ(e.target.value)}
                            required
                            style={{ width: '100%' }}
                          />
                        </div>

                        <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                          <label htmlFor="voice-a-edit">Answer text</label>
                          <textarea
                            id="voice-a-edit"
                            value={voiceTrainingA}
                            onChange={(e) => setVoiceTrainingA(e.target.value)}
                            rows={4}
                            required
                            style={{ width: '100%', resize: 'vertical' }}
                          />
                        </div>

                        <div className="form-actions" style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', marginTop: '2rem' }}>
                          <button
                            type="submit"
                            className="btn btn--primary"
                            disabled={voiceTrainingStatus === 'saving'}
                          >
                            {voiceTrainingStatus === 'saving' ? '⏳ Saving...' : '🧠 Train Bot with this Voice Q&A'}
                          </button>
                          <button
                            type="button"
                            className="btn btn--ghost"
                            onClick={() => {
                              setVoiceTrainingStep('recording-a')
                            }}
                          >
                            &larr; Re-record Answer
                          </button>
                          <button
                            type="button"
                            className="btn btn--ghost"
                            onClick={() => {
                              setVoiceTrainingQ('')
                              setVoiceTrainingA('')
                              setVoiceTrainingStep('idle')
                            }}
                            style={{ color: 'var(--clr-danger)' }}
                          >
                            Reset Form
                          </button>

                          {voiceTrainingStatus === 'success' && <span className="badge badge--success">✔ Bot trained!</span>}
                          {voiceTrainingStatus === 'error' && <span className="badge badge--error">✖ Train failed</span>}
                        </div>
                      </form>
                    )}

                    {voiceTrainingStatus === 'transcribing' && (
                      <div className="voice-transcribe-loading glass" style={{ marginTop: '1rem', padding: '1rem', textAlign: 'center', background: 'rgba(0,0,0,0.2)' }}>
                        <div className="spinner spinner--sm" style={{ display: 'inline-block', marginRight: '0.5rem' }} />
                        <span>Transcribing audio server-side... Please wait.</span>
                      </div>
                    )}
                  </div>
                )}


              </section>
            )}

            {/* ─── TAB: AUDIT LOGS (Phase 11) ─────────────────────────── */}
            {activeTab === 'audit' && (
              <section className="glass db__panel-section animate-fade-in-up">
                <div className="panel-header">
                  <h2>Security Audit Trail</h2>
                  <p className="form-helper">In compliance with DPDPA 2023. Track all administrative updates, settings changes, and credentials verification.</p>
                </div>
                <div className="table-responsive">
                  <table className="db__table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Action Performed</th>
                        <th>Operator</th>
                        <th>Target / Details</th>
                      </tr>
                    </thead>
                    <tbody>
                      {auditLogs.length === 0 ? (
                        <tr><td colSpan={4} className="no-data">No audit logs recorded yet.</td></tr>
                      ) : (
                        auditLogs.map((log, index) => (
                          <tr key={log.id ?? index}>
                            <td>{new Date(log.timestamp).toLocaleString()}</td>
                            <td style={{ fontWeight: '500' }}>{log.action}</td>
                            <td><span className="pill pill--user">{log.actor ?? 'system'}</span></td>
                            <td><code style={{ fontSize: '0.78rem', opacity: 0.75 }}>{log.target ?? log.details ?? '—'}</code></td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </section>
            )}


            {/* ─── TAB: CAMPAIGNS ────────────────────────────────────────── */}
            {activeTab === 'campaigns' && (
              <>
                {/* Campaign Creation Form */}
                <section className="db__form-section">
                  <h2>📣 Create Outbound Campaign</h2>
                  <form onSubmit={(e) => handleCampaignSubmit(e, false)}>
                    <div className="form-row">
                      <div className="form-group">
                        <label>Campaign Name</label>
                        <input
                          type="text"
                          required
                          value={campaignForm.name}
                          onChange={(e) => setCampaignForm({ ...campaignForm, name: e.target.value })}
                          placeholder="e.g. June Batch Follow-Up"
                        />
                      </div>
                      <div className="form-group">
                        <label>Channel</label>
                        <select
                          value={campaignForm.channel}
                          onChange={(e) => setCampaignForm({ ...campaignForm, channel: e.target.value })}
                        >
                          <option value="voice">📞 Voice Call</option>
                          <option value="whatsapp">💬 WhatsApp</option>
                          <option value="sms">📱 SMS</option>
                          <option value="email">📧 Email</option>
                        </select>
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>Schedule Date & Time</label>
                        <input
                          type="datetime-local"
                          value={campaignForm.schedule_time}
                          onChange={(e) => setCampaignForm({ ...campaignForm, schedule_time: e.target.value })}
                        />
                      </div>
                      <div className="form-group">
                        <label>Max Retry Attempts</label>
                        <select
                          value={campaignForm.retry_attempts}
                          onChange={(e) => setCampaignForm({ ...campaignForm, retry_attempts: parseInt(e.target.value) })}
                        >
                          <option value="1">1 attempt</option>
                          <option value="2">2 attempts</option>
                          <option value="3">3 attempts (recommended)</option>
                        </select>
                      </div>
                    </div>
                    <div className="form-group">
                      <label>Campaign Script / Message</label>
                      <textarea
                        rows={4}
                        value={campaignForm.script}
                        onChange={(e) => setCampaignForm({ ...campaignForm, script: e.target.value })}
                        placeholder="Hello, this is Bridgeon Skillversity calling. We noticed you enquired about our courses and we'd love to help you enroll..."
                      />
                      <span className="form-helper">This script will be used by the AI during outbound calls or adapted for WhatsApp/SMS.</span>
                    </div>
                    <div className="form-row">
                      <div className="toggle-row">
                        <div className="toggle-row__label">
                          <span>Consent Required</span>
                          <span>Only contact leads who have explicitly opted in</span>
                        </div>
                        <input
                          type="checkbox"
                          checked={campaignForm.consent_required}
                          onChange={(e) => setCampaignForm({ ...campaignForm, consent_required: e.target.checked })}
                          style={{ width: 18, height: 18, accentColor: 'var(--clr-brand)' }}
                        />
                      </div>
                      <div className="toggle-row">
                        <div className="toggle-row__label">
                          <span>DND Compliance</span>
                          <span>Skip numbers registered on DND registry</span>
                        </div>
                        <input
                          type="checkbox"
                          checked={campaignForm.dnd_compliance}
                          onChange={(e) => setCampaignForm({ ...campaignForm, dnd_compliance: e.target.checked })}
                          style={{ width: 18, height: 18, accentColor: 'var(--clr-brand)' }}
                        />
                      </div>
                    </div>
                    {campaignStatus === 'success' && <div className="status-banner banner--success" style={{ margin: '1rem 0', padding: '0.75rem', borderRadius: '8px', background: 'rgba(52,211,153,0.1)', color: '#34d399', border: '1px solid rgba(52,211,153,0.25)' }}>Campaign created successfully!</div>}
                    {campaignStatus === 'error' && <div className="status-banner banner--error" style={{ margin: '1rem 0', padding: '0.75rem', borderRadius: '8px', background: 'rgba(239,68,68,0.1)', color: 'var(--clr-danger)', border: '1px solid rgba(239,68,68,0.25)' }}>Failed to create campaign.</div>}
                    <div className="form-actions">
                      <button type="button" className="btn btn--ghost" onClick={(e) => handleCampaignSubmit(e, false)}>
                        Save as Draft
                      </button>
                      <button type="submit" className="btn btn--primary" onClick={(e) => handleCampaignSubmit(e, true)}>
                        🚀 Run Campaign Now
                      </button>
                    </div>
                  </form>
                </section>

                {/* Existing Campaigns */}
                <section className="db__panel-section">
                  <div className="panel-header">
                    <h2>📋 Active & Recent Campaigns</h2>
                    <span className="badge badge--info">{campaigns.length} campaigns</span>
                  </div>
                  <div className="campaign-list">
                    {campaigns.map((c) => (
                      <div key={c.id || c.name} className="campaign-card">
                        <div>
                          <div className="campaign-card__name">
                            {c.channel === 'voice' ? '📞' : c.channel === 'whatsapp' ? '💬' : c.channel === 'sms' ? '📱' : '📧'} {c.name}
                          </div>
                          <div className="campaign-card__meta">
                            <span className={`campaign-status status--${c.status.toLowerCase()}`}>
                              {c.status.toLowerCase() === 'running' && '🟢 Running'}
                              {c.status.toLowerCase() === 'scheduled' && '🔵 Scheduled'}
                              {c.status.toLowerCase() === 'completed' && '✅ Completed'}
                              {c.status.toLowerCase() === 'paused' && '⏸ Paused'}
                              {c.status.toLowerCase() === 'draft' && '📝 Draft'}
                            </span>
                          </div>
                        </div>
                        <div className="campaign-card__stats">
                          <div className="campaign-stat">
                            <span className="campaign-stat-val gradient-text">{c.contacted}</span>
                            <span className="campaign-stat-lbl">Dialled</span>
                          </div>
                          <div className="campaign-stat">
                            <span className="campaign-stat-val" style={{ color: '#34d399' }}>{c.answered}</span>
                            <span className="campaign-stat-lbl">Answered</span>
                          </div>
                          <div className="campaign-stat">
                            <span className="campaign-stat-val" style={{ color: 'var(--clr-amber)' }}>{c.converted}</span>
                            <span className="campaign-stat-lbl">Converted</span>
                          </div>
                        </div>
                        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                          {(c.status.toLowerCase() === 'running' || c.status.toLowerCase() === 'paused') && (
                            <button 
                              className="btn btn--ghost btn--sm" 
                              onClick={() => handleUpdateCampaignStatus(c.id, c.status)}
                            >
                              {c.status.toLowerCase() === 'running' ? '⏸ Pause' : '▶️ Resume'}
                            </button>
                          )}
                          <button 
                            className="btn btn--danger btn--sm"
                            onClick={() => handleDeleteCampaign(c.id)}
                          >
                            🗑 Delete
                          </button>
                        </div>
                      </div>
                    ))}
                    {campaigns.length === 0 && (
                      <div className="no-data" style={{ padding: 'var(--space-8)' }}>
                        <div style={{ fontSize: '2rem', marginBottom: 'var(--space-3)' }}>📣</div>
                        <p>No campaigns created yet. Create your first outbound campaign above.</p>
                      </div>
                    )}
                  </div>
                </section>

                {/* Multi-Channel Status */}
                <section className="db__panel-section">
                  <div className="panel-header">
                    <h2>🔗 Multi-Channel Integration Status</h2>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 'var(--space-4)' }}>
                    {integrations.map((ch) => (
                      <div key={ch.name} style={{ background: 'var(--bg-card)', border: `1px solid ${ch.ok ? 'rgba(52,211,153,0.25)' : 'var(--border)'}`, borderRadius: 'var(--radius-lg)', padding: 'var(--space-5)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-3)' }}>
                          <span style={{ fontSize: '1.5rem' }}>{ch.icon}</span>
                          <span className={`badge ${ch.ok ? 'badge--ok' : 'badge--warning'}`}>{ch.status}</span>
                        </div>
                        <div style={{ fontWeight: 700, fontSize: '0.95rem', marginBottom: 'var(--space-1)' }}>{ch.name}</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--txt-muted)' }}>{ch.desc}</div>
                        <button className="btn btn--ghost btn--sm" style={{ marginTop: 'var(--space-4)', width: '100%' }}>Configure →</button>
                      </div>
                    ))}
                    {integrations.length === 0 && (
                      <div style={{ gridColumn: '1 / -1', textAlign: 'center', color: 'var(--txt-muted)', padding: '2rem' }}>
                        Checking integration status...
                      </div>
                    )}
                  </div>
                </section>

              </>
            )}

          </div>
        )}
      </main>

      {/* ── Transcript Modal ─────────────────────────────────────────────── */}
      {selectedCall && (
        <div className="modal-overlay" onClick={() => setSelectedCall(null)}>
          <div className="modal-card glass" onClick={e => e.stopPropagation()}>
            <header className="modal-header">
              <h2>Call Transcript: {selectedCall.call_id}</h2>
              <button className="close-btn" onClick={() => setSelectedCall(null)} aria-label="Close">&times;</button>
            </header>
            <div className="modal-metadata">
              <div><strong>Caller:</strong> {selectedCall.caller}</div>
              <div><strong>User Type:</strong> {selectedCall.user_type}</div>
              <div><strong>Language:</strong> {selectedCall.language}</div>
              <div><strong>Outcome:</strong> {selectedCall.outcome}</div>
            </div>
            <div className="modal-transcript-feed">
              <div className="chat-msg chat-msg--bot">
                <span className="chat-avatar">🤖</span>
                <div className="chat-bubble">
                  {selectedCall.language === 'Malayalam'
                    ? 'Namaskaram! Bridgeon Skillversity-ilekku swagatham. Are you a current student or exploring courses?'
                    : 'Hello! Welcome to Bridgeon Skillversity. Are you a current student or exploring courses?'}
                </div>
              </div>
              <div className="chat-msg chat-msg--user">
                <span className="chat-avatar">👤</span>
                <div className="chat-bubble">
                  {selectedCall.intent === 'placement_queries' && 'Placement cells records are there? Salary package range please.'}
                  {selectedCall.intent === 'batch_schedule' && 'What is the schedule for React class this week?'}
                  {selectedCall.intent === 'fee_structure' && 'I want course duration and total fees.'}
                  {selectedCall.intent === 'greeting_only' && 'Hello? Hello?'}
                </div>
              </div>
              <div className="chat-msg chat-msg--bot">
                <span className="chat-avatar">🤖</span>
                <div className="chat-bubble">
                  {selectedCall.intent === 'placement_queries' && 'We offer comprehensive placement support. Average packages range from 2.5 LPA to 4.9+ LPA. Would you like me to schedule a callback with admissions?'}
                  {selectedCall.intent === 'batch_schedule' && 'Your batch classes are scheduled Monday to Friday from 10 AM to 1 PM.'}
                  {selectedCall.intent === 'fee_structure' && 'Course durations are typically 8 to 10 months. Fees vary by course. Shall I schedule a callback?'}
                  {selectedCall.intent === 'greeting_only' && 'Welcome to Bridgeon. How can I help you today?'}
                </div>
              </div>
            </div>
            <footer className="modal-footer">
              <button className="btn btn--primary" onClick={() => setSelectedCall(null)}>Close View</button>
            </footer>
          </div>
        </div>
      )}

      {/* ── Training Modal ────────────────────────────────────────────────── */}
      {trainingGap && (
        <div className="modal-overlay" onClick={() => setTrainingGap(null)}>
          <div className="modal-card glass" onClick={e => e.stopPropagation()}>
            <header className="modal-header">
              <h2>Teach Bot: Knowledge Gap</h2>
              <button className="close-btn" onClick={() => setTrainingGap(null)} aria-label="Close">&times;</button>
            </header>
            <form onSubmit={handleTrainSubmit}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Trigger Question (Caller query)</label>
                  <input type="text" value={trainingGap.question} readOnly className="input-readonly" />
                </div>
                <div className="form-group">
                  <label htmlFor="train-en">English Response Spoken by Bot</label>
                  <textarea id="train-en" value={trainingForm.en}
                    onChange={e => setTrainingForm({ ...trainingForm, en: e.target.value })}
                    rows={3} placeholder="Enter bot response in English..." required />
                </div>
                <div className="form-group">
                  <label htmlFor="train-ml">Malayalam Response Spoken by Bot</label>
                  <textarea id="train-ml" value={trainingForm.ml}
                    onChange={e => setTrainingForm({ ...trainingForm, ml: e.target.value })}
                    rows={3} placeholder="Enter bot response in Malayalam..." required />
                </div>
                <div className="form-group">
                  <label htmlFor="train-category">Knowledge Category</label>
                  <select id="train-category" value={trainingForm.category}
                    onChange={e => setTrainingForm({ ...trainingForm, category: e.target.value })}>
                    <option value="Course Info">Course Info</option>
                    <option value="Fees">Fees</option>
                    <option value="Admissions">Admissions</option>
                    <option value="Student Support">Student Support</option>
                    <option value="General">General</option>
                  </select>
                </div>
              </div>
              <footer className="modal-footer">
                <button type="button" className="btn btn--ghost" onClick={() => setTrainingGap(null)}>Cancel</button>
                <button type="submit" className="btn btn--primary">Publish Knowledge</button>
              </footer>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
