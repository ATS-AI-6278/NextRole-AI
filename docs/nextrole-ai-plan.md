---
name: NextRole AI Plan
overview: Create a full-stack MVP (FastAPI + Next.js) for an autonomous email assistant with multi-agent pipelines, Gmail integration, SQLite structured memory, and Chroma semantic memory, plus Telegram chat/alerts and a scheduled digest.
todos:
  - id: repo-skeleton
    content: Create monorepo folder structure (`backend/`, `frontend/`, `docs/`) and save the plan as `[docs/nextrole-ai-plan.md]` + root `[README.md]`.
    status: in_progress
  - id: backend-core
    content: Scaffold FastAPI app with `/health`, config management, SQLAlchemy+SQLite models, and Chroma wrapper under `[backend/app/memory]`.
    status: pending
  - id: gmail-client
    content: Implement Gmail API client for OAuth and message operations (list/read/modify labels; archive=remove INBOX; trash=add TRASH).
    status: pending
  - id: privacy-ingestion
    content: Add `PrivacyAgent` with secret detection/redaction and ingestion pipeline that stores structured + semantic memory after redaction.
    status: pending
  - id: classifier-agent
    content: Implement `ClassifierAgent` that tags emails (Newsletter/Job_Applied/Job_Offer/Spam/Personal) and applies Gmail labels.
    status: pending
  - id: career-tracker
    content: Implement `CareerTrackerAgent` that extracts job confirmations into `job_applications`, then updates status based on later domain/thread signals.
    status: pending
  - id: execution-agent-telegram
    content: Implement Telegram webhook + `ExecutionAgent` with an initial command set (e.g. query application updates, archive marketing, forward links, move-to-trash).
    status: pending
  - id: reporting-scheduler
    content: Implement scheduled digests 3x/day via `[backend/app/scheduler/digests.py]`, summarizing DB events and sending Telegram messages.
    status: pending
  - id: dashboard-mvp
    content: Create Next.js dashboard pages for application list/status, plus REST client in `[frontend/src/lib/api.ts]`.
    status: pending
  - id: dev-workflow
    content: Add manual trigger endpoints for ingestion + digest (dev-only) and document env vars + run commands in root README.
    status: pending
isProject: false
---

## Target MVP (build first)
- Multi-agent ingestion & privacy pipeline that reads Gmail messages, detects/redacts secrets, classifies them, and stores structured + semantic memory.
- Career tracking that extracts application confirmations and updates status on later messages.
- Telegram command execution (start with a small set: search application replies, archive/remove marketing, forward links).
- Scheduled digests (3x/day) that summarize activity and send a formatted message to Telegram.
- Web dashboard to visualize tracked applications and their statuses, with basic semantic “search conversations/emails”.
- Multi-user readiness: memory and data partitioned by Telegram `chat_id` (and corresponding Gmail account) so other users can use the system via their own chat.

### High-level architecture
```mermaid
flowchart LR
  User[User via Telegram] -->|messages/commands| TGBot[Telegram Webhook Handler]
  TGBot --> ExecAgent[Execution Agent]
  TGBot --> Reporting[Reporting Agent (cron)]

  TGBot --> Ingest[Ingestion & Privacy Agent]
  Ingest --> Classifier[Classifier Agent]
  Ingest --> Career[Career Tracker Agent]

  Ingest --> Gmail[Gmail API]
  Classifier --> Gmail
  Career --> Gmail

  Ingest --> RelDB[(Relational Memory: SQLite)]
  Career --> RelDB

  Ingest --> VectorDB[(Vector Memory: Chroma)]
  Reporting --> VectorDB

  Dashboard[Next.js Dashboard] --> API[FastAPI REST API]
  API --> RelDB
  API --> VectorDB
```



### Multi-agent interfaces (implementation approach)
- Implement “agents” as Python modules with a shared interface:
  - `run(input, context) -> AgentOutput` where `context` includes `user_id`, `gmail_account_id`, and `db session`.
- Store per-email/thread summaries in vector DB *after* the privacy agent redacts secrets.

### Data model (minimum viable)
- `users` (id, telegram_chat_id, created_at)
- `gmail_accounts` (id, user_id, oauth_refresh_token_encrypted?, email_address)
- `threads` (id, gmail_message_id/thread_id, user_id, labels_applied)
- `job_applications` (id, user_id, company, role, applied_at, status, last_status_at, source_message_id)
- `email_events` (id, user_id, message_id, thread_id, event_type, extracted_entities JSON, created_at)
- `privacy_flags` (id, user_id, message_id, detected_secret_type, created_at)

### Secrets/privacy rules (must be enforced in code)
- Regex-based detection for: `OTP`, `Password`, `Verification Code`, common “one-time code” patterns.
- When detected:
  - Send the detected secret alert to the user via Telegram.
  - Redact sensitive substrings before:
    - writing to logs,
    - saving to relational structured memory, and
    - embedding/saving to Chroma.
- Auto actions:
  - “clutter/archive” means remove `INBOX` label.
  - “trash” means add `TRASH` label.
- No permanent delete except on explicit user command.

## Repo scaffolding to create (new files)
- `[docs/nextrole-ai-plan.md]` (this plan, saved)
- `[README.md]` (root setup + env vars + run instructions)
- Backend:
  - `[backend/app/main.py]` (FastAPI entry)
  - `[backend/app/api/routes.py]` (REST routes)
  - `[backend/app/telegram/webhook.py]` (Telegram webhook handler)
  - `[backend/app/gmail/client.py]` (OAuth + Gmail API wrapper)
  - `[backend/app/agents/privacy_agent.py]`
  - `[backend/app/agents/classifier_agent.py]`
  - `[backend/app/agents/career_tracker_agent.py]`
  - `[backend/app/agents/execution_agent.py]`
  - `[backend/app/agents/reporting_agent.py]`
  - `[backend/app/memory/relational/models.py]` + `[backend/app/memory/relational/repository.py]`
  - `[backend/app/memory/vector/chroma_client.py]`
  - `[backend/app/scheduler/digests.py]` (3x/day trigger)
  - `[backend/requirements.txt]` or `pyproject.toml`
- Frontend:
  - `[frontend/package.json]`
  - `[frontend/app/page.tsx]` (Next.js entry)
  - `[frontend/app/dashboard/page.tsx]` (applications list)
  - `[frontend/app/api/*]` if needed for server actions (optional)
  - `[frontend/src/lib/api.ts]` (client for backend REST API)

## Implementation steps (in the order we’ll do them after you confirm)
1. Create the repo skeleton: `backend/`, `frontend/`, `docs/`, base configs.
2. Backend core:
  - FastAPI app + health endpoint.
  - SQLAlchemy models + SQLite setup.
  - Chroma persistence setup + a simple “store/retrieve embedding by thread summary” abstraction.
3. Gmail integration MVP (Gmail only):
  - OAuth flow scaffolding and token storage structure.
  - API wrapper for: list messages by query, read message payload, modify labels, move to trash, archive.
4. Privacy + ingestion pipeline:
  - `PrivacyAgent` secret detection + redaction.
  - Ingestion service that pulls messages, runs privacy + classification, applies Gmail labels, and stores memory.
5. Career tracking:
  - Extraction of company/role/applied_at from confirmation emails.
  - Status updates when future emails arrive from matching domains/threads.
6. Execution agent + Telegram:
  - Telegram webhook endpoint.
  - Parse a minimal command set and call Gmail + DB.
7. Reporting agent:
  - Scheduler running 3 times per day, querying DB for counts + job updates.
  - Generate and send digest message via Telegram.
8. Dashboard:
  - Display job applications list with status timeline.
  - “View details” fetches message/event summaries and (optional) vector search.
9. Basic operator workflows:
  - Add admin/debug endpoints for manual trigger of ingestion and digest (used in dev).

## Key initial assumptions (can change if you tell me)
- Telegram integration uses a FastAPI webhook endpoint (not long polling) for reliability.
- Gmail ingestion starts with periodic polling (no Pub/Sub push yet).
- LLM provider is pluggable; default implementation will read provider + model from env vars.

### User questions (inputs already gathered)
- Gmail: `Gmail only`.
- Memory DB: `SQLite first`.
- Vector store: `ChromaDB`.
- Dev runtime: local Python backend + local Next.js.
