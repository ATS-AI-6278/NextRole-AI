# NextRole AI

Conversational, multi-agent autonomous email assistant for tracking job applications via Telegram + a web dashboard.

## Repo Layout

- `backend/` - FastAPI backend (Gmail, Telegram, multi-agent pipeline, memory)
- `frontend/` - Next.js dashboard
- `docs/` - project docs (includes this plan copy)

## Prerequisites (MVP)

- Python 3.11+
- Node.js 18+

## Local Dev (after scaffolding)

Backend:
- `cd backend`
- Create a virtual env and install deps:
  - `python -m venv .venv`
  - `./.venv/Scripts/activate` (Windows PowerShell)
  - `pip install -r requirements.txt`
- Run:
  - `uvicorn app.main:app --reload --port 8000`

Frontend:
- `cd frontend`
- `npm install`
- Run:
  - `npm run dev -- -p 3000`

## Environment Variables

Backend will use (eventually) the following env vars (names can evolve during MVP scaffolding):

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`
- `TELEGRAM_BASE_URL` (public URL for webhook)
- `GMAIL_OAUTH_CLIENT_ID`
- `GMAIL_OAUTH_CLIENT_SECRET`
- `GMAIL_OAUTH_REDIRECT_URL`
- `ENCRYPTION_KEY` (for refresh token encryption; 32-byte base64-safe for Fernet)
- `DATABASE_URL` (MVP default: `sqlite:///./nextrole.db`)
- `CHROMA_PERSIST_DIR`
- `ENVIRONMENT` (set to `dev` for dev-only endpoints; default is `dev`)

Frontend:
- `NEXT_PUBLIC_BACKEND_URL` (e.g. `http://localhost:8000`)

## Notes

This MVP is privacy-forward:
- detected secrets (OTP/password/verification codes) are sent to the user and redacted before being stored in long-term memory.

## Dev-only Endpoints (MVP testing)

- `POST /dev/ingest`
  - body: `{ "query": "newer_than:1d", "chat_id": "<optional telegram chat_id>" }`
  - runs ingestion for your connected Gmail accounts and stores memory after redaction
- `POST /dev/digest`
  - body: `{ "briefing": "Dev Digest" }`
  - sends a digest immediately for all users

## Running the dashboard

- Open `frontend` in your browser, enter your Telegram `chat_id`, and refresh the dashboard.
- If you want to connect Gmail, use the `connect gmail` command in the Telegram bot (or open the returned OAuth URL).

