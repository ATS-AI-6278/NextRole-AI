from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.agents.execution_agent import ExecutionAgent
from app.core.config import settings
from app.core.db import get_db

router = APIRouter()


@router.post("/telegram/webhook")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    # Telegram can send a secret token header when you set `secret_token` during webhook setup.
    if settings.TELEGRAM_WEBHOOK_SECRET:
        header_value = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if header_value != settings.TELEGRAM_WEBHOOK_SECRET:
            raise HTTPException(status_code=403, detail="Invalid Telegram webhook secret token")

    update = await request.json()
    agent = ExecutionAgent()
    await agent.handle_update(update=update, db=db)
    return {"ok": True}

