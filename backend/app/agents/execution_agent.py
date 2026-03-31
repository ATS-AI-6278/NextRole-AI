from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.gmail.client import GmailClient
from app.memory.relational.models import GmailAccount, JobApplication
from app.memory.relational.repository import get_or_create_user_by_chat_id


from app.core.ai_client import AIClient

class ExecutionAgent:
    def __init__(self) -> None:
        self.ai = AIClient()

    def _normalize(self, text: str) -> str:
        return (text or "").strip()

    async def _send_telegram(self, chat_id: str, text: str) -> None:
        if not settings.TELEGRAM_BOT_TOKEN:
            return
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": text},
            )

    def _format_job_updates(self, jobs: List[JobApplication]) -> str:
        if not jobs:
            return "No job applications found yet. Connect Gmail and ingest emails first."
        lines = ["Your job application statuses:"]
        for j in jobs[:20]:
            applied = f"Applied: {j.applied_at.date().isoformat()}" if j.applied_at else "Applied: unknown"
            lines.append(f"- {j.company}" + (f" ({j.role})" if j.role else "") + f": {j.status}. {applied}")
        return "\n".join(lines)

    async def handle_update(self, *, update: Dict[str, Any], db: Session) -> None:
        message = update.get("message") or update.get("edited_message") or {}
        chat = message.get("chat") or {}
        chat_id = str(chat.get("id", ""))
        text = self._normalize(message.get("text", ""))

        if not chat_id or not text:
            return

        user = get_or_create_user_by_chat_id(db, telegram_chat_id=chat_id)
        gmail_client = GmailClient()

        if text.startswith("/start"):
            await self._send_telegram(
                chat_id,
                "Welcome to NextRole AI.\n"
                "I am your autonomous career assistant. You can chat with me naturally!\n"
                "Try asking:\n"
                "- 'How are my job applications doing?'\n"
                "- 'Did I hear back from Google?'\n"
                "- 'Clean up my newsletters from today.'\n"
                "- 'Connect my Gmail account.'"
            )
            return

        prompt = (
            "You are the NextRole AI Command Center. Parse the user's message and determine the intended action.\n"
            "Possible actions:\n"
            "- 'connect_gmail': User wants to link their Gmail account.\n"
            "- 'show_updates': User wants to see job application statuses. Params: {'company': string|null}.\n"
            "- 'archive_marketing': User wants to archive newsletters/marketing. Params: {'days': int}.\n"
            "- 'delete_spam': User wants to move spam to trash. Params: {'days': int}.\n"
            "- 'unknown': Default if no action matches.\n\n"
            "Return JSON: {\"action\": \"...\", \"params\": {...}}.\n\n"
            f"User Message: {text}"
        )

        intent = await self.ai.generate_json(prompt)
        action = intent.get("action", "unknown")
        params = intent.get("params", {})

        if action == "connect_gmail":
            start_url = f"{settings.TELEGRAM_BASE_URL.rstrip('/')}/gmail/oauth/start?chat_id={chat_id}"
            await self._send_telegram(chat_id, f"Connect Gmail: {start_url}")
            return

        if action == "show_updates":
            company_kw = params.get("company")
            stmt = select(JobApplication).where(JobApplication.user_id == user.id).order_by(JobApplication.last_status_at.desc())
            jobs = list(db.execute(stmt).scalars().all())
            if company_kw:
                jobs = [j for j in jobs if company_kw.lower() in (j.company or "").lower() or (j.role or "").lower().find(company_kw.lower()) >= 0]
            await self._send_telegram(chat_id, self._format_job_updates(jobs))
            return

        if action == "archive_marketing":
            days = params.get("days") or 1
            accounts = list(db.execute(select(GmailAccount).where(GmailAccount.user_id == user.id)).scalars().all())
            processed = 0
            for acc in accounts:
                service = gmail_client.build_service_from_refresh_token(refresh_token_encrypted=acc.oauth_refresh_token_encrypted)
                ids = gmail_client.list_messages(
                    service=service,
                    query=f"newer_than:{days}d label:Newsletter",
                    max_results=100,
                )
                for m in ids:
                    gmail_client.archive_message(service=service, message_id=m["message_id"])
                    processed += 1
            await self._send_telegram(chat_id, f"Archived {processed} marketing emails from the last {days} day(s).")
            return

        if action == "delete_spam":
            days = params.get("days") or 1
            accounts = list(db.execute(select(GmailAccount).where(GmailAccount.user_id == user.id)).scalars().all())
            processed = 0
            for acc in accounts:
                service = gmail_client.build_service_from_refresh_token(refresh_token_encrypted=acc.oauth_refresh_token_encrypted)
                ids = gmail_client.list_messages(
                    service=service,
                    query=f"newer_than:{days}d label:Spam",
                    max_results=100,
                )
                for m in ids:
                    gmail_client.trash_message(service=service, message_id=m["message_id"])
                    processed += 1
            await self._send_telegram(chat_id, f"Moved {processed} spam emails from the last {days} day(s) to Trash.")
            return

        await self._send_telegram(
            chat_id,
            "I'm not sure how to do that yet. Try asking for job updates or to clean your inbox!"
        )

