import datetime as dt
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import delete, select, update

from app.memory.relational.models import EmailEvent, GmailAccount, JobApplication, PendingAction, PrivacyFlag, ScanTask, Thread, User


def init_db(engine) -> None:
    # MVP: create tables directly (no migrations yet).
    from app.core.db import Base

    Base.metadata.create_all(bind=engine)


def get_or_create_user_by_chat_id(db: Session, telegram_chat_id: str) -> User:
    stmt = select(User).where(User.telegram_chat_id == telegram_chat_id)
    user = db.execute(stmt).scalars().first()
    if user:
        return user

    user = User(telegram_chat_id=telegram_chat_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_gmail_account(db: Session, user_id: int, email_address: str, oauth_refresh_token_encrypted: str) -> GmailAccount:
    stmt = select(GmailAccount).where(GmailAccount.user_id == user_id, GmailAccount.email_address == email_address)
    account = db.execute(stmt).scalars().first()
    if account:
        return account

    account = GmailAccount(
        user_id=user_id,
        email_address=email_address,
        oauth_refresh_token_encrypted=oauth_refresh_token_encrypted,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def upsert_thread(db: Session, user_id: int, gmail_thread_id: str, labels_applied: Optional[Dict[str, Any]] = None) -> Thread:
    stmt = select(Thread).where(Thread.user_id == user_id, Thread.gmail_thread_id == gmail_thread_id)
    thread = db.execute(stmt).scalars().first()
    if thread:
        if labels_applied is not None:
            thread.labels_applied = labels_applied
            db.add(thread)
            db.commit()
        return thread

    thread = Thread(user_id=user_id, gmail_thread_id=gmail_thread_id, labels_applied=labels_applied)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread


def create_job_application(
    db: Session,
    user_id: int,
    company: str,
    role: Optional[str],
    applied_at: Optional[dt.datetime] = None,
    source_message_id: Optional[str] = None,
    gmail_thread_id: Optional[str] = None,
) -> JobApplication:
    job = JobApplication(
        user_id=user_id,
        company=company,
        role=role,
        applied_at=applied_at or dt.datetime.now(dt.timezone.utc),
        status="Applied",
        last_status_at=applied_at or dt.datetime.now(dt.timezone.utc),
        source_message_id=source_message_id,
        gmail_thread_id=gmail_thread_id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def list_job_applications(db: Session, user_id: int, limit: int = 200) -> List[JobApplication]:
    stmt = (
        select(JobApplication)
        .where(JobApplication.user_id == user_id)
        .order_by(JobApplication.last_status_at.desc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def update_job_status(db: Session, job_id: int, new_status: str, *, source_message_id: Optional[str] = None, last_status_at: Optional[dt.datetime] = None) -> JobApplication:
    job = db.execute(select(JobApplication).where(JobApplication.id == job_id)).scalars().first()
    # If not found, create logic can be added later; for now we fail clearly.
    if job is None:
        raise ValueError(f"JobApplication not found: {job_id}")

    job.status = new_status
    job.last_status_at = last_status_at or dt.datetime.now(dt.timezone.utc)
    if source_message_id:
        job.source_message_id = source_message_id
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def record_email_event(
    db: Session,
    user_id: int,
    gmail_message_id: str,
    thread_id: Optional[str],
    event_type: str,
    extracted_entities: Optional[Dict[str, Any]] = None,
) -> EmailEvent:
    ev = EmailEvent(
        user_id=user_id,
        gmail_message_id=gmail_message_id,
        thread_id=thread_id,
        event_type=event_type,
        extracted_entities=extracted_entities,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def record_privacy_flag(db: Session, user_id: int, gmail_message_id: str, detected_secret_type: str) -> PrivacyFlag:
    flag = PrivacyFlag(
        user_id=user_id,
        gmail_message_id=gmail_message_id,
        detected_secret_type=detected_secret_type,
    )
    db.add(flag)
    db.commit()
    db.refresh(flag)
    return flag

def create_pending_action(db: Session, user_id: int, action_type: str, description: str, message_ids: List[str]) -> PendingAction:
    # Clear old pending actions for this user to keep 'Last Proposal' focused
    db.execute(delete(PendingAction).where(PendingAction.user_id == user_id, PendingAction.status == "pending"))
    
    action = PendingAction(user_id=user_id, action_type=action_type, description=description, message_ids=message_ids)
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


def get_latest_pending_action(db: Session, user_id: int) -> Optional[PendingAction]:
    stmt = select(PendingAction).where(PendingAction.user_id == user_id, PendingAction.status == "pending").order_by(PendingAction.created_at.desc())
    return db.execute(stmt).scalars().first()


def update_pending_action_status(db: Session, action_id: int, status: str) -> Optional[PendingAction]:
    action = db.execute(select(PendingAction).where(PendingAction.id == action_id)).scalars().first()
    if action:
        action.status = status
        db.add(action)
        db.commit()
        db.refresh(action)
    return action


def get_incomplete_scan_task(db: Session, user_id: int) -> Optional[ScanTask]:
    stmt = (
        select(ScanTask)
        .where(ScanTask.user_id == user_id, ScanTask.status.in_(["running", "failed"]))
        .order_by(ScanTask.created_at.desc())
        .limit(1)
    )
    return db.execute(stmt).scalars().first()


def start_scan_task(db: Session, user_id: int, task_type: str, scan_limit: int) -> ScanTask:
    # Fail any existing running ones to be clean
    db.execute(
        update(ScanTask)
        .where(ScanTask.user_id == user_id, ScanTask.status == "running")
        .values(status="failed")
    )
    task = ScanTask(user_id=user_id, task_type=task_type, scan_limit=scan_limit, status="running")
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_scan_progress(db: Session, task_id: int, processed_count: int, last_message_id: str) -> None:
    db.execute(
        update(ScanTask)
        .where(ScanTask.id == task_id)
        .values(processed_count=processed_count, last_message_id=last_message_id)
    )
    db.commit()


def complete_scan_task(db: Session, task_id: int) -> None:
    db.execute(update(ScanTask).where(ScanTask.id == task_id).values(status="completed"))
    db.commit()


def fail_scan_task(db: Session, task_id: int) -> None:
    db.execute(update(ScanTask).where(ScanTask.id == task_id).values(status="failed"))
    db.commit()
