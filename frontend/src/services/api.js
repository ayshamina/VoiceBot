/**
 * api.js — Central API helper for the Bridgeon Voice Bot frontend.
 *
 * Connects to FastAPI backend on http://127.0.0.1:8000
 * Uses Vite proxy in dev (/api/v1) with automatic fallback to direct URL.
 */

const DIRECT_BACKEND = 'http://127.0.0.1:8000/api/v1'

const getBackendUrl = () => {
  const envUrl = import.meta.env.VITE_API_BASE_URL
  if (envUrl) return envUrl.replace(/\/$/, '')
  // Use Vite proxy path in dev, direct URL as fallback
  return import.meta.env.DEV ? '/api/v1' : DIRECT_BACKEND
}

let BASE_URL = getBackendUrl()
let useDirectBackend = false


function getAuthHeaders() {
  const token = sessionStorage.getItem('voicebot_admin_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request(path, options = {}, { auth = false, retryDirect = true } = {}) {
  const headers = {
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true',
  }
  if (auth) {
    Object.assign(headers, getAuthHeaders())
  }
  if (options.headers) {
    Object.assign(headers, options.headers)
  }

  const url = `${BASE_URL}${path}`

  try {
    const res = await fetch(url, { ...options, headers })
    if (!res.ok) {
      const text = await res.text()
      throw new Error(`API error ${res.status}: ${text}`)
    }
    const contentType = res.headers.get('content-type') || ''
    if (contentType.includes('application/json')) {
      return res.json()
    }
    return res
  } catch (err) {
    // If Vite proxy fails, retry against backend directly once
    if (retryDirect && !useDirectBackend && typeof window !== 'undefined') {
      BASE_URL = DIRECT_BACKEND
      useDirectBackend = true
      return request(path, options, { auth, retryDirect: false })
    }
    throw err
  }
}

// ── Health ─────────────────────────────────────────────────────────────────
/** GET /api/v1/health — liveness probe */
export const getHealth = () => request('/health')

/** GET /api/v1/health/ready — readiness probe */
export const getReadiness = () => request('/health/ready')

// ── Voice & Telephony Status ───────────────────────────────────────────────
/** GET /api/v1/voice/status — voice API configuration */
export const getVoiceStatus = () => request('/voice/status')

/** GET /api/v1/telephony/status — telephony adapter status */
export const getTelephonyStatus = () => request('/telephony/status')

// ── STT / TTS ─────────────────────────────────────────────────────────────
/** POST /api/v1/voice/transcribe — server-side STT (Sarvam AI or OpenAI Whisper) */
export const transcribeAudio = (audioBase64, language = 'en') => request('/voice/transcribe', {
  method: 'POST',
  body: JSON.stringify({ audio_base64: audioBase64, language }),
})

/** POST /api/v1/voice/synthesize/json — server-side TTS as base64 JSON */
export const synthesizeSpeech = async (text, language = 'en') => {
  const headers = {
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true',
  }
  const url = `${BASE_URL}/voice/synthesize/json`
  const res = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify({ text, language }),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(detail || `TTS failed (${res.status})`)
  }
  return res.json()
}

// ── Dashboard ──────────────────────────────────────────────────────────────
/** GET /api/v1/dashboard/stats — dashboard stats & live calls */
export const getDashboardStats = () => request('/dashboard/stats', {}, { auth: true })

/** GET /api/v1/dashboard/analytics — analytics breakdown */
export const getAnalytics = () => request('/dashboard/analytics', {}, { auth: true })

/** GET /api/v1/dashboard/recent-calls — call logs */
export const getRecentCalls = () => request('/dashboard/recent-calls', {}, { auth: true })

/** GET /api/v1/dashboard/knowledge-gaps — unanswered questions */
export const getKnowledgeGaps = () => request('/dashboard/knowledge-gaps', {}, { auth: true })

/** GET /api/v1/dashboard/settings — get config settings */
export const getDashboardSettings = () => request('/dashboard/settings', {}, { auth: true })

/** PUT /api/v1/dashboard/settings — update config settings */
export const updateDashboardSettings = async (settings) => {
  const res = await request('/dashboard/settings', {
    method: 'PUT',
    body: JSON.stringify(settings),
  }, { auth: true })
  return res?.settings ?? res
}

// ── Knowledge Base ─────────────────────────────────────────────────────────
/** GET /api/v1/knowledge — list knowledge entries */
export const getKnowledgeEntries = () => request('/knowledge')

/** POST /api/v1/knowledge — create a knowledge entry */
export const createKnowledgeEntry = (payload) => request('/knowledge', {
  method: 'POST',
  body: JSON.stringify(payload),
}, { auth: true })

/** DELETE /api/v1/dashboard/knowledge-gaps/:id — resolve a knowledge gap */
export const deleteKnowledgeGap = (id) => request(`/dashboard/knowledge-gaps/${id}`, {
  method: 'DELETE',
}, { auth: true })

/** PUT /api/v1/knowledge/:id — update a knowledge entry */
export const updateKnowledgeEntry = (id, payload) => request(`/knowledge/${id}`, {
  method: 'PUT',
  body: JSON.stringify(payload),
}, { auth: true })

/** DELETE /api/v1/knowledge/:id — delete a knowledge entry */
export const deleteKnowledgeEntry = (id) => request(`/knowledge/${id}`, {
  method: 'DELETE',
}, { auth: true })

/** POST /api/v1/knowledge/upload — upload and ingest a PDF document */
export const uploadPDF = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  
  const headers = {}
  const token = sessionStorage.getItem('voicebot_admin_token')
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  const url = `${BASE_URL}/knowledge/upload`
  const res = await fetch(url, {
    method: 'POST',
    headers,
    body: formData,
  })
  
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Upload failed (${res.status}): ${text}`)
  }
  return res.json()
}

/** POST /api/v1/knowledge/upload-url — ingest a Web URL */
export const uploadURL = async (url) => request('/knowledge/upload-url', {
  method: 'POST',
  body: JSON.stringify({ url }),
}, { auth: true })

// ── Leads ──────────────────────────────────────────────────────────────────
/** GET /api/v1/leads — list captured leads */
export const getLeads = () => request('/leads', {}, { auth: true })

/** POST /api/v1/leads — create a lead record */
export const createLead = (payload) => request('/leads', {
  method: 'POST',
  body: JSON.stringify(payload),
})

/** DELETE /api/v1/leads/:id — delete a lead record */
export const deleteLead = (id) => request(`/leads/${id}`, {
  method: 'DELETE',
}, { auth: true })

// ── Bot Chat ───────────────────────────────────────────────────────────────
/** POST /api/v1/bot/chat — send a message to the bot simulation */
export const chatBot = (payload) => request('/bot/chat', {
  method: 'POST',
  body: JSON.stringify(payload),
})

/** POST /api/v1/bot/reset — reset the bot simulation session */
export const resetChatSession = (payload) => request('/bot/reset', {
  method: 'POST',
  body: JSON.stringify(payload),
})

// ── Telephony — Inbound ────────────────────────────────────────────────────
/** POST /api/v1/telephony/inbound — simulate or handle an inbound call with text or base64 audio */
export const simulateInboundCall = (payload) => request('/telephony/inbound', {
  method: 'POST',
  body: JSON.stringify(payload),
})

/** GET /api/v1/telephony/calls — list all telephony call records */
export const getTelephonyCalls = () => request('/telephony/calls')

// ── Telephony — Outbound ───────────────────────────────────────────────────
/**
 * POST /api/v1/telephony/outbound — initiate a real outbound call via Exotel.
 * @param {Object} payload
 * @param {string} payload.to_number - Target phone number e.g. "+919876543210"
 * @param {string} [payload.campaign_message] - Opening message the bot speaks
 * @param {string} [payload.language] - "en" or "ml"
 * @param {string} [payload.agent_name] - Bot agent name shown to recipient
 */
export const initiateOutboundCall = (payload) => request('/telephony/outbound', {
  method: 'POST',
  body: JSON.stringify(payload),
}, { auth: true })

// ── Admin Bot Training ─────────────────────────────────────────────────────
/**
 * POST /api/v1/training — add a single custom Q&A to bot training data.
 */
export const addTrainingEntry = (payload) => request('/training', {
  method: 'POST',
  body: JSON.stringify(payload),
}, { auth: true })

/**
 * POST /api/v1/training/bulk — bulk import Q&A pairs.
 */
export const bulkTrainingImport = (entries) => request('/training/bulk', {
  method: 'POST',
  body: JSON.stringify({ entries }),
}, { auth: true })

/**
 * POST /api/v1/training/outbound-script — set the outbound call opening script.
 */
export const setOutboundScript = (payload) => request('/training/outbound-script', {
  method: 'POST',
  body: JSON.stringify(payload),
}, { auth: true })

/**
 * POST /api/v1/training/personality — configure bot personality.
 */
export const setBotPersonality = (payload) => request('/training/personality', {
  method: 'POST',
  body: JSON.stringify(payload),
}, { auth: true })

/**
 * GET /api/v1/training/status — get bot training status.
 */
export const getTrainingStatus = () => request('/training/status', {}, { auth: true })

/**
 * POST /api/v1/training/voice — train bot with voice input.
 */
export const voiceTrainBot = (payload) => request('/training/voice', {
  method: 'POST',
  body: JSON.stringify(payload),
}, { auth: true })


// ── Auth ───────────────────────────────────────────────────────────────────
/** POST /api/v1/dashboard/login — authenticate administrator */
export const login = (username, password) => request('/dashboard/login', {
  method: 'POST',
  body: JSON.stringify({ username, password }),
})

/** POST /api/v1/dashboard/mfa — verify OTP for admin */
export const verifyMFA = (username, code) => request('/dashboard/mfa', {
  method: 'POST',
  body: JSON.stringify({ username, code }),
})

/** GET /api/v1/dashboard/audit-logs — retrieve admin audit logs */
export const getAuditLogs = () => request('/dashboard/audit-logs', {}, { auth: true })

// ── Outbound Campaigns ─────────────────────────────────────────────────────
/** GET /api/v1/campaigns — list all outbound campaigns */
export const getCampaigns = () => request('/campaigns', {}, { auth: true })

/** POST /api/v1/campaigns — create a new outbound campaign */
export const createCampaign = (payload) => request('/campaigns', {
  method: 'POST',
  body: JSON.stringify(payload),
}, { auth: true })

/** PUT /api/v1/campaigns/:id/status — update campaign status (start/pause/stop) */
export const updateCampaignStatus = (id, status) => request(`/campaigns/${id}/status`, {
  method: 'PUT',
  body: JSON.stringify({ status }),
}, { auth: true })

/** DELETE /api/v1/campaigns/:id — delete a campaign */
export const deleteCampaign = (id) => request(`/campaigns/${id}`, {
  method: 'DELETE',
}, { auth: true })

// ── Integrations ───────────────────────────────────────────────────────────
/** GET /api/v1/dashboard/integrations — get integrations configuration status */
export const getIntegrationsStatus = () => request('/dashboard/integrations', {}, { auth: true })

export { BASE_URL, DIRECT_BACKEND }

