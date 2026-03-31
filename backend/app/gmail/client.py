from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

from cryptography.fernet import Fernet
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from app.core.config import settings


def _get_fernet() -> Optional[Fernet]:
    if not settings.ENCRYPTION_KEY:
        return None
    return Fernet(settings.ENCRYPTION_KEY.encode("utf-8"))


def encrypt_secret(secret: str) -> str:
    f = _get_fernet()
    if not f:
        # MVP fallback: no encryption configured.
        return secret
    return f.encrypt(secret.encode("utf-8")).decode("utf-8")


def decrypt_secret(secret: str) -> str:
    f = _get_fernet()
    if not f:
        return secret
    return f.decrypt(secret.encode("utf-8")).decode("utf-8")


GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
]


@dataclass
class GmailMessage:
    message_id: str
    thread_id: Optional[str]
    from_address: str
    to_addresses: List[str]
    subject: str
    date: str
    body_text: str


class GmailClient:
    def __init__(self) -> None:
        self.client_config = {
            "web": {
                "client_id": settings.GMAIL_OAUTH_CLIENT_ID,
                "client_secret": settings.GMAIL_OAUTH_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [settings.GMAIL_OAUTH_REDIRECT_URL],
            }
        }

    def build_authorization_url(self, *, state: str, scopes: Optional[List[str]] = None) -> str:
        from urllib.parse import urlencode
        scopes = scopes or GMAIL_SCOPES
        params = {
            "response_type": "code",
            "client_id": settings.GMAIL_OAUTH_CLIENT_ID,
            "redirect_uri": settings.GMAIL_OAUTH_REDIRECT_URL,
            "scope": " ".join(scopes),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    def exchange_code_for_tokens(self, *, code: str) -> Tuple[str, str]:
        # Returns: (refresh_token, access_token)
        # Using a manual request to avoid PKCE 'code_verifier' issues in stateless Flow re-creation
        import requests
        data = {
            "code": code,
            "client_id": settings.GMAIL_OAUTH_CLIENT_ID,
            "client_secret": settings.GMAIL_OAUTH_CLIENT_SECRET,
            "redirect_uri": settings.GMAIL_OAUTH_REDIRECT_URL,
            "grant_type": "authorization_code",
        }
        res = requests.post("https://oauth2.googleapis.com/token", data=data)
        res_data = res.json()
        
        if "error" in res_data:
            raise ValueError(f"Google OAuth Error: {res_data.get('error_description', res_data['error'])}")
            
        refresh_token = res_data.get("refresh_token")
        access_token = res_data.get("access_token")
        
        if not refresh_token:
            raise ValueError("No refresh token returned by Google. Ensure 'prompt=consent' was used.")
            
        return refresh_token, access_token

    def build_service_from_refresh_token(self, *, refresh_token_encrypted: str):
        refresh_token = decrypt_secret(refresh_token_encrypted)
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GMAIL_OAUTH_CLIENT_ID,
            client_secret=settings.GMAIL_OAUTH_CLIENT_SECRET,
            scopes=GMAIL_SCOPES,
        )
        creds.refresh(Request())
        return build("gmail", "v1", credentials=creds)

    def list_messages(self, *, service, query: str, max_results: int = 50) -> List[Dict[str, str]]:
        result = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )
        messages = result.get("messages", []) or []
        # list() doesn't include threadId. Fetch metadata per message.
        out: List[Dict[str, str]] = []
        for m in messages:
            mid = m.get("id")
            if not mid:
                continue
            try:
                meta = (
                    service.users()
                    .messages()
                    .get(userId="me", id=mid, format="metadata", metadataHeaders=["Thread-Id", "From", "To", "Subject", "Date"])
                    .execute()
                )
                headers = {h["name"].lower(): h.get("value", "") for h in meta.get("payload", {}).get("headers", [])}
                out.append(
                    {
                        "message_id": mid,
                        "thread_id": meta.get("threadId") or headers.get("thread-id") or "",
                    }
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Failed to fetch metadata for message {mid}: {e}")
                continue
        return out

    def get_message(self, *, service, message_id: str) -> GmailMessage:
        msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()
        payload = msg.get("payload", {}) or {}
        headers = {h["name"].lower(): h.get("value", "") for h in payload.get("headers", [])}

        body_text = self._extract_body_text(payload)

        return GmailMessage(
            message_id=message_id,
            thread_id=msg.get("threadId"),
            from_address=headers.get("from", ""),
            to_addresses=[x.strip() for x in headers.get("to", "").split(",") if x.strip()],
            subject=headers.get("subject", ""),
            date=headers.get("date", ""),
            body_text=body_text,
        )

    def _extract_body_text(self, payload: Dict[str, Any]) -> str:
        # Gmail base64url encodes body parts.
        body = payload.get("body") or {}
        data = body.get("data")
        if data:
            return base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="replace")

        # Otherwise, recursively walk parts.
        parts = payload.get("parts") or []
        for part in parts:
            part_body = part.get("body") or {}
            part_data = part_body.get("data")
            if part_data:
                return base64.urlsafe_b64decode(part_data.encode("utf-8")).decode("utf-8", errors="replace")
            part_parts = part.get("parts") or []
            if part_parts:
                nested = self._extract_body_text(part)
                if nested:
                    return nested
        return ""

    def modify_labels(
        self,
        *,
        service,
        message_id: str,
        add_label_ids: Optional[List[str]] = None,
        remove_label_ids: Optional[List[str]] = None,
    ) -> None:
        body: Dict[str, Any] = {}
        if add_label_ids:
            body["addLabelIds"] = add_label_ids
        if remove_label_ids:
            body["removeLabelIds"] = remove_label_ids
        service.users().messages().modify(userId="me", id=message_id, body=body).execute()

    def batch_modify_labels(
        self,
        *,
        service,
        message_ids: List[str],
        add_label_ids: Optional[List[str]] = None,
        remove_label_ids: Optional[List[str]] = None,
    ) -> None:
        if not message_ids:
            return
        body: Dict[str, Any] = {"ids": message_ids}
        if add_label_ids:
            body["addLabelIds"] = add_label_ids
        if remove_label_ids:
            body["removeLabelIds"] = remove_label_ids
        service.users().messages().batchModify(userId="me", body=body).execute()

    def trash_message(self, *, service, message_id: str) -> None:
        self.modify_labels(service=service, message_id=message_id, add_label_ids=["TRASH"], remove_label_ids=["INBOX"])

    def archive_message(self, *, service, message_id: str) -> None:
        self.modify_labels(service=service, message_id=message_id, remove_label_ids=["INBOX"])

    def get_profile_email(self, *, service) -> str:
        profile = service.users().getProfile(userId="me").execute()
        return str(profile.get("emailAddress", ""))

    def ensure_label(self, *, service, label_name: str) -> str:
        labels = service.users().labels().list(userId="me").execute().get("labels", []) or []
        for l in labels:
            if l.get("name") == label_name:
                return l["id"]

        created = (
            service.users()
            .labels()
            .create(
                userId="me",
                body={
                    "name": label_name,
                    "labelListVisibility": "labelShow",
                    "messageListVisibility": "show",
                },
            )
            .execute()
        )
        return created["id"]

