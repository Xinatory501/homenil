"""Chat-related database models."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    String,
    Boolean,
    DateTime,
    Integer,
    Text,
    Index,
    Enum as SQLEnum,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column
import enum

from database.base import BotBase


class MessageRole(str, enum.Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SUPPORT = "support"
    SYSTEM = "system"


class RequestStatus(str, enum.Enum):
    """Pending request status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ChatSession(BotBase):
    """Chat session model."""
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Context summary for long conversations
    context_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("idx_chat_sessions_user_active", "user_id", "is_active"),
    )


class ChatHistory(BotBase):
    """Chat history model."""
    __tablename__ = "chat_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)

    role: Mapped[str] = mapped_column(
        SQLEnum(MessageRole, values_callable=lambda x: [e.value for e in x])
    )
    content: Mapped[str] = mapped_column(Text)

    # AI handling info
    is_ai_handled: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_action: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # call_people, ignore_offtopic

    # Metadata
    message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    topic_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_chat_history_session_created", "session_id", "created_at"),
        Index("idx_chat_history_user_created", "user_id", "created_at"),
    )


class ManagedChat(BotBase):
    """Managed chats (groups/supergroups) model."""
    __tablename__ = "managed_chats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    type: Mapped[str] = mapped_column(String(50))
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class BotConfig(BotBase):
    """Bot configuration stored in database."""
    __tablename__ = "bot_config"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class TrainingMessage(BotBase):
    """Training/system messages for AI context."""
    __tablename__ = "training_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, default=5)  # 1-10, 1 is highest
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("idx_training_active_priority", "is_active", "priority"),
    )


class PendingRequest(BotBase):
    """Pending AI requests for recovery."""
    __tablename__ = "pending_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger)
    message_id: Mapped[int] = mapped_column(BigInteger)
    message_text: Mapped[str] = mapped_column(Text)
    session_id: Mapped[int] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(
        SQLEnum(RequestStatus, values_callable=lambda x: [e.value for e in x]),
        default=RequestStatus.PENDING.value
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("idx_pending_status_created", "status", "created_at"),
    )
