"""Multi-bot coordination models (shared database)."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Integer,
    String,
    DateTime,
    Index,
    UniqueConstraint,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column
import enum

from database.base import SharedBase


class ClaimStatus(str, enum.Enum):
    """Request claim status."""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RequestClaim(SharedBase):
    """
    Request claims for multi-bot coordination.
    Ensures only one bot processes each user message.
    """
    __tablename__ = "request_claims"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Unique claim key: chat_id:user_id:message_id
    claim_key: Mapped[str] = mapped_column(String(200), unique=True, index=True)

    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger)
    message_id: Mapped[int] = mapped_column(BigInteger)
    update_id: Mapped[int] = mapped_column(BigInteger)
    bot_id: Mapped[str] = mapped_column(String(50))  # bot1, bot2, bot3

    status: Mapped[str] = mapped_column(
        SQLEnum(ClaimStatus, values_callable=lambda x: [e.value for e in x]),
        default=ClaimStatus.PROCESSING.value
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)

    __table_args__ = (
        Index("idx_request_claims_expires", "expires_at"),
        Index("idx_request_claims_user_status", "user_id", "status"),
    )


class UserOwnerLock(SharedBase):
    """
    Sticky user ownership for consistent bot assignment.
    One user is handled by one bot for a period of time.
    """
    __tablename__ = "user_owner_lock"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    owner_bot_id: Mapped[str] = mapped_column(String(50))
    locked_until: Mapped[datetime] = mapped_column(DateTime, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class BotUserThread(SharedBase):
    """
    Per-bot support topics for users.
    Each bot maintains its own topic for each user.
    """
    __tablename__ = "bot_user_threads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    bot_id: Mapped[str] = mapped_column(String(50))  # bot1, bot2, bot3
    support_chat_id: Mapped[int] = mapped_column(BigInteger)
    thread_id: Mapped[int] = mapped_column(BigInteger)
    language: Mapped[str] = mapped_column(String(10), default="ru")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint("user_id", "bot_id", name="uq_user_bot_thread"),
        Index("idx_bot_user_threads_thread", "thread_id"),
        Index("idx_bot_user_threads_chat_thread", "support_chat_id", "thread_id"),
    )
