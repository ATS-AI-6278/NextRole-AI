import datetime as dt

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import relationship

from app.core.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_chat_id = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    gmail_accounts = relationship("GmailAccount", back_populates="user")
    job_applications = relationship("JobApplication", back_populates="user")


class GmailAccount(Base):
    __tablename__ = "gmail_accounts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    email_address = Column(String, index=True, nullable=False)
    oauth_refresh_token_encrypted = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="gmail_accounts")


class Thread(Base):
    __tablename__ = "threads"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    gmail_thread_id = Column(String, index=True, nullable=False)
    labels_applied = Column(SQLiteJSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    company = Column(String, index=True, nullable=False)
    role = Column(String, index=True, nullable=True)
    applied_at = Column(DateTime(timezone=True), nullable=True)

    status = Column(String, index=True, nullable=False, default="Applied")
    last_status_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    source_message_id = Column(String, index=True, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="job_applications")


class EmailEvent(Base):
    __tablename__ = "email_events"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    gmail_message_id = Column(String, index=True, nullable=False)
    thread_id = Column(String, index=True, nullable=True)
    event_type = Column(String, index=True, nullable=False)

    extracted_entities = Column(SQLiteJSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PrivacyFlag(Base):
    __tablename__ = "privacy_flags"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    gmail_message_id = Column(String, index=True, nullable=False)
    detected_secret_type = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def _utcnow():
    return dt.datetime.now(dt.timezone.utc)

