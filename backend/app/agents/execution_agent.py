from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.gmail.client import GmailClient
from app.memory.relational.models import GmailAccount, JobApplication
from app.core.dependencies import get_ai_client, get_chroma_client
from app.agents.privacy_agent import IngestionPipeline
from app.memory.vector.chroma_client import ChromaClient
from app.memory.relational.repository import (
    get_or_create_user_by_chat_id, 
    get_latest_pending_action, 
    update_pending_action_status,
    create_pending_action,
    get_incomplete_scan_task,
    start_scan_task,
)

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

        # 1. Handle Proactive Confirmations ("Yes", "Do it")
        if text.lower() in ["yes", "confirm", "do it", "sure", "ok", "okay", "go ahead"]:
            pending = get_latest_pending_action(db, user.id)
            if pending:
                await self._send_telegram(chat_id, f"⚡ Executing: {pending.description}...")
                accounts = list(db.execute(select(GmailAccount).where(GmailAccount.user_id == user.id)).scalars().all())
                
                total_done = 0
                for acc in accounts:
                    service = gmail_client.build_service_from_refresh_token(refresh_token_encrypted=acc.oauth_refresh_token_encrypted)
                    if pending.action_type == "trash":
                        # Applying both TRASH and removing INBOX in one batch call
                        gmail_client.batch_modify_labels(service=service, message_ids=pending.message_ids, add_label_ids=["TRASH"], remove_label_ids=["INBOX"])
                        # SYNC: Forget the junk in AI Memory too
                        chroma.delete_message_summaries(user_id=user.id, message_ids=pending.message_ids)
                    elif pending.action_type == "archive":
                        gmail_client.batch_modify_labels(service=service, message_ids=pending.message_ids, remove_label_ids=["INBOX"])
                    total_done += len(pending.message_ids)

                
                update_pending_action_status(db, pending.id, "completed")
                await self._send_telegram(chat_id, f"✅ Done! {total_done} messages processed. Your inbox is cleaner now.")
                return

        # 2. Parse Intent
        
        prompt = (
            "You are the NextRole AI Agent. Parse the user's message and determine the action.\n"
            "ACTIONS:\n"
            "- 'scan_inbox': Refresh/scan mail. Params: {'limit': int}. Use limit 500 if they say 'FULL SCAN' or 'WHOLE'.\n"
            "- 'show_updates': Query job status or email history.\n"
            "- 'unknown': Natural chat.\n\n"
            f"User Message: {text}"
        )

        intent = await self.ai.generate_json(prompt, model_type="lite")
        action = intent.get("action", "unknown")
        params = intent.get("params", {}) or {}

        if action == "scan_inbox":
            incomplete = get_incomplete_scan_task(db, user.id)
            scan_limit = params.get("limit") or 20
            if "full scan" in text.lower() or "whole" in text.lower():
                scan_limit = 500

            if incomplete:
                await self._send_telegram(
                    chat_id, 
                    f"🔍 Ooh yeah, I remember I was doing a scan of your last {incomplete.scan_limit} emails, but I ran into a bit of a problem. "
                    f"I've already finished {incomplete.processed_count}. Let me pick up exactly where I left off!"
                )
                scan_id = incomplete.id
                scan_limit = incomplete.scan_limit
            else:
                if scan_limit >= 500:
                    await self._send_telegram(chat_id, f"🚀 Initiating a **FULL SCAN** of your last {scan_limit} emails. This will be deep and thorough...")
                else:
                    await self._send_telegram(chat_id, "🔍 Scanning your inbox for updates...")
                
                new_task = start_scan_task(db, user.id, "full_scan", scan_limit)
                scan_id = new_task.id
            
            total_processed = 0
            all_observations = {"spam": [], "newsletter": [], "marketing": []}
            
            pipeline = IngestionPipeline()
            accounts = list(db.execute(select(GmailAccount).where(GmailAccount.user_id == user.id)).scalars().all())

            for acc in accounts:
                service = gmail_client.build_service_from_refresh_token(refresh_token_encrypted=acc.oauth_refresh_token_encrypted)
                res = await pipeline.run_for_account(
                    db=db, user_id=user.id, telegram_chat_id=chat_id, 
                    gmail_account_id=acc.id, gmail_service=service, 
                    gmail_client=gmail_client, chroma_client=chroma, 
                    query="in:inbox", max_results=scan_limit,
                    scan_task_id=scan_id
                )
                if isinstance(res, dict):
                    total_processed += res.get("processed", 0)
                    obs = res.get("observations", {})
                    for k in all_observations:
                        all_observations[k].extend(obs.get(k, []))
            
            # Agentic Proactive Reasoning
            report_prompt = (
                f"Generate a scan summary for {username}. \n"
                f"Scan Results: {total_processed} new emails ingested.\n"
                f"Observations: {len(all_observations['spam'])} spam, {len(all_observations['newsletter'])} newsletters.\n"
                "Task: Write a professional, friendly briefing. If there is spam or newsletters, "
                "proactively ask if the user wants you to clean them up (archive newsletters or trash spam). "
                "Be brief and encouraging."
            )
            report_text = await self.ai.generate_text(report_prompt, model_type="lite")
            
            # Persist pending actions for confirmation later
            if all_observations["spam"]:
                create_pending_action(db, user.id, "trash", f"Delete {len(all_observations['spam'])} spam emails", all_observations["spam"])
            elif all_observations["newsletter"]:
                create_pending_action(db, user.id, "archive", f"Archive {len(all_observations['newsletter'])} newsletters", all_observations["newsletter"])

            await self._send_telegram(chat_id, report_text)
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

