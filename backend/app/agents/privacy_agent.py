import re
import json
import logging
import httpx
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.gmail.client import GmailClient
from app.memory.vector.chroma_client import ChromaClient
from app.memory.relational.repository import record_email_event, record_privacy_flag, upsert_thread
from app.core.dependencies import get_ai_client, get_chroma_client

logger = logging.getLogger(__name__)

@dataclass
class DetectedSecret:
    secret_type: str
    matched_value: str


class PrivacyAgent:
    def __init__(self) -> None:
        self.ai = get_ai_client()
        self.OTP_RE = re.compile(r"\b(?:OTP|one[-\s]?time|verification code)\b[^0-9A-Za-z]{0,20}(\d{4,8})\b", re.I)
        self.GENERIC_6_DIGIT_RE = re.compile(r"\b(\d{6})\b")

    async def detect_secrets(self, text: str) -> List[DetectedSecret]:
        found: List[DetectedSecret] = []
        for m in self.OTP_RE.finditer(text):
            found.append(DetectedSecret(secret_type="OTP", matched_value=m.group(1)))
        for m in self.GENERIC_6_DIGIT_RE.finditer(text):
            found.append(DetectedSecret(secret_type="OTP", matched_value=m.group(1)))

        text_for_llm = self.redact_text(text, found)
        prompt = (
            "Analyze the following email and identify any highly sensitive transient secrets "
            "like passwords or verification phrases. "
            "Return a JSON list: [{\"secret_type\": \"Password|VerificationCode\", \"matched_value\": \"...\"}]. "
            "Important: Do not include IDs, tracking numbers, or public info.\n\n"
            f"Email Content:\n{text_for_llm}"
        )
        llm_results = await self.ai.generate_json(prompt, model_type="gemma")
        if isinstance(llm_results, list):
            for item in llm_results:
                if "secret_type" in item and "matched_value" in item:
                    found.append(DetectedSecret(secret_type=item["secret_type"], matched_value=str(item["matched_value"])))

        uniq: Dict[Tuple[str, str], DetectedSecret] = {}
        for d in found:
            uniq[(d.secret_type, d.matched_value)] = d
        return list(uniq.values())

    def redact_text(self, text: str, detected: List[DetectedSecret]) -> str:
        redacted = text
        for d in detected:
            if not d.matched_value:
                continue
            token = re.escape(d.matched_value)
            redacted = re.sub(token, f"[REDACTED_{d.secret_type}]", redacted)
        return redacted


async def send_telegram_message(chat_id: str, text: str) -> None:
    if not settings.TELEGRAM_BOT_TOKEN or not chat_id:
        return
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text},
        )


def summarize_email_for_vector(subject: str, from_address: str, date: str, body_text: str, *, max_chars: int = 2000) -> str:
    body_snip = body_text[:max_chars]
    return f"From: {from_address}\nSubject: {subject}\nDate: {date}\nBody:\n{body_snip}"


class IngestionPipeline:
    def __init__(self, *, privacy_agent: Optional[PrivacyAgent] = None) -> None:
        self.privacy_agent = privacy_agent or PrivacyAgent()

    async def run_for_account(
        self,
        *,
        db: Session,
        user_id: int,
        telegram_chat_id: str,
        gmail_account_id: int,
        gmail_service,
        gmail_client: GmailClient,
        chroma_client: ChromaClient,
        query: str,
    ) -> Dict[str, Any]:
        all_messages = gmail_client.list_messages(service=gmail_service, query=query, max_results=20)
        
        # Pre-filter duplicates to get an accurate count of NEW work
        from app.memory.relational.models import EmailEvent
        new_messages = []
        for m in all_messages:
            msg_id = m.get("message_id")
            if not msg_id:
                logger.warning("Found message dict missing 'message_id' in list response.")
                continue
            exists = db.execute(select(EmailEvent).where(EmailEvent.gmail_message_id == msg_id)).scalars().first()
            if not exists:
                new_messages.append(m)

        total_new = len(new_messages)
        if total_new == 0:
            return {"processed": 0, "secrets_alerted": 0, "status": "up_to_date"}

        await send_telegram_message(telegram_chat_id, f"📥 Found {total_new} new email(s). Starting analysis and memory linking...")

        processed = 0
        secrets_alerted = 0
        career_updates = 0
        failed = 0

        for i, m in enumerate(new_messages):
            try:
                message_id = m.get("message_id")
                if not message_id:
                    logger.warning("Skipping message with no ID in ingestion loop.")
                    continue
                    
                thread_id = m.get("thread_id") or ""
                
                # Progress Heartbeat (Every 3 emails to show movement)
                if (i + 1) % 3 == 0 or (i + 1) == total_new:
                    await send_telegram_message(telegram_chat_id, f"⚙️ Processing... ({i+1}/{total_new} complete)")

                gmail_message = gmail_client.get_message(service=gmail_service, message_id=message_id)
                logger.info(f"Ingesting Email: {gmail_message.subject[:50]}...")

                raw_text = summarize_email_for_vector(gmail_message.subject, gmail_message.from_address, gmail_message.date, gmail_message.body_text)

                detected = await self.privacy_agent.detect_secrets(raw_text)
                if detected:
                    secrets_alerted += 1
                    for d in detected:
                        record_privacy_flag(db, user_id=user_id, gmail_message_id=message_id, detected_secret_type=d.secret_type)
                    redacted_text = self.privacy_agent.redact_text(raw_text, detected)
                else:
                    redacted_text = raw_text

                upsert_thread(db, user_id=user_id, gmail_thread_id=thread_id)
                record_email_event(db, user_id=user_id, gmail_message_id=message_id, thread_id=thread_id, event_type="email_ingested")
                chroma_client.upsert_thread_summary(user_id=user_id, thread_id=thread_id or message_id, summary_text=redacted_text, message_id=message_id, gmail_thread_id=thread_id or None)

                # Classify
                try:
                    from app.agents.classifier_agent import ClassifierAgent
                    classifier = ClassifierAgent()
                    await classifier.run(text=redacted_text, subject=gmail_message.subject, from_address=gmail_message.from_address, message_id=message_id, thread_id=thread_id)
                except Exception as e:
                    logger.error(f"Classifier Error: {e}")

                # Career Track
                try:
                    from app.agents.career_tracker_agent import CareerTrackerAgent
                    career = CareerTrackerAgent()
                    tracker_res = await career.run(db=db, user_id=user_id, message_id=message_id, thread_id=thread_id, text=redacted_text, subject=gmail_message.subject, from_address=gmail_message.from_address, telegram_chat_id=telegram_chat_id)
                    if tracker_res:
                        career_updates += 1
                except Exception as e:
                    logger.error(f"Career Tracker Error: {e}")

                processed += 1
            except Exception as e:
                failed += 1
                logger.error(f"Failed to process email {m.get('message_id')}: {e}")
                continue

        return {
            "processed": processed,
            "failed": failed,
            "secrets_alerted": secrets_alerted,
            "career_updates": career_updates,
            "status": "success" if failed == 0 else "partial_success"
        }
