import re
import json
import logging
import httpx
import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.gmail.client import GmailClient
from app.memory.vector.chroma_client import ChromaClient
from app.memory.relational.repository import record_email_event, record_privacy_flag, upsert_thread
from app.core.dependencies import get_ai_client, get_chroma_client

from app.agents.classifier_agent import ClassifierAgent
from app.agents.career_tracker_agent import CareerTrackerAgent

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
        self.ai = get_ai_client()

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
        max_results: int = 20,
        scan_task_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        from app.memory.relational.repository import (
            update_scan_progress, complete_scan_task, fail_scan_task
        )
        all_messages = gmail_client.list_messages(service=gmail_service, query=query, max_results=max_results)
        
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

        await send_telegram_message(telegram_chat_id, f"📥 Found {total_new} new email(s). Starting Hyper-Efficiency Batch Analysis...")

        processed = 0
        secrets_alerted = 0
        career_updates = 0
        failed = 0
        
        observations = {"spam": [], "newsletter": [], "marketing": []}

        # CHUNK INTO BATCHES OF 2 (Ultra-Conservative for 15k TPM)
        for b_idx in range(0, len(new_messages), 2):
            # Progress Update: Only print ONCE per batch!
            await send_telegram_message(telegram_chat_id, f"⚙️ Batch Analysis: {processed}/{total_new} complete...")

            batch = new_messages[b_idx : b_idx + 2]
            batch_data = []
            
            # 1. Fetch metadata for all in batch
            for m in batch:
                msg_id = m.get("message_id")

                try:
                    gmail_message = gmail_client.get_message(service=gmail_service, message_id=msg_id)
                    batch_data.append({
                        "id": msg_id,
                        "tid": m.get("thread_id") or "",
                        "subject": gmail_message.subject,
                        "from": gmail_message.from_address,
                        "date": gmail_message.date,
                        "body": gmail_message.body_text[:500],  # Compressed snippet for Gemma TPM Limits
                        "full_body": gmail_message.body_text,   # Full body for memory recall
                    })
                except Exception as e:
                    logger.error(f"Failed to fetch message {msg_id}: {e}")
                    failed += 1

            if not batch_data:
                continue

            # 2. Super-Analysis LLM Call (Hyper-Intelligent Mode)
            prompt = (
                "Perform an Ultra-Deep Analysis on the following batch of emails. "
                "Your goal is to extract actionable career data while ensuring zero-leakage of transient secrets.\n\n"
                "For each email, return a JSON object with:\n"
                "1. 'id': The message ID.\n"
                "2. 'secrets': A list of sensitive items (e.g., {'type': 'OTP|Password|RecoveryCode', 'value': '...'}). "
                "Focus ONLY on temporary credentials, NOT login names or tracking IDs.\n"
                "3. 'classification': {\n"
                "     'label': 'Job_Applied|Job_Interview|Job_Offer|Job_Rejection|Newsletter|Marketing|Spam|Personal',\n"
                "     'apply_labels': true,\n"
                "     'add_label_names': ['NextRole/Career' if job-related, else category],\n"
                "     'remove_label_names': []\n"
                "   }\n"
                "4. 'career_info': {\n"
                "     'company': 'Clean Company Name',\n"
                "     'role': 'Job title or 'Position'',\n"
                "     'status': 'Applied|Interview|Offer|Rejected',\n"
                "     'is_job_related': bool\n"
                "   }\n\n"
                "RULES:\n"
                "- If the email is an interview request or scheduling link, set status to 'Interview'.\n"
                "- If it mentions 'not moving forward' or 'other candidates', set status to 'Rejected'.\n"
                "- If it's a multi-job digest from LinkedIn/Indeed, label as 'Newsletter'.\n\n"
                f"Batch Emails (JSON):\n{json.dumps(batch_data, indent=2)}"
            )
            # Use Gemma for the complex batch task (preserves rate limits)
            ai_results = await self.ai.generate_json(prompt, model_type="gemma")
            
            if not ai_results:
                logger.error(f"FATAL: AI returned empty response for batch starting at index {b_idx}. Skipping chunk.")
                failed += len(batch_data)
                continue

            if not isinstance(ai_results, list):
                # Fallback if AI returns single object
                ai_results = [ai_results]

            # 3. Process Batch Results
            result_map = {str(res.get("id")): res for res in ai_results if res.get("id")}

            for item in batch_data:
                msg_id = item["id"]
                thread_id = item["tid"]
                res = result_map.get(msg_id)
                if not res:
                    logger.warning(f"No AI result for {msg_id}, skipping.")
                    continue

                try:
                    # Redaction & Privacy
                    detected_secrets = res.get("secrets", [])
                    full_text = item.get("full_body") or item["body"]
                    redacted_text = full_text
                    if detected_secrets:
                        secrets_alerted += 1
                        for s in detected_secrets:
                            stype = s.get("type", "Secret")
                            val = s.get("value")
                            if val:
                                record_privacy_flag(db, user_id=user_id, gmail_message_id=msg_id, detected_secret_type=stype)
                                redacted_text = redacted_text.replace(val, f"[REDACTED_{stype}]")

                    # Relational Records
                    upsert_thread(db, user_id=user_id, gmail_thread_id=thread_id)
                    record_email_event(db, user_id=user_id, gmail_message_id=msg_id, thread_id=thread_id, event_type="email_ingested")
                    
                    # Search Memory (Chroma)
                    chroma_client.upsert_thread_summary(
                        user_id=user_id, 
                        thread_id=thread_id or msg_id, 
                        summary_text=f"From: {item['from']}\nSubject: {item['subject']}\n{redacted_text}", 
                        message_id=msg_id, 
                        gmail_thread_id=thread_id or None
                    )

                    # Category & Observations
                    classifier = ClassifierAgent()
                    class_res = await classifier.run(
                        text=redacted_text, subject=item["subject"], from_address=item["from"], 
                        message_id=msg_id, thread_id=thread_id, ai_result=res.get("classification")
                    )
                    category = class_res.get("category", "Personal")
                    if category == "Spam":
                        observations["spam"].append(msg_id)
                    elif category == "Newsletter":
                        observations["newsletter"].append(msg_id)
                    elif category == "Marketing":
                        observations["marketing"].append(msg_id)

                    # Career Tracking
                    career = CareerTrackerAgent()
                    tracker_res = await career.run(
                        db=db, user_id=user_id, message_id=msg_id, thread_id=thread_id, 
                        text=redacted_text, subject=item["subject"], from_address=item["from"], 
                        date_str=item["date"], telegram_chat_id=telegram_chat_id, 
                        ai_result=res.get("career_info")
                    )
                    if tracker_res:
                        career_updates += 1

                    processed += 1
                except Exception as e:
                    logger.error(f"Error processing record {msg_id}: {e}")
                    failed += 1

            # Checkpoint Progress after each batch
            if scan_task_id:
                update_scan_progress(db, scan_task_id, processed, batch_data[-1]["id"])

            # Gemma-aware pacing is now handled automatically by AIClient
            pass

        if scan_task_id:
            if failed == 0:
                complete_scan_task(db, scan_task_id)
            else:
                fail_scan_task(db, scan_task_id)

        return {
            "processed": processed,
            "failed": failed,
            "secrets_alerted": secrets_alerted,
            "career_updates": career_updates,
            "observations": observations,
            "status": "success" if failed == 0 else "partial_success"
        }
