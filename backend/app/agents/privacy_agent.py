from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.gmail.client import GmailClient
from app.memory.relational.models import EmailEvent, PrivacyFlag
from app.memory.relational.repository import record_email_event, record_privacy_flag, upsert_thread
from app.memory.vector.chroma_client import ChromaClient


from app.core.ai_client import AIClient

@dataclass
class DetectedSecret:
    secret_type: str
    matched_value: str


class PrivacyAgent:
    """
    Detect sensitive secrets (OTP/password/verification codes) and redact them before:
    - logging
    - saving structured memory
    - saving embeddings (vector memory)
    """

    def __init__(self) -> None:
        self.ai = AIClient()
        # Keep patterns simple for fast preliminary pass.
        self.OTP_RE = re.compile(r"\b(?:OTP|one[-\s]?time|verification code)\b[^0-9A-Za-z]{0,20}(\d{4,8})\b", re.I)
        self.GENERIC_6_DIGIT_RE = re.compile(r"\b(\d{6})\b")

    async def detect_secrets(self, text: str) -> List[DetectedSecret]:
        found: List[DetectedSecret] = []

        # 1. Fast Regex Pass (Heuristic)
        for m in self.OTP_RE.finditer(text):
            found.append(DetectedSecret(secret_type="OTP", matched_value=m.group(1)))
        
        for m in self.GENERIC_6_DIGIT_RE.finditer(text):
            found.append(DetectedSecret(secret_type="OTP", matched_value=m.group(1)))

        # 2. LLM Pass (Contextual)
        prompt = (
            "Analyze the following email and identify any highly sensitive transient secrets "
            "like OTPs, temporary passwords, or verification codes. "
            "Return a JSON list of objects: [{\"secret_type\": \"OTP|Password|VerificationCode\", \"matched_value\": \"...\"}]. "
            "Important: Do not include IDs, tracking numbers, or public info.\n\n"
            f"Email Content:\n{text}"
        )
        
        llm_results = await self.ai.generate_json(prompt)
        if isinstance(llm_results, list):
            for item in llm_results:
                if "secret_type" in item and "matched_value" in item:
                    found.append(DetectedSecret(secret_type=item["secret_type"], matched_value=str(item["matched_value"])))

        # De-dup by (type,value)
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
    if not settings.TELEGRAM_BOT_TOKEN:
        # In dev without credentials, we just no-op.
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
        """
        MVP ingestion:
        - Pull messages matching `query`
        - Detect+redact secrets
        - Store privacy flags (types only) and vector/relational memory using redacted content
        - Optionally invoke downstream agents (classifier/career) if present
        """

        messages = gmail_client.list_messages(service=gmail_service, query=query, max_results=50)
        processed = 0
        secrets_alerted = 0

        for m in messages:
            message_id = m["message_id"]
            thread_id = m.get("thread_id") or ""
            gmail_message = gmail_client.get_message(service=gmail_service, message_id=message_id)

            raw_text = summarize_email_for_vector(
                gmail_message.subject,
                gmail_message.from_address,
                gmail_message.date,
                gmail_message.body_text,
            )

            detected = await self.privacy_agent.detect_secrets(raw_text)
            if detected:
                secrets_alerted += 1
                # Record type-only flags (no secret values).
                for d in detected:
                    record_privacy_flag(db, user_id=user_id, gmail_message_id=message_id, detected_secret_type=d.secret_type)

                # Alert user immediately; do not include full values.
                types = sorted({d.secret_type for d in detected})
                await send_telegram_message(
                    chat_id=telegram_chat_id,
                    text=f"Sensitive info detected in Gmail email. Types: {', '.join(types)}. I redacted it and will not store it.",
                )
                redacted_text = self.privacy_agent.redact_text(raw_text, detected)
            else:
                redacted_text = raw_text

            # Thread upsert for later linkage.
            upsert_thread(db, user_id=user_id, gmail_thread_id=thread_id, labels_applied=None)

            # Relational memory: store an ingestion event with extracted entities later.
            record_email_event(
                db,
                user_id=user_id,
                gmail_message_id=message_id,
                thread_id=thread_id,
                event_type="email_ingested",
                extracted_entities=None,
            )

            # Vector memory: store redacted summary (privacy-forward).
            chroma_client.upsert_thread_summary(
                user_id=user_id,
                thread_id=thread_id or message_id,
                summary_text=redacted_text,
                message_id=message_id,
                gmail_thread_id=thread_id or None,
            )

            processed += 1

            # Downstream: run if/when the modules exist.
            try:
                from app.agents.classifier_agent import ClassifierAgent  # type: ignore
                classifier = ClassifierAgent()
                classifier_result = await classifier.run(
                    text=redacted_text,
                    subject=gmail_message.subject,
                    from_address=gmail_message.from_address,
                    message_id=message_id,
                    thread_id=thread_id,
                )
                if classifier_result.get("apply_labels"):
                    classifier.apply_labels(
                        service=gmail_service,
                        gmail_client=gmail_client,
                        message_id=message_id,
                        add_label_names=classifier_result.get("add_label_names") or [],
                        remove_label_names=classifier_result.get("remove_label_names") or [],
                    )
            except Exception as e:
                # MVP: do not fail ingestion if classifier isn't implemented or errors.
                logger.error(f"Classifier Error: {e}")

            try:
                from app.agents.career_tracker_agent import CareerTrackerAgent  # type: ignore
                career = CareerTrackerAgent()
                await career.run(
                    db=db,
                    user_id=user_id,
                    message_id=message_id,
                    thread_id=thread_id,
                    text=redacted_text,
                    subject=gmail_message.subject,
                    from_address=gmail_message.from_address,
                    telegram_chat_id=telegram_chat_id,
                )
            except Exception as e:
                logger.error(f"Career Tracker Error: {e}")

        return {"processed": processed, "secrets_alerted": secrets_alerted}

