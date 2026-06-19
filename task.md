# Bridgeon Voice Call Assistant — Implementation Tasks

## Project Overview
This task document breaks the PRD into phased, step-by-step work items for building the Bridgeon Voice Call Assistant v4.0.

---

## Phase 1: Scaffold a runnable app ✅ Completed
1. [x] Create the repository structure with backend + frontend folders.
2. [x] Add a FastAPI backend skeleton with a `/health` endpoint.
3. [x] Add a React (Vite) frontend placeholder page.
4. [x] Write README instructions for starting both locally.
5. [x] Install backend Python dependencies
6. [x] Install frontend Node.js dependencies
7. [x] Verify backend starts and `/health` returns 200
8. [x] Verify frontend opens and displays live backend status

Deliverable: backend starts, frontend opens, and the app is visibly running.

## Phase 2: Admin dashboard shell with live sample data ✅ Completed
1. [x] Build a basic admin dashboard UI shell.
2. [x] Add backend API endpoints that return static cards and configuration data.
3. [x] Connect dashboard UI to the backend.

Deliverable: open the admin page and see live data rendered from the backend.

## Phase 3: Voice flow simulation and basic bot pipeline ✅ Completed
1. [x] Add a local API endpoint for a simulated voice session.
2. [x] Implement a simple text-based bot response route.
3. [x] Add a frontend or test page to submit questions and display responses.

Deliverable: simulate a call/query and see the bot return a response.

## Phase 4: Knowledge base CRUD and FAQ response ✅ Completed
1. [x] Define FAQ/knowledge models for backend storage.
2. [x] Build create/read/update/delete endpoints for knowledge entries.
3. [x] Add admin UI for managing FAQs.
4. [x] Use stored FAQ entries to answer bot queries.

Deliverable: manage FAQ entries in the UI and query the bot using saved content.

## Phase 5: Lead capture and consent flow ✅ Completed
1. [x] Add lead and consent data models.
2. [x] Build lead capture endpoints with phone validation.
3. [x] Add a simple form or flow in the UI to collect leads and consent.

Deliverable: capture a lead, store it, and verify the record exists.

## Phase 6: Bilingual support and language selection ✅ Completed
1. [x] Add support for English and Malayalam fields in knowledge and lead flows.
2. [x] Implement language detection or selection for the bot.
3. [x] Update UI to display and manage both languages.

Deliverable: see bilingual content in the app and receive responses in the selected language.

## Phase 7: Telephony integration stub and service interface ✅ Completed
1. [x] Add a telephony adapter interface in the backend.
2. [x] Implement a local call simulator for inbound audio/text.
3. [x] Wire STT/TTS service classes with stubbed connectors.

Deliverable: simulate an inbound call and observe the full pipeline locally.

## Phase 8: RAG retrieval prototype ✅ Completed
1. [x] Add a local vector store prototype and embedding pipeline.
2. [x] Load knowledge/docs into the retriever.
3. [x] Route bot answers through grounded retrieval.

Deliverable: ask a knowledge question and see a grounded retrieval-based answer.

## Phase 9: Engine/settings toggles and admin config ✅ Completed
1. [x] Add admin settings for engine mode, office hours, and escalation.
2. [x] Add backend config storage.
3. [x] Add UI controls to update settings.
4. [x] Wire bot greeting, office hours, and escalation to runtime settings.

Deliverable: change a setting in the UI and see it affect bot behavior.

## Phase 10: Metrics dashboard and monitoring stub ✅ Completed
1. [x] Add event tracking for calls and leads.
2. [x] Build a simple analytics dashboard page.
3. [x] Display runtime metrics such as call count and lead count.

Deliverable: generate sample events and view live metrics.

## Phase 11: Security and audit basics ✅ Completed
1. [x] Add simple admin authentication or access gate.
2. [x] Add audit logging for key actions.
3. [x] Ensure data access is protected in the backend.

Deliverable: log in and see audit records for actions taken.

## Phase 12: Production readiness and test harness ✅ Completed
1. [x] Add local test scripts and checks.
2. [x] Add CI/run instructions for starting backend and frontend.
3. [x] Validate the app starts cleanly in the current environment.

Deliverable: run the app and basic tests, confirming it is production-ready enough to review.

---

## Quick Start Task List
- [x] Create the repo and local app scaffold.
- [x] Build the admin dashboard shell with backend connectivity.
- [x] Add a simple bot simulation endpoint.
- [x] Implement knowledge base CRUD.
- [x] Add lead capture and consent handling.
- [x] Add bilingual support.
- [x] Add telephony simulation and service adapter.
- [x] Add RAG retrieval prototype.
- [x] Add settings toggles and admin config.
- [x] Add basic analytics and audit tracking.
- [x] Validate the full app end-to-end locally.
