import { Link } from 'react-router-dom'
import { useHealth } from '../hooks/useHealth'
import './LandingPage.css'

const API_DOCS_URL = 'http://localhost:8000/docs'

/* ── Feature card data ────────────────────────────────────────────────── */
const FEATURES = [
  {
    icon: '🎙️',
    title: 'Bilingual Voice AI',
    desc: 'Answers calls in English and Malayalam with natural-sounding Neural TTS. Auto-detects caller language within the first two responses.',
  },
  {
    icon: '📋',
    title: 'Smart Lead Capture',
    desc: 'Conversationally captures name, phone, and course interest. Stores leads with caller consent — never without explicit permission.',
  },
  {
    icon: '🔍',
    title: 'RAG Knowledge Base',
    desc: 'Grounds every answer in admin-approved content using Retrieval-Augmented Generation — hallucination-safe by design.',
  },
  {
    icon: '📊',
    title: 'Admin Control Panel',
    desc: 'Full bot configuration, knowledge CRUD, call logs, and live analytics — no developer needed for day-to-day management.',
  },
  {
    icon: '📞',
    title: 'Outbound Campaigns',
    desc: 'Proactive follow-up campaigns with scheduling, retry rules, DND compliance, and per-contact consent tracking.',
  },
  {
    icon: '💬',
    title: 'Multi-Channel',
    desc: 'Extends beyond voice — WhatsApp rich messages, SMS follow-ups, and automated email reports built right in.',
  },
]

/* ── How it works steps ───────────────────────────────────────────────── */
const STEPS = [
  { icon: '📞', num: '01', title: 'Caller Dials', desc: 'Bridgeon\'s number routes instantly to the AI assistant — no wait, no hold music.' },
  { icon: '🧠', num: '02', title: 'AI Understands', desc: 'Intent detection + RAG retrieves the most accurate, grounded answer from the knowledge base.' },
  { icon: '🗣️', num: '03', title: 'Responds Naturally', desc: 'Neural TTS delivers a warm, professional response in English or Malayalam.' },
  { icon: '✅', num: '04', title: 'Lead Captured', desc: 'Interested callers are captured as leads — with consent — and followed up automatically.' },
]

/* ── Stat bar data ────────────────────────────────────────────────────── */
const STATS = [
  { value: '24/7',  label: 'Call Coverage' },
  { value: '60%',  label: 'Workload Reduction' },
  { value: '4.7★', label: 'Bridgeon Rating' },
  { value: '<2s',  label: 'Response Latency' },
]

/* ── Status badge ─────────────────────────────────────────────────────── */
function StatusBadge({ loading, error, data }) {
  if (loading) return <span className="badge badge--loading">⏳ Connecting…</span>
  if (error)   return <span className="badge badge--error">🔴 Backend offline</span>
  return (
    <span className="badge badge--ok" title={`Uptime: ${data?.uptime_seconds}s`}>
      <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#34d399', display: 'inline-block', boxShadow: '0 0 8px #34d399', animation: 'blink 1.5s ease-in-out infinite' }} />
      Backend live — v{data?.version}
    </span>
  )
}

/* ── Main page ────────────────────────────────────────────────────────── */
export default function LandingPage() {
  const { data, loading, error } = useHealth()

  return (
    <div className="lp">
      {/* Background grid */}
      <div className="lp__bg-grid" aria-hidden="true" />

      {/* ── Navbar ────────────────────────────────────────────────── */}
      <nav className="lp__nav glass" aria-label="Main navigation">
        <div className="lp__nav-inner">
          <div className="lp__logo">
            <div className="lp__logo-icon">🤖</div>
            <span className="lp__logo-text">
              Bridgeon <span className="gradient-text">Buddy</span>
            </span>
          </div>
          <div className="lp__nav-actions">
            <StatusBadge loading={loading} error={error} data={data} />
            <Link to="/bot" id="btn-chat-bot" className="btn btn--ghost" style={{ padding: '0.5rem 1.1rem', fontSize: '0.85rem' }}>
              💬 Try Chat
            </Link>
            <Link to="/admin" id="btn-admin-panel" className="btn btn--primary" style={{ padding: '0.5rem 1.25rem', fontSize: '0.85rem' }}>
              Admin Panel →
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ──────────────────────────────────────────────────── */}
      <header className="lp__hero" aria-labelledby="hero-heading">
        {/* Decorative blobs */}
        <div className="blob blob--1" aria-hidden="true" />
        <div className="blob blob--2" aria-hidden="true" />
        <div className="blob blob--3" aria-hidden="true" />

        {/* Left: Content */}
        <div className="lp__hero-content animate-fade-in-up">
          <div className="lp__tag">
            <span className="lp__tag-dot" />
            Bridgeon Skillversity · Voice Assistant v4.0
          </div>

          <h1 id="hero-heading" className="lp__hero-title">
            AI Voice Buddy<br />
            <span className="gradient-text">That Never Sleeps</span>
          </h1>

          <p className="lp__hero-sub">
            The Bridgeon Voice Call Assistant answers every inbound call, captures leads
            with consent, provides bilingual course information, and escalates seamlessly —
            24 hours a day, 7 days a week.
          </p>

          <div className="lp__hero-cta">
            <Link to="/call" id="btn-realtime-call" className="btn btn--primary">
              📞 Start Real-Time Call
            </Link>
            <Link to="/telephony" id="btn-telephony-sim" className="btn btn--ghost">
              🎭 Simulate a Call
            </Link>
            <Link to="/bot" id="btn-simulate-bot" className="btn btn--ghost">
              💬 Try Chat Bot
            </Link>
          </div>

          {/* Quick trust signals */}
          <div style={{ marginTop: '2rem', display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--txt-muted)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              ✅ English & Malayalam
            </span>
            <span style={{ fontSize: '0.8rem', color: 'var(--txt-muted)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              🔒 Consent-first lead capture
            </span>
            <span style={{ fontSize: '0.8rem', color: 'var(--txt-muted)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              🧠 RAG-powered answers
            </span>
          </div>
        </div>

        {/* Right: Animated Voice Orb */}
        <div className="lp__hero-visual animate-float" aria-hidden="true">
          <div className="lp__orb-container">
            <div className="lp__orb">
              <span className="lp__orb-icon">🎙️</span>
            </div>
            <div className="lp__orb-ring lp__orb-ring--1" />
            <div className="lp__orb-ring lp__orb-ring--2" />
            <div className="lp__orb-ring lp__orb-ring--3" />

            {/* Floating chips */}
            <div className="lp__orb-chip lp__orb-chip--1">
              🟢 Live
            </div>
            <div className="lp__orb-chip lp__orb-chip--2">
              📋 Lead Saved
            </div>
            <div className="lp__orb-chip lp__orb-chip--3">
              🌐 EN / ML
            </div>
          </div>
        </div>
      </header>

      {/* ── Stats bar ─────────────────────────────────────────────── */}
      <section className="lp__stats" aria-label="Key metrics">
        {STATS.map((s) => (
          <div key={s.label} className="lp__stat">
            <span className="lp__stat-value gradient-text">{s.value}</span>
            <span className="lp__stat-label">{s.label}</span>
          </div>
        ))}
      </section>

      {/* ── Features ──────────────────────────────────────────────── */}
      <section className="lp__features" id="features" aria-labelledby="features-heading">
        <h2 id="features-heading" className="lp__section-title">
          Built for <span className="gradient-text">Every Caller</span>
        </h2>
        <p className="lp__section-sub">
          From prospective students to current trainees — every interaction is handled
          with intelligence, empathy, and speed.
        </p>
        <div className="lp__feature-grid">
          {FEATURES.map((f, i) => (
            <article
              key={f.title}
              className="lp__feature-card"
              style={{ animationDelay: `${i * 80}ms` }}
              aria-label={f.title}
            >
              <div className="lp__feature-icon-wrap">{f.icon}</div>
              <h3 className="lp__feature-title">{f.title}</h3>
              <p className="lp__feature-desc">{f.desc}</p>
            </article>
          ))}
        </div>
      </section>

      {/* ── How It Works ──────────────────────────────────────────── */}
      <section className="lp__how" aria-labelledby="how-heading">
        <div className="lp__how-inner">
          <h2 id="how-heading" className="lp__section-title">
            How <span className="gradient-text--teal">It Works</span>
          </h2>
          <p className="lp__section-sub">
            A seamless four-step pipeline from inbound call to captured lead — all automated.
          </p>
          <div className="lp__steps">
            {STEPS.map((step) => (
              <div key={step.num} className="lp__step animate-fade-in-up">
                <div className="lp__step-num">{step.icon}</div>
                <div>
                  <h3>{step.title}</h3>
                  <p>{step.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── System Status Card ────────────────────────────────────── */}
      <section className="lp__status-section" aria-labelledby="status-heading">
        <h2 id="status-heading" className="lp__section-title">
          Live <span className="gradient-text">System Status</span>
        </h2>
        <div className="lp__status-card">
          {loading && (
            <div className="lp__status-loading" role="status" aria-live="polite">
              <div className="spinner" aria-hidden="true" />
              <span>Reaching backend…</span>
            </div>
          )}
          {error && !loading && (
            <div className="lp__status-error" role="alert">
              <span className="lp__status-dot lp__status-dot--red" />
              <div>
                <strong>Backend Unreachable</strong>
                <p>Start the FastAPI server with <code>uvicorn main:app --reload</code></p>
                <code className="lp__error-msg">{error}</code>
              </div>
            </div>
          )}
          {data && !loading && (
            <div className="lp__status-grid" aria-label="Backend status details">
              <StatusItem label="Status"      value={data.status}      ok={data.status === 'healthy'} />
              <StatusItem label="App"         value={data.app} />
              <StatusItem label="Version"     value={`v${data.version}`} />
              <StatusItem label="Environment" value={data.environment} />
              <StatusItem label="Uptime"      value={`${data.uptime_seconds}s`} />
              <StatusItem label="Timestamp"   value={new Date(data.timestamp).toLocaleTimeString()} />
            </div>
          )}
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────────────────── */}
      <footer className="lp__footer" role="contentinfo">
        <div className="lp__footer-inner">
          <div className="lp__footer-logo">
            <div className="lp__logo-icon" style={{ width: 30, height: 30, fontSize: '1rem' }}>🤖</div>
            <span>Bridgeon <span className="gradient-text">Buddy</span></span>
          </div>
          <div className="lp__footer-links">
            <Link to="/call" className="lp__footer-link">📞 Real-Time Call</Link>
            <Link to="/telephony" className="lp__footer-link">🎭 Telephony Sim</Link>
            <Link to="/bot" className="lp__footer-link">💬 Chat Bot</Link>
            <Link to="/admin" className="lp__footer-link">⚙️ Admin Panel</Link>
            <a href={API_DOCS_URL} className="lp__footer-link" target="_blank" rel="noopener noreferrer">📄 API Docs</a>
          </div>
          <p className="lp__footer-copy">
            © {new Date().getFullYear()} Bridgeon Skillversity · Voice Call Assistant v4.0 · Built with FastAPI + React
          </p>
        </div>
      </footer>
    </div>
  )
}

/* ── Status item sub-component ────────────────────────────────────────── */
function StatusItem({ label, value, ok }) {
  return (
    <div className="lp__status-item">
      <span className="lp__status-label">{label}</span>
      <span className={`lp__status-value ${ok === false ? 'lp__status-value--bad' : ok === true ? 'lp__status-value--ok' : ''}`}>
        {ok === true  && <span className="lp__status-dot lp__status-dot--green" aria-hidden="true" />}
        {ok === false && <span className="lp__status-dot lp__status-dot--red"   aria-hidden="true" />}
        {value}
      </span>
    </div>
  )
}
