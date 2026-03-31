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
        ai_result: Optional[dict] = None,
    ) -> dict:
        if ai_result:
            result = ai_result
        else:
            prompt = (
                "Categorize this email into exactly one of these labels: 'Job Application', 'Newsletter', 'Marketing', 'Spam', 'Personal'.\n"
                "Also decide if we should archive it (Newsletter/Marketing) or move to trash (Spam).\n"
                "Return JSON: {\"label\": \"string\", \"apply_labels\": bool, \"add_label_names\": [\"string\"], \"remove_label_names\": [\"string\"]}.\n\n"
                f"Subject: {subject}\nFrom: {from_address}\nBody: {text[:1000]}"
            )
            # Use gemma for fast classification
            result = await self.ai.generate_json(prompt, model_type="gemma")
        
        # Ensure 'label' maps to CATEGORY_LABELS or default
        label = result.get("label", "Personal")
        add_labels = result.get("add_label_names", [])
        if not add_labels and label in self.CATEGORY_LABELS:
            add_labels = [self.CATEGORY_LABELS[label]]

        return {
            "category": label,
            "apply_labels": result.get("apply_labels", True),
            "add_label_names": add_labels,
            "remove_label_names": result.get("remove_label_names", []),
        }

    async def classify(self, text: str) -> str:
        # Legacy method if still called elsewhere
        prompt = (
            "Categorize the following email into one of these types: [Job_Applied, Job_Offer, Newsletter, Spam, Personal].\n\n"
            f"Email Content:\n{text}"
        )
        result = await self.ai.generate_json(prompt, model_type="gemma")
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

