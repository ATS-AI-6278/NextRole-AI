import datetime as dt
import email.utils
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

    def _parse_email_date(self, date_str: str) -> dt.datetime:
        try:
            if not date_str:
                return dt.datetime.now(dt.timezone.utc)
            return email.utils.parsedate_to_datetime(date_str)
        except Exception:
            return dt.datetime.now(dt.timezone.utc)

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

    def _find_job_by_thread(self, db: Session, user_id: int, thread_id: str) -> Optional[JobApplication]:
        if not thread_id:
            return None
        stmt = select(JobApplication).where(JobApplication.user_id == user_id, JobApplication.gmail_thread_id == thread_id)
        return db.execute(stmt).scalars().first()

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
        date_str: str,
        telegram_chat_id: Optional[str] = None,
        ai_result: Optional[dict] = None,
    ) -> Optional[dict]:
        if ai_result:
            result = ai_result
        else:
            prompt = (
                "Extract job application details from this email. "
                "Focus only on Company Name, Job Role, and Status (Applied, Interview, Rejected, Offer).\n"
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
        msg_date = self._parse_email_date(date_str)

        # Priority 1: Match by Thread ID
        job = self._find_job_by_thread(db, user_id=user_id, thread_id=thread_id)
        
        # Priority 2: If no thread match, fall back to Company Name (for initial applications or missing thread data)
        if not job:
            job = self._find_latest_job_for_company(db, user_id=user_id, company=company)

        # 1) New Application (If no job found, create it)
        if not job:
            create_job_application(
                db=db,
                user_id=user_id,
                company=company,
                role=role,
                applied_at=msg_date,
                source_message_id=message_id,
                gmail_thread_id=thread_id,
            )
            return {"created": True, "company": company, "role": role}

        # 2) Status Update (If job exists and status changed)
        if job.status != status:
            update_job_status(db=db, job_id=job.id, new_status=status, source_message_id=message_id, last_status_at=msg_date)
            # Link thread ID if it was missing
            if not job.gmail_thread_id and thread_id:
                job.gmail_thread_id = thread_id
                db.add(job)
                db.commit()

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

