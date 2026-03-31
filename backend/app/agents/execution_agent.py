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


from app.core.dependencies import get_ai_client, get_chroma_client

import logging
logger = logging.getLogger(__name__)

class ExecutionAgent:
    def __init__(self) -> None:
        self.ai = get_ai_client()

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
        chroma = get_chroma_client()

        logger.info(f"Telegram Update: User={chat_id} Text='{text[:50]}...'")

        if text.startswith("/start"):
            await self._send_telegram(
                chat_id,
                "Welcome to NextRole AI.\n"
                "I am your autonomous career assistant. You can chat with me naturally!\n"
                "Try asking:\n"
                "- 'How are my job applications doing?'\n"
                "- 'Did I hear back from Google?'\n"
                "- 'Scan my inbox now.'\n"
                "- 'Connect my Gmail account.'"
            )
            return

        prompt = (
            "You are the NextRole AI Command Center. Parse the user's message and determine the intended action.\n"
            "CRITICAL RULES:\n"
            "1. ONLY return 'scan_inbox' if the user explicitly asks to 'scan', 'pull', or 'refresh' their inbox now.\n"
            "2. If the user asks a question about counts (e.g., 'how many emails?'), status updates, or specific companies (e.g., 'Did I hear from X?'), return 'show_updates'.\n"
            "3. If they are just chatting, return 'unknown'.\n\n"
            "Possible actions:\n"
            "- 'connect_gmail': User wants to link their Gmail account.\n"
            "- 'scan_inbox': Force a fresh scan of the inbox for new messages.\n"
            "- 'show_updates': Query the current memory for job statuses, email counts, or history. Params: {'query': string|null}.\n"
            "- 'archive_marketing': Archive newsletters. Params: {'days': int}.\n"
            "- 'delete_spam': Delete spam. Params: {'days': int}.\n"
            "- 'unknown': Natural chat without a specific system action.\n\n"
            "Return JSON: {\"action\": \"...\", \"params\": {...}}.\n\n"
            f"User Message: {text}"
        )

        intent = await self.ai.generate_json(prompt, model_type="lite")
        action = intent.get("action", "unknown")
        params = intent.get("params", {})

        if action == "scan_inbox":
            await self._send_telegram(chat_id, "🔍 Scanning your inbox for new updates...")
            total_processed = 0
            total_updates = 0
            total_secrets = 0
            total_failed = 0
            
            from app.agents.privacy_agent import IngestionPipeline
            pipeline = IngestionPipeline()
            # USE scalars().all() to ensure we get Model objects, not Rows.
            accounts = list(db.execute(select(GmailAccount).where(GmailAccount.user_id == user.id)).scalars().all())

            for acc in accounts:
                service = gmail_client.build_service_from_refresh_token(refresh_token_encrypted=acc.oauth_refresh_token_encrypted)
                res = await pipeline.run_for_account(
                    db=db, user_id=user.id, telegram_chat_id=chat_id,
                    gmail_account_id=acc.id, gmail_service=service, gmail_client=gmail_client,
                    chroma_client=chroma, query="newer_than:1d"
                )
                if isinstance(res, dict):
                    total_processed += res.get("processed", 0)
                    total_updates += res.get("career_updates", 0)
                    total_secrets += res.get("secrets_alerted", 0)
                    total_failed += res.get("failed", 0)
            
            summary_msg = f"✅ Inbox scan complete!\n- Emails Ingested: {total_processed}\n- Job Updates Found: {total_updates}\n- Secrets Redacted: {total_secrets}"
            if total_failed > 0:
                summary_msg += f"\n- ⚠️ Skipped (Errors): {total_failed}"
            
            if total_processed == 0 and total_updates == 0 and total_failed == 0:
                summary_msg = "✅ Scan complete! Your inbox was already up to date."
                
            await self._send_telegram(chat_id, summary_msg)
            return

        if action == "connect_gmail":
            start_url = f"{settings.TELEGRAM_BASE_URL.rstrip('/')}/gmail/oauth/start?chat_id={chat_id}"
            await self._send_telegram(chat_id, f"Connect Gmail: {start_url}")
            return

        if action == "show_updates":
            query = params.get("query")
            logger.info(f"Action: show_updates Query='{query}'")
            # Intelligent Context Search: Query Vector DB for semantic matches first
            context_results = chroma.search_threads(user_id=user.id, query_text=text, top_k=3)
            context_text = "\n".join([r.text for r in context_results]) if context_results else ""
            
            stmt = select(JobApplication).where(JobApplication.user_id == user.id).order_by(JobApplication.last_status_at.desc())
            jobs = list(db.execute(stmt).scalars().all())
            
            summary_prompt = (
                f"User asked: '{text}'\n\n"
                f"Job Database Statuses:\n{self._format_job_updates(jobs)}\n\n"
                f"Relevant Email Context:\n{context_text}\n\n"
                "Provide a natural, helpful response to the user. "
                "If they asked about a specific company, focus on that."
            )
            # Use core model for final synthesis
            response_text = await self.ai.generate_text(summary_prompt, model_type="core")
            await self._send_telegram(chat_id, response_text)
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

        # DEFAULT: Natural Chatting Engagement & Long-Term Memory
        logger.info(f"Action: natural_chat User={user.id}")
        # 1. Record User Message in Chat Memory
        chroma.add_chat_message(user_id=user.id, text=text, role="user")

        # 2. Search for relevant context across both domains
        email_context_results = chroma.search_threads(user_id=user.id, query_text=text, top_k=5)
        chat_history_results = chroma.search_chat_history(user_id=user.id, query_text=text, top_k=3)

        email_context = "\n".join([r.text for r in email_context_results]) if email_context_results else "No relevant email context."
        chat_context = "\n".join([f"{r.metadata.get('role', 'unknown')}: {r.text}" for r in chat_history_results]) if chat_history_results else "No relevant past conversations."
        
        chat_prompt = (
            "You are NextRole AI, a highly intelligent and helpful career assistant. "
            "You have access to the user's email history and past conversations. "
            "The user is chatting with you on Telegram. Speak naturally and helpfully.\n\n"
            f"User Message: {text}\n\n"
            f"--- RELEVANT EMAIL CONTEXT ---\n{email_context}\n\n"
            f"--- PAST CONVERSATION CONTEXT ---\n{chat_context}\n\n"
            "INSTRUCTIONS:\n"
            "1. Use the email context if they ask about jobs, status, or dates.\n"
            "2. Use the past conversation context to maintain continuity if they refer to previous topics.\n"
            "3. If neither context is relevant, be a friendly career coach."
        )
        
        # Use lite model for general chat
        chat_response = await self.ai.generate_text(chat_prompt, model_type="lite")
        
        # 3. Record Bot Response in Chat Memory
        chroma.add_chat_message(user_id=user.id, text=chat_response, role="bot")
        
        await self._send_telegram(chat_id, chat_response)

