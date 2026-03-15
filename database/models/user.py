"""User-related database models."""
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
)
from sqlalchemy.orm import Mapped, mapped_column
import enum

from database.base import BotBase


class UserRole(str, enum.Enum):
    """User role enumeration."""
    USER = "user"
    ADMIN = "admin"


class User(BotBase):
    """User model for bot-specific database."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="ru")
    role: Mapped[str] = mapped_column(
        SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.USER.value
    )

    # Support topic
    thread_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)

    # Status flags
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    ban_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ban_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # AI state
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_disabled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Stats
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    session_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_users_thread_id", "thread_id"),
        Index("idx_users_username", "username"),
    )


class AdminAction(BotBase):
    """Log of admin actions."""
    __tablename__ = "admin_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(BigInteger, index=True)
    target_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    action: Mapped[str] = mapped_column(String(100))
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FloodLog(BotBase):
    """Flood detection log."""
    __tablename__ = "flood_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    message_count: Mapped[int] = mapped_column(Integer, default=1)
    window_start: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_flood_log_user_window", "user_id", "window_start"),
    )
