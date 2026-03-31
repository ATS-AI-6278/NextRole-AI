from __future__ import annotations

import datetime as dt
from typing import Dict, List, Optional

import httpx
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import func, select

from app.core.config import settings
from app.core.db import SessionLocal
from app.memory.relational.models import JobApplication, User


def _send_telegram(chat_id: str, text: str) -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        return
    try:
        httpx.post(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
    except Exception:
        # MVP: swallow errors so scheduler doesn't crash.
        pass


from app.core.ai_client import AIClient

async def _format_digest(*, briefing_label: str, offer_count: int, interview_count: int, new_applications: int) -> str:
    ai = AIClient()
    prompt = (
        f"You are the Reporting Agent for NextRole AI. Generate a professional and encouraging "
        f"summary for the user's {briefing_label}.\n\n"
        f"Current Data (last 12 hours):\n"
        f"- Priority: {offer_count} Offer Letter(s), {interview_count} Interview Invite(s).\n"
        f"- System Stats: {new_applications} new application(s) logged.\n"
        f"- Clutter: 25+ marketing emails auto-archived (estimated).\n\n"
        "Use emojis, bold headings, and a clean structure optimized for Telegram. "
        "Highlight priority actions at the top. If there are no updates, keep it brief and motivating."
    )
    return await ai.generate_text(prompt)


def _get_counts_for_user(db, *, hours_back: int) -> Dict[str, int]:
    now = dt.datetime.now(dt.timezone.utc)
    since = now - dt.timedelta(hours=hours_back)
    # MVP: approximate counts using last_status_at timestamps.
    offer_count = db.execute(
        select(func.count(JobApplication.id)).where(JobApplication.status == "Offer", JobApplication.last_status_at >= since)
    ).scalar_one()

    interview_count = db.execute(
        select(func.count(JobApplication.id)).where(JobApplication.status == "Interview", JobApplication.last_status_at >= since)
    ).scalar_one()

    new_apps = db.execute(
        select(func.count(JobApplication.id)).where(JobApplication.status == "Applied", JobApplication.last_status_at >= since)
    ).scalar_one()

    return {
        "offer_count": int(offer_count),
        "interview_count": int(interview_count),
        "new_applications": int(new_apps),
    }


async def send_digests_once(*, briefing: str) -> None:
    db = SessionLocal()
    try:
        users = db.execute(select(User)).scalars().all()
        for u in users:
            counts = _get_counts_for_user(db, hours_back=12)
            text = await _format_digest(
                briefing_label=briefing,
                offer_count=counts["offer_count"],
                interview_count=counts["interview_count"],
                new_applications=counts["new_applications"],
            )
            _send_telegram(u.telegram_chat_id, text)
    finally:
        db.close()


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")

    morning_hour = int(getattr(settings, "DIGEST_MORNING_HOUR", 8))
    evening_hour = int(getattr(settings, "DIGEST_EVENING_HOUR", 17))
    night_hour = int(getattr(settings, "DIGEST_NIGHT_HOUR", 21))

    scheduler.add_job(
        send_digests_once,
        trigger=CronTrigger(hour=morning_hour, minute=0),
        id="digest_morning",
        kwargs={"briefing": "Morning Briefing"},
        replace_existing=True,
    )
    scheduler.add_job(
        send_digests_once,
        trigger=CronTrigger(hour=evening_hour, minute=0),
        id="digest_evening",
        kwargs={"briefing": "Evening Briefing"},
        replace_existing=True,
    )
    scheduler.add_job(
        send_digests_once,
        trigger=CronTrigger(hour=night_hour, minute=0),
        id="digest_night",
        kwargs={"briefing": "Night Briefing"},
        replace_existing=True,
    )

    scheduler.start()
    return scheduler
