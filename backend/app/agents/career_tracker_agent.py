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

    def _send_priority_telegram(self, chat_id: Optional[str], text: str) -> None:
        if not chat_id or not settings.TELEGRAM_BOT_TOKEN:
            return
        try:
            import httpx
            httpx.post(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": text},
                timeout=10,
            )
        except Exception:
            pass

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
        Use LLM to extract job details and update the database.
        """
        combined = f"Subject: {subject}\nFrom: {from_address}\n\n{text}".strip()

        prompt = (
            "You are a Career Tracking AI for NextRole AI. Analyze the following email regarding job applications.\n"
            "Identify if this is a 'New Application' confirmation or a 'Status Update' (Interview, Rejected, Offer).\n\n"
            "Rules:\n"
            "1. Extract 'company' name precisely.\n"
            "2. Extract 'role' (job title) if present.\n"
            "3. Determine 'status': one of [Applied, Interview, Rejected, Offer].\n"
            "4. Return JSON: {\"is_job_related\": bool, \"is_new_application\": bool, \"company\": \"...\", \"role\": \"...\", \"status\": \"...\"}.\n\n"
            f"Email Content:\n{combined}"
        )

        result = await self.ai.generate_json(prompt)
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
                self._send_priority_telegram(
                    telegram_chat_id,
                    text=f"🚀 Priority Update: {company} changed status to {status}!"
                )
            return {"updated": True, "company": company, "to": status}

        return None

