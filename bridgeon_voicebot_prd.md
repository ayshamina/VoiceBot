# Product Requirements Document (PRD)
# Bridgeon Voice Call Assistant

**Document Version:** 4.0
**Prepared By:** Intern — Bridgeon Solutions
**Date:** June 2026
**Status:** Draft

---

## Table of Contents

1. [Overview](#1-overview)
2. [Stakeholders](#2-stakeholders)
3. [User Personas](#3-user-personas)
4. [Scope](#4-scope)
5. [Bridgeon Institutional Knowledge Base](#5-bridgeon-institutional-knowledge-base)
6. [Voice Call Architecture](#6-voice-call-architecture)
7. [Functional Requirements — Voice Call System](#7-functional-requirements--voice-call-system)
8. [Outbound Calling & Campaign Manager](#8-outbound-calling--campaign-manager)
9. [Multi-Channel Integration](#9-multi-channel-integration)
10. [Admin Control Panel](#10-admin-control-panel)
11. [Bot Training System](#11-bot-training-system)
12. [Voice-Based Admin Training](#12-voice-based-admin-training)
13. [AI Agent Behavior & Personality](#13-ai-agent-behavior--personality)
14. [AI Enhancements — RAG & Continuous Learning](#14-ai-enhancements--rag--continuous-learning)
15. [Analytics Dashboard](#15-analytics-dashboard)
16. [Security & Compliance](#16-security--compliance)
17. [Knowledge Management System](#17-knowledge-management-system)
18. [Technical Architecture](#18-technical-architecture)
19. [Hybrid Tools Integration](#19-hybrid-tools-integration)
20. [Performance Requirements](#20-performance-requirements)
21. [Acceptance Criteria](#21-acceptance-criteria)
22. [Risks & Mitigation](#22-risks--mitigation)
23. [Competitive Differentiation](#23-competitive-differentiation)
24. [KPIs & Success Metrics](#24-kpis--success-metrics)
25. [Future Enhancements](#25-future-enhancements)
26. [Milestones & Timeline](#26-milestones--timeline)
27. [Glossary](#27-glossary)

---

## 1. Overview

### 1.1 Product Summary

The **Bridgeon Voice Call Assistant** is an AI-powered, telephony-integrated voice bot designed to serve as the primary 24/7 phone-based representative of **Bridgeon Skillversity** — one of Kerala's leading IT and technology training institutes.

When anyone dials Bridgeon's phone number, the call is automatically routed through this intelligent voice assistant. The bot handles the full conversation using real-time speech recognition, natural language understanding, and natural-sounding text-to-speech — all without requiring a human agent for routine queries.

Version 4.0 significantly expands the platform beyond inbound voice calls. The system now supports **outbound calling campaigns**, **multi-channel communication** (WhatsApp, SMS, email), **voice-based admin training**, **enhanced RAG-powered AI**, and a **hybrid tool stack** combining paid and open-source engines.

The system is built around six core pillars:

- **Voice Call Handling** — Answers inbound calls, detects caller intent, and responds naturally in English or Malayalam
- **Outbound Campaigns** — Proactive lead follow-ups, reminders, and scheduled call campaigns
- **Multi-Channel Integration** — WhatsApp, SMS, and email notifications alongside voice
- **Admin Control Panel** — Full bot configuration including voice-based training and engine selection
- **AI & RAG Engine** — Live knowledge retrieval, continuous learning, and auto-updated FAQs
- **Bot Training System** — Text and voice-based training by admins, with instant publishing

The bot serves four caller types: current students, prospective students, parents, and corporate recruiters.

---

### 1.2 Problem Statement

Bridgeon currently handles a large volume of inbound phone calls from students and prospective learners. These calls are largely repetitive and consume significant staff time:

| Pain Point | Impact |
|---|---|
| Repetitive calls about course fees, duration, and admission | Staff time wasted on low-complexity queries |
| No phone support outside office hours | Missed leads and frustrated callers |
| No structured lead capture during calls | Lost admissions opportunities |
| No Malayalam-first voice support | Local Kerala callers feel underserved |
| No admin control over bot responses | Every change requires a developer |
| No mechanism to teach the bot new information | Knowledge becomes stale over time |
| No outbound engagement for leads and reminders | Follow-up happens too late or not at all |
| Communication limited to voice only | Students and leads prefer WhatsApp and SMS |
| FAQ knowledge updated manually and infrequently | Bot gives outdated course or fee information |

---

### 1.3 Goals

#### Business Goals
- Answer 100% of inbound calls automatically during and outside office hours
- Reduce human call handling workload by **60%**
- Increase qualified lead capture by **30%**
- Improve admission conversion rate by **20%**
- Enable admin staff to update and train the bot — including by voice — without developer involvement
- Launch proactive outbound campaigns for lead follow-up and student reminders
- Communicate across WhatsApp, SMS, and email in addition to voice

#### User Goals

| User | Goal |
|---|---|
| Students | Get schedule, project, and mentor information over a phone call or WhatsApp |
| Prospective Students | Learn about courses, fees, and admissions without waiting on hold |
| Parents | Receive trustworthy, professional information about Bridgeon |
| Recruiters | Access placement cell information quickly |

#### Admin Goals
- Control all bot settings, responses, and behaviors from a dashboard
- Add, edit, and delete knowledge entries — by typing or by speaking
- Toggle between paid and open-source AI/telephony engines
- View call logs, lead data, and bot performance metrics
- Monitor and fix bot errors in real time
- Manage outbound campaign schedules, retry rules, and consent records

---

## 2. Stakeholders

| Role | Responsibility |
|---|---|
| Bridgeon Management | Product approval and strategic direction |
| Bot Admin (Bridgeon Staff) | Training the bot, managing knowledge base, monitoring performance |
| Admissions Team | Reviewing leads captured during calls, follow-up |
| Placement Team | Providing accurate placement and career information |
| Developer (Intern) | Designing, building, and deploying the system |
| Current Students | Internal callers and UAT participants |
| Prospective Students | External callers and UAT participants |

---

## 3. User Personas

### Persona A — Current Student (Caller)

**Who they are:** An active trainee at Bridgeon studying AI, Data Science, Flutter, or another program. Aged 18–26, based in Kerala.

**Goals when calling:**
- Find out batch schedule or class timings
- Ask about project submission deadlines
- Get a mentor's contact information
- Understand assessment format or dates

**Expectations:**
- Friendly, casual tone — like talking to a helpful senior
- Fast responses without being put on hold
- Malayalam language support
- WhatsApp follow-up messages with links or PDFs

**Pain Points:**
- Waiting for mentor callbacks on simple queries
- No way to get information outside working hours

---

### Persona B — Prospective Student (Caller)

**Who they are:** A fresh graduate or working professional exploring tech training options, aged 18–30.

**Goals when calling:**
- Understand what courses are available and what they cover
- Know the total fee and payment options
- Learn about placements and expected salaries
- Find out how to enroll or attend a demo session

**Expectations:**
- Professional, clear, and reassuring tone
- No aggressive sales pressure
- Quick lead capture and follow-up from Bridgeon team
- Receive course brochure via WhatsApp after the call

**Pain Points:**
- Calls go unanswered after hours
- Inconsistent information from different staff members

---

### Persona C — Parent (Caller)

**Who they are:** Parent or guardian of a prospective student evaluating Bridgeon.

**Goals when calling:**
- Understand the quality and structure of the education
- Get assurance about placement outcomes
- Assess safety, credibility, and value for money

**Expectations:**
- Trustworthy, professional communication
- Factual information — no exaggerated claims

---

### Persona D — Recruiter / HR (Caller)

**Who they are:** A hiring manager from a tech company looking to source trained junior developers or analysts.

**Goals when calling:**
- Understand what type of candidates Bridgeon produces
- Get placement cell contact details
- Ask about available candidate profiles

---

### Persona E — Bot Admin (Internal)

**Who they are:** A Bridgeon staff member (non-technical) responsible for managing the voice bot.

**Goals:**
- Update the bot's knowledge base with new course info, fees, schedules
- Correct wrong or outdated answers — by typing or speaking
- Train the bot with historical call data and new Q&A pairs
- Monitor call performance, leads, and unanswered questions
- Control escalation rules and call routing
- Manage outbound campaigns and consent records

**Expectations:**
- A simple, intuitive admin dashboard — no coding required
- Ability to add knowledge entries one at a time, including by voice
- Instant preview of how the bot will respond to a query
- Alerts when the bot fails to answer a question
- Toggle to switch between paid and open-source tool engines

---

## 4. Scope

### 4.1 In Scope

**v1.0 — Inbound Voice Core**
- Inbound voice call handling via telephony gateway (Twilio / Exotel)
- Real-time speech-to-text for English and Malayalam
- Natural-sounding text-to-speech responses
- Intent detection and context-aware conversation flow
- User type detection (student vs outsider) with tone adaptation
- FAQ handling for students and prospective students
- Lead capture during calls with caller consent
- Call escalation to human counselor after 3 failed attempts
- Admin control panel with full bot configuration
- Bot training interface — add, edit, delete knowledge entries
- Historical data import for initial bot training
- Call logs, transcript storage, and lead management dashboard
- Analytics and performance reporting
- WhatsApp text fallback option after call

**v4.0 — Platform Expansion (This Document)**
- Outbound calling campaigns with scheduling, retry rules, and consent tracking
- Multi-channel integration: WhatsApp (rich replies), SMS, and email notifications
- Voice-based admin training via speech input
- Enhanced RAG: live database retrieval, continuous learning, Google Sheets sync
- Security enhancements: consent recording, opt-in/opt-out management, call encryption
- Hybrid tool stack: paid + open-source engine support with admin toggle

---

## 5. Bridgeon Institutional Knowledge Base

The voice bot must act as a well-informed representative of Bridgeon Skillversity. All call responses must be grounded in verified, admin-approved content.

### 5.1 About Bridgeon

Bridgeon Skillversity is one of Kerala's most sought-after IT and technology training institutes. It operates as an **industry simulator** — the focus is on real-world skill development, not theory. Key facts the bot must know and communicate:

- Practice-first learning with heavy emphasis on coding, debugging, and live project builds
- Holistic development: technical skills + communication, presentation, and professional behavior
- Flexible formats: offline, online, and hybrid
- "Skill + Degree" model: formal university degrees (BCA, MCA) alongside bootcamps
- "Earn While You Learn" pathway activated in Year 2 for eligible students
- Rated **4.7/5** on Justdial and Glassdoor

### 5.2 Course Catalog

All flagship programs are **8 to 10 months**. No prior coding experience required.

#### Software Development

| Course | Key Technologies |
|---|---|
| MERN Stack Development | MongoDB, Express, React, Node.js |
| MEAN Stack Development | MongoDB, Express, Angular, Node.js |
| Java Full Stack Development | Java, Spring Boot, React/Angular |
| Python Full Stack Engineering | Python, Django/Flask, React |
| .NET Full Stack Development | C#, .NET, SQL Server |

#### Mobile Development

| Course | Focus |
|---|---|
| Flutter Development | Native & cross-platform mobile apps (iOS and Android) |

#### Data, AI & Analytics

| Course | Focus |
|---|---|
| Data Science | Python, statistics, ML fundamentals, data pipelines |
| Data Analytics | SQL, Excel, Power BI, visualization |
| Artificial Intelligence | Machine learning, deep learning, model deployment |
| Machine Learning | Supervised/unsupervised learning, model building |

#### Creative & Design

| Course | Focus |
|---|---|
| UI/UX Product Design | Figma, user research, prototyping |
| Graphic Designing | Adobe tools, visual communication |
| Media Production | Video, content creation, editing |

### 5.3 Placement & Salary Data

| Role | Starting Salary Range |
|---|---|
| Flutter / Full Stack Developer | ₹2.5 LPA – ₹4.1 LPA |
| Data Scientist / AI Engineer | ₹4.0 LPA – ₹4.9+ LPA |

> **Rule:** The bot must never guarantee placement. Approved response:
> *"Placement support is provided, but outcomes depend on your skill level, project quality, and interview performance."*

### 5.4 Fee Handling

The bot must never invent fee amounts. Approved fallback:
> *"Course fees vary by program. I'll have our admissions team call you back with the exact details — shall I take your number?"*

---

## 6. Voice Call Architecture

### 6.1 System Overview

The Bridgeon Voice Call Assistant is built on a telephony-integrated AI pipeline. When a caller dials Bridgeon's number, the call is routed through a telephony gateway into the bot system, which handles the conversation end-to-end using speech recognition, NLP, and text-to-speech.

```
Caller dials Bridgeon's number
           │
           ▼
┌──────────────────────────────────┐
│       Telephony Gateway           │
│  (Twilio / Exotel / FreeSWITCH)  │
│  Acts as the phone bridge         │
└──────────────┬───────────────────┘
               │  Audio stream (real-time)
               ▼
┌──────────────────────────────────┐
│     Speech-to-Text (STT) Layer    │
│  Google STT / Vosk (open-source) │
│  Real-time English + Malayalam    │
└──────────────┬───────────────────┘
               │  Transcribed text
               ▼
┌──────────────────────────────────┐
│     NLP / Intent Detection        │
│  (OpenAI GPT + LangChain + RAG)  │
│  User type, intent, language      │
└──────┬───────────────────┬───────┘
       │                   │
       ▼                   ▼
┌────────────┐    ┌─────────────────┐
│ FAQ Engine │    │  Knowledge Base  │
│            │    │  (Admin-trained) │
└─────┬──────┘    └────────┬────────┘
      │                    │
      ▼                    ▼
┌──────────────────────────────────┐
│      Conversation Manager         │
│  Session context, user type,      │
│  language, lead capture state     │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│      Lead Capture Module          │
│  Name, phone, course interest     │
│  Stored with call ID + timestamp  │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│     Response Generator            │
│  Tone-aware, grounded,            │
│  hallucination-safe               │
└──────────────┬───────────────────┘
               │  Text response
               ▼
┌──────────────────────────────────┐
│     Text-to-Speech (TTS) Layer    │
│  Azure Neural / Coqui TTS         │
│  Natural Malayalam + English      │
└──────────────┬───────────────────┘
               │  Audio
               ▼
┌──────────────────────────────────┐
│    Escalation Decision Engine     │
│  Resolved? → End call gracefully  │
│  Unresolved? → Transfer to human  │
└──────────────┬───────────────────┘
               │
               ▼
        Caller receives response
           or human transfer
```

---

### 6.2 Telephony Gateway

| Option | Description | Best For |
|---|---|---|
| **Twilio Voice** | Global telephony API, WebSocket audio streaming, programmable call flows | Primary production gateway |
| **Exotel** | India-focused telephony, strong regional support, easy IVR setup | Alternative for local reliability |
| **FreeSWITCH / Asterisk** | Open-source telephony server, full PBX capabilities | Prototyping and cost-efficient fallback |
| **Dialogflow CX Telephony** | Built-in Google telephony integration | If using Dialogflow as NLP layer |

**Requirements:**
- Inbound and outbound call routing to/from bot system
- Real-time bidirectional audio streaming
- Call hold and transfer capability (for human escalation)
- DTMF (keypad input) support as fallback when voice fails
- Call recording with admin toggle
- Indian phone number support (local + toll-free)

---

### 6.3 Example Call Flow

```
📞 Caller dials Bridgeon's number

Bot:    "Namaskaram! Bridgeon Skillversity-ilekku swagatham.
         Hello! Welcome to Bridgeon Skillversity.
         Are you a current student, or are you exploring our courses?
         നിങ്ങൾ ഒരു വിദ്യാർഥിയാണോ, അതോ ഞങ്ങളുടെ കോഴ്‌സുകൾ അന്വേഷിക്കുകയാണോ?"

Caller: "I want to know about the Data Science course."

Bot:    "Sure! Our Data Science program runs for 8 to 10 months
         and covers Python, statistics, machine learning fundamentals,
         and data pipelines. No prior coding experience is needed.
         Would you like details about the fee or admission process?"

Caller: "Yes, fees please."

Bot:    "For accurate fee details, I'd like to connect you with
         our admissions team. May I take your name and number
         so they can call you back? Is that okay?"

Caller: "Yes. My name is Arun, number is 9876543210."

Bot:    "Thank you, Arun! I've noted your details.
         A Bridgeon counselor will call you back within one business day.
         Would you also like me to send the course brochure to your WhatsApp?"

Caller: "Yes please."

Bot:    "Done! You'll receive it shortly. Have a great day!"

📞 Call ends — lead stored, WhatsApp brochure dispatched automatically
```

---

### 6.4 Speech-to-Text Layer

| Requirement | Specification |
|---|---|
| Engine (Paid) | Google Cloud Speech-to-Text |
| Engine (Open-source) | Vosk (offline capable, Malayalam model) |
| Languages | English (en-IN), Malayalam (ml-IN) |
| Mixed-language input | Supported (e.g., "Flutter courseinte fee ethra aanu?") |
| Streaming mode | Real-time, low-latency |
| Accuracy target | ≥ 90% (English), ≥ 85% (Malayalam) |
| Noise handling | Background noise suppression enabled |
| Accent tuning | Custom model fine-tuned with Kerala accent samples |

---

### 6.5 Text-to-Speech Layer

| Requirement | Specification |
|---|---|
| Engine (Paid) | Azure Neural Voice / Google TTS |
| Engine (Open-source) | Coqui TTS (Malayalam and English models) |
| Voice character | Natural, warm, professional — not robotic |
| Speed | Adjustable (default: conversational pace ~130 WPM) |
| Malayalam voice | Native-sounding female or male voice |
| Pause handling | Natural pauses at sentence boundaries |
| SSML support | Required for emphasis, pauses, and number reading |

---

### 6.6 Call Escalation Flow

When the bot cannot resolve a caller's query, it must escalate gracefully without making the caller feel rejected.

```
Bot fails to understand or answer (Attempt 1)
    │
    ▼
Politely ask for clarification
    │
Bot fails again (Attempt 2)
    │
    ▼
Offer examples of what it can help with
    │
Bot fails again (Attempt 3)
    │
    ▼
Escalation triggered:

Option A — Human Transfer (during office hours):
"Let me connect you to one of our team members right away."
→ Transfer call to live counselor via telephony gateway

Option B — After-hours fallback:
"Our team is currently unavailable, but I've noted your query.
 A counselor will call you back within one business day."
→ Log query + caller number → Store as priority lead

Option C — Emergency contact:
→ Play Bridgeon's direct contact number and email
```

---

## 7. Functional Requirements — Voice Call System

### 7.1 Inbound Call Handling

The system must:
- Answer every inbound call automatically within 2 rings
- Disclose call recording at the start of every call if recording is enabled
- Play a bilingual greeting (Malayalam first, then English)
- Detect the caller's language within the first 2 responses
- Maintain conversational context throughout the call
- Handle call disconnections gracefully (save partial lead data)
- Support DTMF keypad input as a fallback when voice is unclear

---

### 7.2 User Type Detection During Call

**Trigger on greeting:**
> *"Are you a current student, or are you exploring our courses?"*

**Student voice triggers:** "my batch", "my mentor", "my project", "schedule", "attendance", "submission", "assessment"

**Outsider voice triggers:** "fees", "admission", "enroll", "how to join", "course details", "placement"

**Rules:**
- User type persists for the entire call
- Caller can self-correct: "Actually I'm a student" → bot switches context
- If unclear, default to outsider mode

---

### 7.3 FAQ Handling During Calls

All FAQs must be optimized for **voice delivery** — concise, spoken-word friendly responses (no bullet points in speech, natural sentence flow).

**Student FAQs (minimum 20 at launch):**
1. What is my batch schedule this week?
2. When is my next project submission deadline?
3. How do I contact my mentor?
4. What topics are covered in my current module?
5. Is attendance mandatory for all sessions?
6. How are assessments graded?
7. Can I switch from offline to online mode?
8. What happens if I miss a class?
9. How do I report a technical issue?
10. What is the "Earn While You Learn" program?

**Outsider FAQs (minimum 20 at launch):**
1. What courses does Bridgeon offer?
2. How long are the programs?
3. Do I need prior coding experience?
4. Is there a free demo class?
5. What is the placement support like?
6. What salary can I expect after completing a course?
7. Do students get a certificate?
8. Are courses available online?
9. How do I enroll?
10. Where are the Bridgeon campuses located?

---

### 7.4 Lead Capture During Calls

When a prospective caller expresses interest, the bot initiates a conversational lead capture — spoken naturally, not like a form.

**Flow:**
1. *"May I know your name?"*
2. *"Thanks [Name]! What's a good number to reach you on?"* (Validate: 10-digit Indian format)
3. *"And which program are you most interested in?"* → Bot lists available courses
4. *"Perfect, I've noted all your details. Our admissions team will call you back within one business day."*
5. Lead stored with: name, phone, course interest, call timestamp, call ID

**Consent requirement:**
> *"I'll save your details so our team can follow up. Is that okay with you?"*
> Bot must not proceed without caller confirmation.

**Post-capture offer:**
> *"Would you like me to send the course brochure to your WhatsApp number?"*

---

### 7.5 Multilingual Voice Support

| Requirement | Specification |
|---|---|
| Languages | English (en-IN), Malayalam (ml-IN) |
| Detection | Automatic based on first 1–2 caller responses |
| Switching | Caller can switch mid-call; bot follows immediately |
| Mixed language | Bot must handle sentences mixing Malayalam and English technical terms |
| Greeting | Always bilingual: Malayalam first, then English |
| All responses | Available in both languages in knowledge base |

---

### 7.6 Motivational & Supportive Voice Responses (Students)

When students call about projects, assessments, or difficulties, the bot must include spoken encouragement:

| Trigger | Voice Response |
|---|---|
| Project difficulty | *"Projects can be tough, but this is exactly what prepares you for the industry. Let's take it step by step."* |
| Upcoming assessment | *"You've got this! Here's what you need to know about the format."* |
| General frustration | *"It's completely normal to hit a wall sometimes. Every developer has been there. What specific part can I help you with?"* |

---

## 8. Outbound Calling & Campaign Manager

### 8.1 Overview

Version 4.0 introduces proactive outbound calling capability. The bot can initiate calls to leads, enrolled students, and opted-in contacts for follow-ups, reminders, and structured campaigns — all managed through the admin panel.

**Use cases:**
- Lead follow-up: call back prospective students who didn't complete enrollment
- Batch reminders: notify students of upcoming deadlines, assessments, or schedule changes
- Admission campaigns: reach out to inquiry leads before a batch fills
- Event invitations: inform contacts about demo days, webinars, or open days

---

### 8.2 Campaign Manager

The admin can create and manage outbound campaigns from the dashboard:

| Field | Description |
|---|---|
| Campaign name | Descriptive label (e.g., "June Batch Follow-Up") |
| Target list | Upload CSV or select from existing leads/contacts |
| Message / script | Pre-approved bot script for this campaign |
| Channel | Voice call / WhatsApp / SMS / Email |
| Schedule | Date, time, and timezone for campaign start |
| Retry rules | How many times to retry unanswered calls (max 3), with interval between retries |
| Consent required | Toggle: only contact leads who have opted in |
| Campaign status | Draft / Scheduled / Running / Paused / Completed |

---

### 8.3 Outbound Call Flow

```
Campaign scheduler triggers at configured time
           │
           ▼
Fetch next contact from target list
  └── Check: has consent been recorded? → No → Skip, log, move on
           │  Yes
           ▼
Telephony gateway dials contact's number
           │
    ┌──────┴──────┐
    │ No answer   │ Answered
    ▼             ▼
Retry queue    Bot delivers campaign script
(up to 3x)     → Handles questions → Captures response
               → Logs outcome (interested / not interested / callback)
               → Sends WhatsApp/SMS follow-up if opted in
```

---

### 8.4 Retry Rules

| Rule | Specification |
|---|---|
| Maximum retry attempts | 3 per contact per campaign |
| Retry interval | Configurable (default: 4 hours between attempts) |
| Retry window | Only within admin-defined calling hours (e.g., 9 AM – 7 PM IST) |
| DND compliance | Numbers on DND registry are automatically excluded |
| After final retry | Mark as "Unreachable" — do not attempt again unless admin overrides |

---

### 8.5 Consent & Opt-In Tracking

- Every contact must have a recorded opt-in before being included in outbound campaigns
- Opt-in sources: inbound call consent, WhatsApp reply, web form, admin manual entry
- Opt-out is honoured immediately: if a contact says "stop calling" or replies STOP to SMS, they are removed from all future campaigns
- Consent records are stored with: source, timestamp, method, and admin who recorded it
- Admin dashboard shows consent status for every contact in the lead database

---

### 8.6 Campaign Analytics

| Metric | Description |
|---|---|
| Total contacts dialled | Per campaign |
| Answer rate | % of calls picked up |
| Retry success rate | % of contacts reached on 2nd or 3rd attempt |
| Conversion rate | % who expressed interest or booked callback |
| Opt-out rate | % who opted out during or after campaign |
| Channel performance | Voice vs WhatsApp vs SMS response comparison |

---

## 9. Multi-Channel Integration

### 9.1 Overview

The Bridgeon Voice Call Assistant extends beyond phone calls in v4.0 to communicate with students and leads across their preferred channels. Voice remains the primary interaction channel; WhatsApp, SMS, and email serve as follow-up and notification layers.

---

### 9.2 WhatsApp Integration

**Implementation:** Twilio WhatsApp API / WhatsApp Business API

**Supported message types:**

| Type | Use Case |
|---|---|
| Text message | Post-call summaries, confirmations, reminders |
| PDF document | Course brochures, fee structures, syllabi |
| Image | Batch schedules, event posters, campus maps |
| Link | Enrollment forms, demo class registration, Bridgeon website |
| Template messages | Outbound campaign notifications (requires WhatsApp pre-approval) |

**Triggers:**
- After inbound call: offer to send brochure or summary
- After lead capture: send confirmation and next steps
- Outbound campaign: send campaign message as WhatsApp if voice fails
- After enrollment: send welcome message and batch schedule PDF

**Conversation rules:**
- Bot handles simple WhatsApp replies (yes/no, FAQ queries)
- Complex queries escalate to human via WhatsApp transfer or callback
- All WhatsApp conversations logged to admin panel

---

### 9.3 SMS Integration

**Implementation:** Twilio SMS / Exotel SMS

| Use Case | Trigger |
|---|---|
| Post-call confirmation | After any call where lead data was captured |
| Appointment reminder | 24 hours before a scheduled callback or demo |
| Batch reminder | 1 day before assessment or project deadline |
| Opt-out confirmation | Immediately after a contact opts out |
| Campaign follow-up | When voice call is unanswered after final retry |

**SMS rules:**
- Maximum 160 characters for standard SMS; longer messages split automatically
- DND registry checked before every SMS
- Opt-out reply (STOP) processed within 60 seconds

---

### 9.4 Email Notifications

**Implementation:** SendGrid / SMTP integration

| Email Type | Recipients | Trigger |
|---|---|---|
| Lead captured | Admissions team | Every new lead from voice or WhatsApp |
| Daily lead summary | Admin, admissions team | Each morning at 8 AM IST |
| Campaign completion report | Admin | When a campaign finishes |
| Unanswered questions alert | Admin | When bot knowledge gap count exceeds threshold |
| Weekly performance report | Management, admin | Every Monday |

**Student-facing emails** (future, when email addresses are collected):
- Course brochure delivery
- Enrollment confirmation
- Batch schedule and assessment reminders

---

### 9.5 Channel Routing Logic

When a lead interaction begins, the system selects the best follow-up channel:

```
Call ends
    │
    ▼
Was WhatsApp consent given?
  ├── Yes → Send WhatsApp message (rich content if applicable)
  └── No  → Send SMS (text only)
           │
           ▼
       Was email collected?
         ├── Yes → Send email copy to admissions team with lead data
         └── No  → Email only sent internally to admin
```

---

## 10. Admin Control Panel

The Admin Control Panel is a web-based dashboard that gives Bridgeon staff full control over the voice bot — with zero coding required.

### 10.1 Admin Dashboard Overview

The dashboard provides a single-screen view of:

- Live call activity (active calls, queue, duration)
- Today's call volume and lead count
- Bot performance metrics (resolution rate, escalation rate)
- Recent unanswered questions (knowledge gaps)
- Active outbound campaign status
- Engine mode indicator (paid / open-source)
- Quick access to all management modules

---

### 10.2 Knowledge Base Manager

The admin can manage all bot knowledge through a simple interface:

#### Add New Knowledge Entry

The admin fills in:

| Field | Description |
|---|---|
| Question / Trigger phrase | What a caller might say (e.g., "What is the fee for Flutter?") |
| Response (English) | The bot's spoken reply in English |
| Response (Malayalam) | The bot's spoken reply in Malayalam |
| Category | Course Info / Fees / Admissions / Student Support / Placement / General |
| Active | Toggle to enable or disable this entry |

**Save** → Entry immediately active in the bot's next call.

#### Edit Existing Entry
- Search by keyword or category
- Click any entry to edit question, response, or language
- Save → changes go live instantly

#### Delete Entry
- Mark entry as inactive (soft delete) or permanently remove
- Inactive entries are invisible to the bot but retained for reference

#### Bulk Import
- Upload a CSV or Excel file with multiple Q&A pairs
- System parses, validates, and imports all entries
- Preview before confirming import

#### Google Sheets Sync
- Connect a Google Sheet as a live FAQ source
- Sheet columns: Question, English Response, Malayalam Response, Category
- Bot pulls updates automatically every 15 minutes
- Admin can trigger a manual sync at any time

---

### 10.3 Call Configuration Settings

The admin can configure all call behavior settings:

| Setting | Description | Default |
|---|---|---|
| Greeting message (English) | What the bot says when it picks up | Bridgeon default |
| Greeting message (Malayalam) | Malayalam greeting text | Bridgeon default |
| Bot voice (English) | Select from available Azure/Google neural voices | Female, professional |
| Bot voice (Malayalam) | Select Malayalam voice | Native female voice |
| Speaking speed | Adjust TTS pace (slow / normal / fast) | Normal |
| Office hours | Set hours when human transfer is available | 9 AM – 6 PM IST |
| After-hours behavior | Transfer / fallback message / voicemail | Fallback message |
| Escalation threshold | Number of failed attempts before escalation | 3 |
| Call recording | Enable / disable call recording | Enabled |
| Max call duration | Auto-end call after N minutes if no response | 10 minutes |
| Engine mode | Paid (production) / Open-source (fallback) | Paid |

---

### 10.4 Engine Toggle (Paid vs Open-Source)

Admins can switch the AI/telephony engine without developer involvement:

| Component | Paid Engine | Open-Source Engine |
|---|---|---|
| Telephony | Twilio / Exotel | FreeSWITCH / Asterisk |
| STT | Google Cloud STT / Azure STT | Vosk |
| TTS | Azure Neural Voice / Google TTS | Coqui TTS |
| NLP | OpenAI GPT-4o / Azure OpenAI | Rasa NLU / local open-source LLMs |

**Toggle behavior:**
- Admin selects mode (Paid / Open-source / Hybrid) from the settings panel
- System applies the change immediately for new calls
- Active calls continue on their current engine until completion
- Dashboard shows current engine mode with a status indicator

---

### 10.5 Escalation & Routing Rules

The admin can configure call routing:

| Rule | Options |
|---|---|
| Escalation target (office hours) | Specific phone number or SIP extension |
| Escalation target (after hours) | Voicemail / callback lead / fallback message |
| Priority routing | VIP numbers always routed to human |
| Caller blacklist | Block specific numbers from reaching bot |
| Department routing | Student calls → student support; Recruiter calls → placement cell |

---

### 10.6 Lead Management

The admin can view and manage all leads captured during calls:

- View all leads in a table: name, phone, course, date, call ID, channel source
- Filter by date range, course interest, follow-up status, or channel
- Mark leads as: New / Contacted / Enrolled / Not Interested
- Add notes to any lead record
- Export leads as CSV for use in external tools
- Manually add leads (for walk-in or email inquiries)
- View consent status and opt-in/opt-out history for each lead

---

### 10.7 Call Logs & Transcripts

For every call, the admin can access:

- Caller number and call duration
- Full call transcript (text version of the conversation)
- Bot's detected intent and user type
- Whether lead was captured
- Whether call was escalated and to whom
- Audio recording playback (if recording is enabled)
- Flag calls for review or use in bot training

---

### 10.8 Unanswered Questions Monitor

The admin sees a live feed of questions the bot could not answer:

- Question text (from call transcript)
- Frequency (how many callers asked this)
- Date first seen
- One-click option: *"Add this as a new knowledge entry"*
- One-click option: *"Train by voice"* — opens the voice training interface

This directly feeds the bot training workflow.

---

### 10.9 Admin User Management

| Feature | Description |
|---|---|
| Multiple admin accounts | Different staff members can have their own login |
| Role-based access | Super Admin (full access) / Content Manager (knowledge only) / Viewer (read-only) |
| Activity log | Every change to the bot is logged with editor name and timestamp |
| Password reset | Self-service password reset for admin accounts |

---

## 11. Bot Training System

The bot training system allows the admin to continuously improve the voice bot's intelligence — adding knowledge from past calls, new course data, and corrections — all through a simple, guided interface.

### 11.1 Training Philosophy

The bot is trained using a **Retrieval-Augmented Generation (RAG)** approach:

- The admin adds knowledge entries (Q&A pairs, course documents, FAQ data)
- These are indexed in a vector database for semantic search
- When a call comes in, the bot retrieves the most relevant knowledge and generates a natural, grounded response
- The bot never invents information — it only responds from its trained knowledge base
- Unanswered questions are automatically flagged and surfaced to the admin for training

---

### 11.2 One-by-One Training Interface

The admin can teach the bot new information one entry at a time through a guided form:

**Step 1 — Add the question or topic:**
> *"What should a caller be asking for this to trigger?"*
> Example input: *"Do you offer weekend batches?"*

**Step 2 — Add the English response:**
> *"How should the bot answer in English?"*
> Example: *"Yes, Bridgeon offers weekend batches for working professionals. You can choose Saturday-Sunday schedules for most of our programs."*

**Step 3 — Add the Malayalam response:**
> *"How should the bot answer in Malayalam?"*
> (Admin types or pastes Malayalam text; system validates Unicode)

**Step 4 — Assign category and tags:**
> Category: Course Info | Tags: schedule, weekend, batch

**Step 5 — Test it:**
> Admin types a test question → Bot shows how it will respond → Admin confirms or edits

**Step 6 — Publish:**
> Entry goes live immediately in the bot's knowledge base

---

### 11.3 Training from Historical Call Data

The admin can use past call transcripts to train the bot:

**Import Call Transcripts:**
- Upload a batch of call transcripts (TXT, CSV, or auto-imported from call logs)
- System identifies questions callers asked and responses that were given or missed
- Admin reviews each extracted Q&A pair and approves, edits, or rejects it
- Approved pairs are added to the knowledge base

**Workflow:**

```
Upload old call transcripts
           │
           ▼
System extracts Q&A candidates
           │
           ▼
Admin reviews each pair
  ├── Approve → Added to knowledge base
  ├── Edit → Admin corrects response → Added
  └── Reject → Discarded
           │
           ▼
Bot is updated with new knowledge
```

---

### 11.4 Training from Documents

The admin can upload documents to train the bot on structured content:

**Supported document types:**
- PDF brochures (course syllabi, fee structures)
- Word documents (FAQs, policy documents)
- Excel/CSV files (batch schedules, contact lists)
- Plain text files
- Google Sheets (live sync — see Section 10.2)

**Process:**
1. Admin uploads document
2. System extracts text and identifies key Q&A pairs automatically
3. Admin reviews extracted entries, edits if needed, and approves
4. Approved entries added to knowledge base

---

### 11.5 Training Corrections (Feedback Loop)

When the bot gives a wrong or incomplete answer during a call, the admin can correct it directly:

1. Open the relevant call transcript in the admin panel
2. Highlight the bot's incorrect response
3. Click **"Correct this answer"**
4. Enter the correct English and Malayalam responses (by typing or by voice)
5. Save → Bot is updated immediately

This creates a continuous improvement loop where every mistake is a training opportunity.

---

### 11.6 Continuous Learning from Unanswered Questions

The system automatically identifies knowledge gaps and assists in closing them:

- Every unanswered caller question is logged with frequency and date
- When the same question is asked by 3 or more callers, an alert is sent to the admin
- Admin receives a suggested answer drafted by the AI based on existing knowledge context
- Admin reviews, edits if needed, and publishes with one click
- Published entries are immediately active and the gap alert is resolved

---

### 11.7 Knowledge Base Versioning

Every training update is versioned:

| Feature | Description |
|---|---|
| Version history | Every knowledge base update is saved with timestamp and editor name |
| Rollback | Admin can revert to any previous version with one click |
| Change diff | Visual comparison of what changed between versions |
| Audit log | Full history of all training actions |

---

### 11.8 Training Quality Indicators

The admin dashboard shows training health metrics:

| Metric | Description |
|---|---|
| Total knowledge entries | How many Q&A pairs the bot knows |
| Coverage rate | % of recent caller questions answered successfully |
| Knowledge gaps | Questions asked in last 7 days with no matching entry |
| Last updated | When knowledge base was last modified |
| Pending review | Extracted Q&A pairs awaiting admin approval |

---

## 12. Voice-Based Admin Training

### 12.1 Overview

In v4.0, admins can train the bot by **speaking** — without typing a single character. This makes the training process faster, more natural, and accessible to non-technical staff, especially when working away from a keyboard.

The voice training mode uses the same STT pipeline as the call system and integrates directly with the knowledge base manager.

---

### 12.2 Voice Training Flow

```
Admin taps "Train by Voice" in the admin panel
           │
           ▼
Bot (via browser or admin app) asks:
"What question should trigger this response?"
           │
           ▼
Admin speaks the trigger question aloud
→ STT captures and transcribes it
→ Displayed on screen for admin to confirm or re-speak
           │
           ▼
Bot asks: "What should I say in English when someone asks this?"
           │
           ▼
Admin speaks the English response
→ Transcribed and displayed
           │
           ▼
Bot asks: "What should I say in Malayalam?"
           │
           ▼
Admin speaks the Malayalam response
→ Transcribed and displayed
           │
           ▼
Bot confirms via voice:
"Got it! I'll now answer [trigger question] with your response.
 Save this entry?"
           │
  ┌────────┴────────┐
  │ Admin says Yes  │ Admin says No
  ▼                 ▼
Entry saved      Discard and restart
immediately
Bot confirms:
"Saved! This is now live."
```

---

### 12.3 Voice Training Requirements

| Requirement | Specification |
|---|---|
| Interface | Browser-based microphone access (no app install needed) |
| STT engine used | Same as call engine (paid or open-source based on toggle) |
| Transcription display | Live display as admin speaks; corrections allowed before saving |
| Confirmation | Bot reads back the entry via TTS for admin to verify |
| Save speed | Entry goes live within 30 seconds of confirmation |
| Supported languages | Admin can train in English; Malayalam training confirmed separately |
| Fallback | If STT fails, admin can switch to typed input without losing progress |

---

### 12.4 Voice Correction Mode

Admins can also correct existing entries by voice:

1. From the unanswered questions monitor or call transcript view, click **"Correct by Voice"**
2. Bot reads the current incorrect answer aloud
3. Admin speaks the corrected response
4. Bot confirms and saves

---

## 13. AI Agent Behavior & Personality

### 13.1 Student Caller — Tone

- Warm, casual, and encouraging
- Uses simple, jargon-free language
- Celebrates effort and progress
- Never dismissive or condescending

**Sample voice phrases:**
- *"Great question! Let me pull that up for you."*
- *"You're on the right track — here's what you need to know."*
- *"I know assessments can be stressful, but you've got this!"*

---

### 13.2 Outsider / Prospective Caller — Tone

- Professional, clear, and trustworthy
- Avoids aggressive sales language
- Reassures callers about Bridgeon's outcomes
- Proactively offers to connect with admissions

**Sample voice phrases:**
- *"I'd be happy to walk you through our programs."*
- *"Bridgeon has helped hundreds of students launch their tech careers — let me tell you how."*
- *"Our admissions team can give you a personalized recommendation. Shall I arrange a callback?"*

---

### 13.3 Hallucination Prevention (Voice-Specific)

Because wrong information over a phone call directly damages trust, the bot must be strictly grounded:

- **Never invent fees, dates, or statistics not in the knowledge base**
- **Never confirm a specific batch timing unless it is stored in the active schedule**
- **Never name specific companies as hiring partners unless explicitly approved**

Approved fallback for unknown queries:
> *"I want to make sure I give you accurate information. Let me have our team call you back with the exact details."*

---

## 14. AI Enhancements — RAG & Continuous Learning

### 14.1 RAG Architecture

The bot uses **Retrieval-Augmented Generation** to ensure all responses are grounded in real, admin-approved knowledge. The v4.0 RAG system adds live database retrieval and automatic gap detection.

```
Caller query arrives
       │
       ▼
Semantic search across vector database
  ├── Course information (from admin panel + Google Sheets)
  ├── Live schedule data (from connected database)
  ├── Fee structures (last updated timestamp checked)
  └── Placement statistics
       │
       ▼
Top-K relevant chunks retrieved
       │
       ▼
GPT / Rasa generates grounded response
(strictly constrained to retrieved context)
       │
       ▼
Response delivered to caller
       │
       ▼
If no relevant chunk found:
  → Log as knowledge gap
  → Deliver fallback response
  → Flag for admin training queue
```

---

### 14.2 Live Database Retrieval

The RAG system can pull real-time data from connected sources:

| Source | Data Retrieved | Update Frequency |
|---|---|---|
| Admin knowledge base | FAQs, Q&A pairs, course info | Real-time (on save) |
| Google Sheets | FAQ updates, batch schedules | Every 15 minutes |
| PostgreSQL database | Enrolled student counts, batch availability | Real-time API |
| Admin-uploaded documents | Syllabi, brochures, policy docs | On upload |

---

### 14.3 Continuous Learning from Unanswered Questions

The system does not wait for the admin to manually discover gaps. It actively learns:

- Every failed query (no matching knowledge chunk found) is logged automatically
- Queries are clustered by semantic similarity — similar questions are grouped
- When a cluster reaches 3+ unique callers, an alert is sent to the admin
- The AI drafts a suggested answer based on context from existing knowledge
- Admin sees: the gap question, how many callers asked it, and the AI's draft answer
- Admin approves, edits, or rejects with one click — or uses voice training

---

### 14.4 Auto-Update FAQs from Google Sheets

Admins or content managers can maintain a Google Sheet as a live FAQ source:

**Sheet format:**

| Column | Description |
|---|---|
| Trigger Question | What the caller might ask |
| English Response | Bot's English answer |
| Malayalam Response | Bot's Malayalam answer |
| Category | Course Info / Fees / Admissions / etc. |
| Active (Y/N) | Whether this entry is live |

**Sync behavior:**
- Sheet is checked every 15 minutes
- New rows are automatically added to the knowledge base
- Edited rows update the existing entry
- Rows marked N in the Active column are deactivated
- Admin receives a sync summary notification after each update

---

### 14.5 Knowledge Freshness Monitoring

| Feature | Description |
|---|---|
| Staleness alerts | Entries not updated in 30 days are flagged for review |
| Last-updated timestamps | Every entry shows when it was last modified |
| Source tracking | Each entry linked to its origin (admin, transcript, Google Sheet, document) |
| Conflict detection | If two entries answer the same question differently, admin is alerted |

---

## 15. Analytics Dashboard

### 15.1 Call Analytics

| Metric | Description |
|---|---|
| Total inbound calls | Daily / weekly / monthly count |
| Calls fully resolved by bot | % handled without escalation |
| Calls escalated to human | Count and % |
| Average call duration | In seconds |
| Peak call hours | Hourly call volume heatmap |
| Call abandonment rate | % of callers who hung up before being helped |
| Calls by user type | Student vs outsider breakdown |
| Language breakdown | English vs Malayalam vs mixed |

### 15.2 Outbound Campaign Analytics

| Metric | Description |
|---|---|
| Campaigns run this month | Count and status breakdown |
| Total contacts dialled | Across all campaigns |
| Answer rate | % of outbound calls picked up |
| Conversion rate | % who expressed interest or booked callback |
| Opt-out rate | % who opted out during or after campaign |
| Retry success rate | % reached on 2nd or 3rd attempt |

### 15.3 Multi-Channel Analytics

| Metric | Description |
|---|---|
| WhatsApp messages sent | Total and by type (brochure / reminder / campaign) |
| WhatsApp reply rate | % of sent messages that received a reply |
| SMS delivery rate | % successfully delivered |
| Email open rate | For admin-facing reports |
| Channel preference breakdown | Voice vs WhatsApp vs SMS engagement comparison |

### 15.4 Knowledge & FAQ Analytics

| Metric | Description |
|---|---|
| Top 10 most asked questions | Ranked by call frequency |
| Unanswered questions | Questions with no matching entry |
| Knowledge gap rate | % of calls with at least one unanswered question |
| FAQ resolution rate | % of FAQ queries answered successfully |
| Google Sheets sync status | Last sync time and number of entries updated |

### 15.5 Lead Analytics

| Metric | Description |
|---|---|
| Leads captured per day | Total and by course |
| Lead capture completion rate | % of leads fully captured vs abandoned mid-flow |
| Leads by course interest | Ranked by popularity |
| Follow-up status | New / Contacted / Enrolled / Not Interested |
| Leads by channel | Voice / WhatsApp / SMS source breakdown |

### 15.6 Training Analytics

| Metric | Description |
|---|---|
| Total knowledge entries | Current count in knowledge base |
| Entries added this week | Training activity tracking |
| Voice-trained entries | Entries created via voice training |
| Coverage rate trend | Week-over-week improvement |
| Corrections made | Number of bot answers corrected by admin |
| Auto-suggested entries approved | From continuous learning module |

---

## 16. Security & Compliance

### 16.1 Call Data Protection

- All call recordings encrypted at rest (AES-256) and in transit (TLS 1.2+)
- Call transcripts stored in encrypted database
- Lead data (name, phone, email) encrypted separately with field-level encryption
- Student personal data isolated in a dedicated encrypted partition
- Access restricted by role-based permissions

---

### 16.2 Consent Recording During Calls

Every call that involves data collection must include explicit verbal consent:

- **Call recording disclosure** — Bot informs callers at the start if recording is enabled:
  > *"This call may be recorded for quality and training purposes."*
- **Data storage consent** — Bot obtains verbal consent before saving any personal information:
  > *"I'll save your details so our team can follow up. Is that okay with you?"*
- Consent responses are captured in the call transcript and stored as a consent record
- Consent records include: caller number, timestamp, call ID, and verbatim confirmation phrase
- Bot must not store or forward any personal data if the caller declines consent

---

### 16.3 Opt-In / Opt-Out Tracking for Outbound Campaigns

| Action | Behaviour |
|---|---|
| Opt-in via inbound call | Caller confirms consent during lead capture; stored immediately |
| Opt-in via WhatsApp | Contact replies YES to a consent message; logged with timestamp |
| Opt-in via web form | Admin imports consent record with source and date |
| Opt-out via voice | Contact says "stop calling" or "remove me" during a call; system flags and deactivates immediately |
| Opt-out via SMS | Contact replies STOP; processed within 60 seconds |
| Opt-out via WhatsApp | Contact replies STOP or UNSUBSCRIBE; processed within 60 seconds |
| DND check | All outbound contacts checked against TRAI DND registry before dialling |

Opt-out is permanent unless the contact explicitly re-opts in through a verified channel.

---

### 16.4 Admin Panel Security

- Multi-factor authentication (MFA) required for all admin logins
- Session timeout after 30 minutes of inactivity
- All admin actions logged in audit trail
- IP allowlisting option for admin panel access
- Voice training sessions require active admin authentication before opening microphone

---

### 16.5 Compliance

- Compliant with **India's Digital Personal Data Protection Act (DPDPA) 2023**
- Aligned with **GDPR principles** for any international callers
- Compliant with **TRAI regulations** for outbound calling and DND
- Data retention: lead data retained for 12 months; call recordings for 6 months
- All data deletion requests managed by admin within 72 hours
- Consent audit trail retained for 24 months

---

## 17. Knowledge Management System

### 17.1 Knowledge Sources

All bot knowledge must originate from admin-approved sources:

- Official Bridgeon website content
- Course brochures and syllabi
- Internally approved FAQ documents
- Admin-entered Q&A pairs (typed or voice-trained)
- Approved call transcripts (after admin review)
- Placement team updates
- Administrative schedule updates
- Google Sheets (live sync)

### 17.2 Knowledge Architecture

```
Admin Training Interface (Text + Voice)
         │
         ├── Google Sheets Sync (auto every 15 min)
         │
         ▼
Knowledge Base (Vector DB — Pinecone / ChromaDB)
  ├── Course Information
  ├── Fees & Admissions
  ├── Student FAQs
  ├── Placement Data
  ├── Batch Schedules
  ├── Motivational Responses
  ├── Campaign Scripts
  └── Error Fallbacks
         │
         ▼
RAG Retrieval Layer
(Semantic search + live DB query on every caller query)
         │
         ▼
Response Generator
(GPT / Rasa grounded strictly to retrieved context)
         │
         ▼
Unanswered Query Logger
(Gaps → Continuous Learning Queue → Admin Alert)
```

### 17.3 Update Process

Content managers can update the following without developer help:

- FAQ questions and answers (English + Malayalam) — by typing or by voice
- Course details (name, duration, fees, eligibility)
- Batch schedules
- Placement statistics
- Motivational message library
- Greeting and farewell scripts
- After-hours fallback messages
- Outbound campaign scripts
- Google Sheets FAQ sync source

---

## 18. Technical Architecture

### 18.1 Full System Architecture

```
Inbound Phone Call / Outbound Campaign Trigger
        │
        ▼
Telephony Gateway (Twilio / Exotel / FreeSWITCH)
        │  WebSocket audio stream
        ▼
FastAPI Backend (Python)
  │  Real-time audio processing
  ▼
STT Engine (Google Cloud STT [paid] / Vosk [open-source])
  │  Transcribed text
  ▼
Language Detector + Intent Classifier
  │  Intent + user type + language
  ▼
RAG Pipeline (LangChain + Pinecone)
  │  Retrieve relevant knowledge chunks
  │  Pull live data from PostgreSQL / Google Sheets
  ▼
LLM (OpenAI GPT-4o [paid] / Rasa NLU [open-source])
  │  Generate grounded, tone-aware response
  ▼
Lead Capture Module (if triggered)
  │  Validate + store in PostgreSQL + consent log
  ▼
Consent & Opt-In Manager
  │  Record consent, check opt-out status
  ▼
Escalation Engine
  │  Resolved? → Continue
  │  Unresolved (3x)? → Transfer / Fallback
  ▼
TTS Engine (Azure Neural [paid] / Coqui TTS [open-source])
  │  Natural voice audio
  ▼
Telephony Gateway → Audio back to caller
  │
  ▼
Multi-Channel Dispatcher
  ├── WhatsApp (Twilio WhatsApp API) → Rich message / brochure
  ├── SMS (Twilio SMS / Exotel) → Text notification
  └── Email (SendGrid) → Internal lead alert / report

────────────────────────────────────────

Admin Control Panel (React.js)
  │  HTTPS API calls
  ▼
FastAPI Admin API
  ├── Knowledge CRUD (text + voice)
  ├── Training pipeline (text, document, voice, transcript)
  ├── Google Sheets sync manager
  ├── Call log retrieval
  ├── Lead management + consent records
  ├── Campaign manager (outbound)
  ├── Engine toggle (paid / open-source)
  └── Bot config settings
  │
  ▼
PostgreSQL (leads, logs, admin data, consent records)
Redis (session store, real-time state)
Pinecone (vector embeddings for RAG)
Firebase Storage (documents, recordings)
Google Sheets API (live FAQ sync)
```

---

### 18.2 Technology Stack

| Component | Paid / Production | Open-Source / Fallback |
|---|---|---|
| Telephony Gateway | Twilio Voice / Exotel | FreeSWITCH / Asterisk |
| Speech-to-Text | Google Cloud STT / Azure STT | Vosk |
| Text-to-Speech | Azure Neural Voice / Google TTS | Coqui TTS |
| NLP / LLM | OpenAI GPT-4o | Rasa NLU |
| Vector Store | Pinecone | ChromaDB (local) |
| Backend API | FastAPI (Python) | — |
| Admin Frontend | React.js | — |
| Database | PostgreSQL | — |
| Session Store | Redis | — |
| Document Storage | Firebase Storage | — |
| WhatsApp | Twilio WhatsApp API | — |
| SMS | Twilio SMS / Exotel SMS | — |
| Email | SendGrid | SMTP |
| Hosting | Google Cloud Run | — |
| Authentication | Firebase Auth + MFA | — |
| FAQ Sync | Google Sheets API | — |

---

## 19. Hybrid Tools Integration

### 19.1 Philosophy

The Bridgeon Voice Bot adopts a **hybrid tool strategy** — combining the reliability of all paid commercial services with the flexibility and cost-efficiency of free/open-source tools.

| Context | Recommended Approach |
|---|---|
| Production (live calls) | Paid tools — Twilio, Azure, Google, OpenAI |
| Prototyping and development | Open-source tools — FreeSWITCH, Vosk, Coqui, Rasa |
| Fallback (during outages) | Open-source tools serve as automatic backup |
| Cost-sensitive deployments | Open-source tools as primary with paid for critical paths |

---

### 19.2 Tool Mapping

#### Telephony

| Tool | Type | Use |
|---|---|---|
| Twilio Voice | Paid | Primary production telephony; inbound + outbound |
| Exotel | Paid | India-specific backup telephony |
| FreeSWITCH | Open-source | Self-hosted PBX for development and fallback |
| Asterisk | Open-source | Alternative open-source telephony server |

#### Speech-to-Text

| Tool | Type | Use |
|---|---|---|
| Google Cloud Speech-to-Text | Paid | Production STT; Malayalam (ml-IN) + English |
| Azure Speech STT | Paid | Alternative paid STT |
| Vosk | Open-source | Offline STT; prototyping; fallback |

#### Text-to-Speech

| Tool | Type | Use |
|---|---|---|
| Azure Neural Voice | Paid | Production TTS; natural voice quality |
| Google TTS | Paid | Alternative paid TTS |
| Coqui TTS | Open-source | Open-source TTS for development; Malayalam support |

#### NLP / Conversational AI

| Tool | Type | Use |
|---|---|---|
| OpenAI GPT-4o / Azure OpenAI | Paid | Production LLM; RAG-grounded response generation |
| Rasa NLU / local open-source LLMs | Open-source | Open-source NLU and conversational generation; fallback or primary use when paid engines are unavailable |

---

### 19.3 Admin Engine Toggle

The admin panel includes a **Global Engine Mode** setting:

```
Settings → Engine Configuration

  Engine Mode: [● Paid (Production)]  [○ Open-Source (Fallback)]

  Current configuration:
  ┌────────────┬──────────────────────────────────┐
  │ Component  │ Active Engine                    │
  ├────────────┼──────────────────────────────────┤
  │ Telephony  │ Twilio Voice                     │
  │ STT        │ Google Cloud Speech-to-Text      │
  │ TTS        │ Azure Neural Voice               │
  │ NLP / LLM  │ OpenAI GPT-4o                   │
  └────────────┴──────────────────────────────────┘

  [Switch to Open-Source Mode]   [Save Configuration]
```

Switching modes applies to all new calls and interactions immediately. A confirmation prompt is displayed before switching in production to prevent accidental changes.

---

### 19.4 Fallback Behaviour

When a paid engine is unavailable (detected via health check), the system automatically switches to the open-source fallback:

```
Health check detects paid STT failure
           │
           ▼
System switches to Vosk for STT (automatic)
Admin is notified via dashboard alert + email
           │
           ▼
Calls continue without interruption
           │
           ▼
Paid engine restored → Admin prompted to switch back
```

---

## 20. Performance Requirements

| Requirement | Target |
|---|---|
| Inbound call answer time | Within 2 rings (~4 seconds) |
| Outbound call dial time | Within 5 seconds of campaign trigger |
| STT transcription latency | < 500ms real-time |
| Bot response generation | < 1.5 seconds after transcription |
| TTS audio generation | < 1 second |
| End-to-end voice response | < 3 seconds total |
| Concurrent calls supported | 100+ simultaneous |
| System uptime | 99% (24/7) |
| Knowledge base update propagation | < 30 seconds after admin saves |
| Voice training entry save time | < 30 seconds after admin confirms |
| Google Sheets sync delay | ≤ 15 minutes |
| WhatsApp message delivery | < 10 seconds after call end |
| SMS delivery | < 30 seconds |
| Admin panel load time | < 2 seconds |
| FAQ retrieval accuracy | > 85% |
| User type detection accuracy | > 90% |
| Voice transcription accuracy (English) | > 90% |
| Voice transcription accuracy (Malayalam) | > 85% |
| Opt-out processing time | < 60 seconds |

---

## 21. Acceptance Criteria

| Feature | Acceptance Criteria |
|---|---|
| Call answering | 100% of test calls answered within 2 rings |
| Consent disclosure | Recording notice plays on 100% of calls where recording is enabled |
| Bilingual greeting | Malayalam + English greeting plays on every call |
| User type detection | ≥ 90% correct classification across 50 test calls |
| FAQ retrieval | ≥ 85% accurate spoken response across sampled FAQ set |
| Lead capture | 100% of captured leads stored correctly with all fields and consent record |
| Voice recognition (English) | ≥ 90% accuracy in test environment |
| Voice recognition (Malayalam) | ≥ 85% accuracy in test environment |
| Language switching | Bot follows caller language change within one response |
| Escalation (office hours) | Call transferred to human after 3 failed attempts |
| Escalation (after hours) | Fallback message played and lead stored |
| Hallucination | Zero fabricated answers across all test scenarios |
| Admin knowledge add | New entry live in bot within 30 seconds of saving |
| Voice training | Voice-trained entry live within 30 seconds of admin confirmation |
| Admin training from transcript | Extracted Q&A pairs reviewed and importable |
| Training correction | Bot answer corrected and updated within 60 seconds |
| Outbound campaign | Campaign dials all consented contacts on schedule; retries unanswered per rules |
| Opt-out processing | Opt-out honoured and recorded within 60 seconds of request |
| WhatsApp delivery | Brochure or follow-up message delivered within 10 seconds of call end |
| Google Sheets sync | New FAQ rows live within 15 minutes of sheet update |
| Engine toggle | Switching engine mode takes effect on next new call |
| Fallback engine | System auto-switches to open-source within 60 seconds of paid engine failure |
| Admin login security | MFA enforced; session times out after 30 minutes |
| Knowledge rollback | Admin can revert to previous version in one click |

---

## 22. Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Malayalam STT errors with Kerala accents | Medium | High | Fine-tune with local accent recordings; DTMF fallback; Vosk as backup |
| LLM hallucination during calls | Medium | High | Strict RAG grounding; no free-form generation; zero-hallucination acceptance test |
| Call latency exceeds 3 seconds | Medium | High | Optimize STT-to-TTS pipeline; use streaming TTS |
| Admin enters incorrect knowledge via voice | Medium | Medium | STT transcription shown for confirmation before saving; version rollback available |
| Outbound campaign reaching non-consented contacts | Low | High | Mandatory consent check before every dial; DND registry integration |
| Paid API downtime (Twilio, Google, Azure) | Low | High | Auto-fallback to open-source engines; admin alert + dashboard indicator |
| Google Sheets sync failure | Low | Medium | Manual sync trigger available; stale data alert after 30 minutes |
| Lead data privacy breach | Low | High | AES-256 encryption; DPDPA compliance; role-based access controls |
| Caller frustration with voice bot | Medium | Medium | Easy escalation path; always offer human option |
| Knowledge base becomes outdated | Medium | Medium | Staleness alerts at 30 days; Google Sheets live sync; gap auto-detection |
| High concurrent call volume | Low | Medium | Auto-scaling on Google Cloud Run; queue management |
| WhatsApp message delivery failure | Low | Medium | SMS fallback if WhatsApp delivery fails; retry logic |
| Open-source STT/TTS quality gap | Medium | Medium | Paid engines as default; open-source used only in fallback/dev mode |

---

## 23. Competitive Differentiation

When callers ask why they should choose Bridgeon, the bot communicates these verified differentiators:

| Differentiator | Spoken Response |
|---|---|
| Practice-first | *"At Bridgeon, most of your day is spent actually coding, debugging, and building real apps — not just attending lectures."* |
| Industry simulation | *"Bridgeon operates like a real tech company. You work on actual projects under conditions that mirror the industry."* |
| Holistic training | *"Beyond coding, you'll develop communication skills, presentation skills, and professional habits — exactly what companies look for."* |
| Earn While You Learn | *"High-performing students can start earning through live projects by Year 2 of the program."* |
| Skill + Degree path | *"You can pursue a formal university degree like BCA or MCA alongside your bootcamp — skills and credentials together."* |
| Reputation | *"Bridgeon holds a 4.7 out of 5 rating across hundreds of student reviews on Justdial and Glassdoor."* |

**Rule:** Bot must never make unverified comparisons with competitor institutes.

---

## 24. KPIs & Success Metrics

### Business KPIs

| KPI | Target |
|---|---|
| Reduction in manual call handling | ≥ 60% within 3 months of launch |
| Leads captured per month | 30% increase over pre-bot baseline |
| Admission conversions from bot leads | ≥ 20% improvement |
| After-hours calls handled | 100% answered (vs 0% before bot) |
| Outbound campaign conversion rate | ≥ 15% of dialled leads express interest |

### Caller Experience KPIs

| KPI | Target |
|---|---|
| Call resolution rate (bot only) | > 75% of calls resolved without human |
| Average call duration | < 3 minutes for routine queries |
| Lead capture completion rate | > 70% of interested callers complete flow |
| CSAT score (post-call SMS survey) | > 4.5 / 5 |
| WhatsApp brochure acceptance rate | > 50% of prospective callers accept |

### AI Performance KPIs

| KPI | Target |
|---|---|
| Intent recognition accuracy | > 90% |
| Voice transcription accuracy | > 90% (EN), > 85% (ML) |
| Escalation rate | < 15% of all calls |
| Hallucination rate | 0% |
| Knowledge gap rate | < 10% of calls have unanswered questions |
| Continuous learning resolution rate | > 80% of flagged gaps closed within 7 days |

### Admin & Training KPIs

| KPI | Target |
|---|---|
| Knowledge base size at launch | ≥ 50 verified Q&A entries |
| Weekly knowledge updates by admin | ≥ 5 new or corrected entries |
| Voice-trained entries per week | ≥ 2 entries trained by voice |
| Time to correct a bot error | < 5 minutes from identification |
| Admin panel adoption | All content managers using panel weekly |
| Google Sheets sync uptime | > 99% successful syncs |

---

## 25. Future Enhancements

### Voice & Call Features
- Voicemail transcription and auto-response
- Voice biometric caller identification for returning students
- Post-call voice summary sent to caller via WhatsApp audio

### Student Features
- LMS integration: real-time attendance, grade queries over call
- Personalized weekly reminder calls for deadlines and assessments
- "Call your mentor" routing through the bot

### AI & Training Features
- Sentiment analysis: detect frustrated callers and prioritize escalation
- Long-term caller memory for returning users
- A/B testing different bot responses to optimize resolution rate
- Automated model fine-tuning from accumulated call data

### Admin Features
- Mobile admin app (iOS + Android) with voice training support
- Full CRM integration (Zoho / HubSpot) for lead pipeline management
- Role-based multi-campus management (different knowledge bases per campus)

### Platform Expansion
- Telegram Bot integration
- Tamil and Hindi language support
- Dedicated Bridgeon mobile app with in-app voice assistant
- In-app WhatsApp bot for full conversational flows (beyond notifications)

---

## 26. Milestones & Timeline

| Milestone | Week | Deliverable |
|---|---|---|
| M1 — PRD Approval + Content Setup | Week 1 | Signed PRD; knowledge base content collection begins |
| M2 — Telephony + Backend Setup | Week 2 | Twilio/Exotel integrated; FastAPI backend scaffolded; FreeSWITCH dev environment set up |
| M3 — Core Voice Bot (English) | Week 3 | STT + NLP + TTS pipeline; English FAQ calls working |
| M4 — Malayalam Support | Week 4 | Malayalam STT/TTS live; bilingual calls tested |
| M5 — Lead Capture + Escalation | Week 5 | Lead flow complete; human transfer working; consent recording live |
| M6 — Admin Control Panel | Week 6 | Full admin dashboard live; knowledge CRUD functional; engine toggle working |
| M7 — Bot Training System | Week 7 | Text training, transcript import, correction flow, voice training interface |
| M8 — RAG & Continuous Learning | Week 8 | Live DB retrieval, gap detection, Google Sheets sync |
| M9 — Outbound Campaigns | Week 9 | Campaign manager live; outbound calling with retry and consent tracking |
| M10 — Multi-Channel Integration | Week 10 | WhatsApp rich replies, SMS, email notifications live |
| M11 — Security & Compliance Audit | Week 11 | Full security review; DPDPA compliance check; consent audit |
| M12 — Testing & UAT | Week 12 | UAT with real callers and admin staff; all channels tested |
| M13 — Production Launch | Week 13 | Bot live on Bridgeon's phone number; all channels active; admin trained |

---

## 27. Glossary

| Term | Definition |
|---|---|
| Voice Call Assistant | An AI-powered bot that handles inbound and outbound phone calls using speech recognition and synthesis |
| Telephony Gateway | A service (e.g., Twilio, Exotel, FreeSWITCH) that bridges phone calls to the bot software system |
| STT | Speech-to-Text — converts spoken audio from a call into written text |
| TTS | Text-to-Speech — converts the bot's text response into a natural-sounding voice |
| RAG | Retrieval-Augmented Generation — the bot retrieves relevant knowledge before generating a response, preventing hallucination |
| Intent | The purpose behind a caller's words (e.g., "find out course fees") |
| Hallucination | When an AI generates plausible-sounding but incorrect or fabricated information |
| DTMF | Dual-Tone Multi-Frequency — keypad input used as a voice fallback (press 1, press 2, etc.) |
| Lead Capture | Collecting a caller's name, phone, and course interest for admissions follow-up |
| Escalation | Transferring a call from the bot to a human agent when the bot cannot resolve the query |
| Knowledge Base | The structured repository of Q&A pairs, course data, and FAQs the bot is trained on |
| Admin Panel | The web dashboard where Bridgeon staff control, configure, and train the bot |
| Bot Training | The process of adding new knowledge entries so the bot can answer more questions |
| Voice Training | Training the bot by speaking entries aloud instead of typing them |
| Vector Database | A specialized database (e.g., Pinecone) that stores knowledge as semantic embeddings for fast retrieval |
| Session | A single phone call interaction from answer to disconnect |
| DPDPA | Digital Personal Data Protection Act — India's data protection law (2023) |
| TRAI | Telecom Regulatory Authority of India — governs telecom services and DND regulations |
| CSAT | Customer Satisfaction Score — post-call satisfaction rating |
| UAT | User Acceptance Testing — validation testing by real staff and callers before go-live |
| MFA | Multi-Factor Authentication — security layer for admin panel login |
| SSML | Speech Synthesis Markup Language — used to control voice pace, emphasis, and pauses in TTS |
| DND | Do Not Disturb — TRAI registry of numbers that must not receive outbound marketing calls |
| Opt-In | Explicit consent given by a contact to receive outbound calls or messages |
| Opt-Out | A contact's request to be removed from all outbound communication |
| Campaign Manager | The admin tool for scheduling, running, and monitoring outbound call/message campaigns |
| Hybrid Tools | A deployment strategy combining paid commercial APIs with open-source tools |
| FreeSWITCH | Open-source telephony server used for development and fallback telephony |
| Asterisk | Open-source PBX system; alternative to FreeSWITCH |
| Vosk | Open-source offline speech recognition library with Malayalam support |
| Coqui TTS | Open-source text-to-speech system supporting multiple languages |
| Rasa | Open-source conversational AI framework for NLU and dialogue management |
| Google Sheets Sync | Automated process that pulls FAQ updates from a connected Google Sheet into the knowledge base |
| Continuous Learning | The system's ability to automatically identify knowledge gaps and surface them for admin training |
| Engine Toggle | Admin panel control to switch between paid and open-source AI/telephony engines |

---

## Conclusion

The Bridgeon Voice Call Assistant v4.0 is a fully evolved, multi-channel, AI-powered communication platform — purpose-built for Bridgeon Skillversity.

This version takes the inbound voice bot of v1.0 and transforms it into a proactive, omnichannel engagement system that:

- **Answers every inbound call** — 24/7, in natural Malayalam and English, with zero wait time
- **Reaches out proactively** — through scheduled outbound campaigns with smart retry logic and full consent management
- **Communicates everywhere** — via WhatsApp rich messages, SMS, and email alongside voice
- **Trains itself continuously** — through RAG-powered gap detection, Google Sheets sync, and admin voice training
- **Stays secure and compliant** — with DPDPA-aligned consent recording, opt-in/opt-out tracking, and encrypted data handling
- **Runs flexibly** — on a hybrid tool stack that puts paid APIs in production and open-source tools on standby

The admin remains in full control — from speaking new knowledge entries into the bot, to toggling between engines, to launching campaigns — all without writing a single line of code.

This document is the foundational specification for v4.0 development. All sections are subject to revision following stakeholder review and technical discovery during implementation.

---

*Document Version 4.0 | Bridgeon Voice Call Assistant PRD | June 2026*
