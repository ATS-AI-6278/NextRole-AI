from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from app.gmail.client import GmailClient


from app.core.ai_client import AIClient

@dataclass
class ClassifierResult:
    category: str
    add_label_names: List[str]
    remove_label_names: List[str]
    apply_labels: bool = True


class ClassifierAgent:
    CATEGORY_LABELS = {
        "Newsletter": "Newsletter",
        "Job_Applied": "Job_Applied",
        "Job_Offer": "Job_Offer",
        "Spam": "Spam",
        "Personal": "Personal",
    }

    def __init__(self) -> None:
        self.ai = AIClient()

    async def run(
        self,
        *,
        text: str,
        subject: str,
        from_address: str,
        message_id: str,
        thread_id: str,
    ) -> dict:
        """
        Use LLM to categorize the email.
        Returns a structure the caller can use to apply Gmail labels.
        """
        combined = f"Subject: {subject}\nFrom: {from_address}\n\n{text}".strip()
        category = await self.classify(combined)

        add_label = self.CATEGORY_LABELS.get(category, "Personal")
        
        return {
            "category": category,
            "apply_labels": True,
            "add_label_names": [add_label],
            "remove_label_names": [],
        }

    async def classify(self, text: str) -> str:
        prompt = (
            "You are an Email Classifier AI for NextRole AI. Categorize the following email into "
            "one of these types: [Job_Applied, Job_Offer, Newsletter, Spam, Personal].\n"
            "- Job_Applied: Application confirmation emails.\n"
            "- Job_Offer: Interview invitations or job offers.\n"
            "- Newsletter: Marketing emails, weekly digests, or promotional content.\n"
            "- Spam: Fraud, scams, or obvious junk.\n"
            "- Personal: Direct correspondence or personal matters.\n\n"
            "Return JSON: {\"category\": \"...\", \"reason\": \"...\"}.\n\n"
            f"Email Content:\n{text}"
        )
        
        result = await self.ai.generate_json(prompt)
        return result.get("category", "Personal")

    def apply_labels(
        self,
        *,
        service,
        gmail_client: GmailClient,
        message_id: str,
        add_label_names: List[str],
        remove_label_names: Optional[List[str]] = None,
    ) -> None:
        remove_label_names = remove_label_names or []

        add_ids: List[str] = []
        for name in add_label_names:
            if name:
                add_ids.append(gmail_client.ensure_label(service=service, label_name=name))

        remove_ids: List[str] = []
        for name in remove_label_names:
            if name:
                remove_ids.append(gmail_client.ensure_label(service=service, label_name=name))

        gmail_client.modify_labels(
            service=service,
            message_id=message_id,
            add_label_ids=add_ids or None,
            remove_label_ids=remove_ids or None,
        )

