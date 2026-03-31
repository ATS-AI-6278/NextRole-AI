from __future__ import annotations

import datetime as dt
import re
from typing import Optional, Tuple

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.memory.relational.models import JobApplication
from app.memory.relational.repository import create_job_application, update_job_status


from app.core.ai_client import AIClient

class CareerTrackerAgent:
    def __init__(self) -> None:
        self.ai = AIClient()

    async def _send_priority_telegram(self, chat_id: Optional[str], text: str) -> None:
        if not chat_id or not settings.TELEGRAM_BOT_TOKEN:
            return
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={"chat_id": chat_id, "text": text},
                )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to send priority Telegram message: {e}")

    def _find_latest_job_for_company(self, db: Session, user_id: int, company: str) -> Optional[JobApplication]:
        stmt = (
            select(JobApplication)
            .where(JobApplication.user_id == user_id, JobApplication.company.ilike(f"%{company}%"))
            .order_by(JobApplication.last_status_at.desc())
            .limit(1)
        )
        return db.execute(stmt).scalars().first()

    async def run(
        self,
        *,
        db: Session,
        user_id: int,
        message_id: str,
        thread_id: str,
        text: str,
        subject: str,
        from_address: str,
        telegram_chat_id: Optional[str] = None,
    ) -> Optional[dict]:
        """
        - [x] **Memory System Improvements**
          - [x] Implement `ChatHistory` collection in `ChromaClient`
          - [x] Add methods for `add_chat_message` and `query_chat_history`
        - [x] **Execution Agent Upgrade**
          - [x] Refactor `handle_update` to retrieve and include chat history context
          - [x] Improve natural language intent parsing
        - [x] **Career & Proactive Alerts**
          - [x] Update `CareerTrackerAgent` to support direct Telegram alerts for high-priority statuses
          - [x] Ensure `IngestionPipeline` correctly routes status update results to the user
        """
        prompt = (
            "Extract job application details from this email. "
            "Focus only on Company Name, Job Role, and Status (Applied, Interviewing, Rejected, Offer).\n"
            "Return JSON: {\"company\": \"string\", \"role\": \"string\", \"status\": \"string\", \"is_job_related\": bool}.\n\n"
            f"Subject: {subject}\nBody: {text[:2000]}"
        )
        # Use lite model for extraction
        result = await self.ai.generate_json(prompt, model_type="lite")
        if not result or not result.get("is_job_related"):
            return None

        company = result.get("company", "Unknown Company")
        role = result.get("role")
        status = result.get("status", "Applied")

        # 1) New Application
        if result.get("is_new_application") or status == "Applied":
            existing = self._find_latest_job_for_company(db, user_id=user_id, company=company)
            if existing and existing.status == "Applied" and (dt.datetime.now(dt.timezone.utc) - existing.last_status_at).days < 2:
                return {"created": False, "reason": "duplicate"}

            create_job_application(
                db=db,
                user_id=user_id,
                company=company,
                role=role,
                applied_at=dt.datetime.now(dt.timezone.utc),
                source_message_id=message_id,
            )
            return {"created": True, "company": company, "role": role}

        # 2) Status Update
        job = self._find_latest_job_for_company(db, user_id=user_id, company=company)
        if job and job.status != status:
            update_job_status(db=db, job_id=job.id, new_status=status, source_message_id=message_id)
            if status in {"Interview", "Offer"}:
                await self._send_priority_telegram(
                    telegram_chat_id,
                    text=f"🔔 PRIORITY UPDATE: {company} has moved your application for '{role or 'position'}' to '{status.upper()}'! Check your email for more details."
                )
            elif status == "Rejected":
                await self._send_priority_telegram(
                    telegram_chat_id,
                    text=f"Status Update: {company} updated your application for '{role or 'position'}' to 'Rejected'. I've recorded this in your history."
                )
            return {"updated": True, "company": company, "to": status}

        return None

