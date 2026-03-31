from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.gmail.client import GmailClient, encrypt_secret
from app.memory.relational.repository import get_or_create_gmail_account, get_or_create_user_by_chat_id, list_job_applications
from app.memory.relational.models import GmailAccount, User
from app.agents.privacy_agent import IngestionPipeline
from app.memory.vector.chroma_client import ChromaClient
from app.scheduler.digests import send_digests_once
from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health():
    return {"ok": True}


from fastapi.responses import HTMLResponse, RedirectResponse

@router.get("/gmail/oauth/start")
def gmail_oauth_start(chat_id: str = Query(...), state: str = Query("", alias="state")):
    """
    Redirects the user to the Google OAuth URL.
    """
    gmail_client = GmailClient()
    oauth_state = state or chat_id
    auth_url = gmail_client.build_authorization_url(state=oauth_state)
    return RedirectResponse(url=auth_url)


@router.get("/gmail/oauth/callback")
def gmail_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    gmail_client = GmailClient()
    user = get_or_create_user_by_chat_id(db, state)

    refresh_token, _access_token = gmail_client.exchange_code_for_tokens(code=code)
    gmail_service = gmail_client.build_service_from_refresh_token(refresh_token_encrypted=encrypt_secret(refresh_token))
    email_address = gmail_client.get_profile_email(service=gmail_service) or "unknown@example.com"

    get_or_create_gmail_account(
        db,
        user_id=user.id,
        email_address=email_address,
        oauth_refresh_token_encrypted=encrypt_secret(refresh_token),
    )
    return HTMLResponse(content="""
        <h1>Success!</h1>
        <p>Your Gmail account has been successfully connected to NextRole AI.</p>
        <p>You can now close this window and return to your Telegram bot.</p>
    """)


@router.get("/dashboard/applications")
def dashboard_applications(
    x_telegram_chat_id: str = Header(...),
    db: Session = Depends(get_db),
):
    """
    MVP dashboard endpoint:
    - identifies user by Telegram `chat_id` header
    - returns job applications with latest status
    """
    user = get_or_create_user_by_chat_id(db, x_telegram_chat_id)
    jobs = list_job_applications(db, user.id)
    return [
        {
            "id": j.id,
            "company": j.company,
            "role": j.role,
            "applied_at": j.applied_at.isoformat() if j.applied_at else None,
            "status": j.status,
            "last_status_at": j.last_status_at.isoformat() if j.last_status_at else None,
        }
        for j in jobs
    ]


class DevIngestRequest(BaseModel):
    query: str = "newer_than:1d"
    chat_id: Optional[str] = None


@router.post("/dev/ingest")
async def dev_ingest(
    req: DevIngestRequest,
    db: Session = Depends(get_db),
):
    """
    Dev-only endpoint to run ingestion manually (useful for testing the pipeline).
    - Ingests Gmail messages matching `query`
    - Sends secret alerts immediately to Telegram
    - Stores structured + vector memory after redaction
    """
    if settings.ENVIRONMENT != "dev":
        raise HTTPException(status_code=403, detail="Forbidden")

    pipeline = IngestionPipeline()
    gmail_client = GmailClient()
    chroma_client = ChromaClient()

    users: list[User]
    if req.chat_id:
        users = [get_or_create_user_by_chat_id(db, req.chat_id)]
    else:
        users = list(db.execute(select(User)).scalars().all())

    total_processed = 0
    total_secret_alerts = 0

    for u in users:
        accounts = list(db.execute(select(GmailAccount).where(GmailAccount.user_id == u.id)).scalars().all())
        for acc in accounts:
            service = gmail_client.build_service_from_refresh_token(refresh_token_encrypted=acc.oauth_refresh_token_encrypted)
            result = await pipeline.run_for_account(
                db=db,
                user_id=u.id,
                telegram_chat_id=u.telegram_chat_id,
                gmail_account_id=acc.id,
                gmail_service=service,
                gmail_client=gmail_client,
                chroma_client=chroma_client,
                query=req.query,
            )
            total_processed += int(result.get("processed") or 0)
            total_secret_alerts += int(result.get("secrets_alerted") or 0)

    return {
        "ok": True,
        "processed": total_processed,
        "secrets_alerted": total_secret_alerts,
    }


class DevDigestRequest(BaseModel):
    briefing: str = "Dev Digest"


@router.post("/dev/digest")
def dev_digest(req: DevDigestRequest):
    """
    Dev-only endpoint to send a digest immediately.
    """
    if settings.ENVIRONMENT != "dev":
        raise HTTPException(status_code=403, detail="Forbidden")

    send_digests_once(briefing=req.briefing)
    return {"ok": True, "sent": True, "briefing": req.briefing}

