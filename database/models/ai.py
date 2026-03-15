"""AI provider, key, and model database models (shared database)."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    Index,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import SharedBase


class AIProvider(SharedBase):
    """AI provider configuration."""
    __tablename__ = "ai_providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    base_url: Mapped[str] = mapped_column(String(500))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    keys: Mapped[list["AIKey"]] = relationship("AIKey", back_populates="provider", lazy="selectin")
    models: Mapped[list["AIModel"]] = relationship("AIModel", back_populates="provider", lazy="selectin")


class AIKey(SharedBase):
    """API key for AI provider."""
    __tablename__ = "ai_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider_id: Mapped[int] = mapped_column(Integer, ForeignKey("ai_providers.id"), index=True)
    api_key: Mapped[str] = mapped_column(String(500))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Rate limiting
    requests_made: Mapped[int] = mapped_column(Integer, default=0)
    requests_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    limit_reset_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Cooldown for 429 errors
    cooldown_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Error tracking
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_error_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    provider: Mapped["AIProvider"] = relationship("AIProvider", back_populates="keys")

    @property
    def masked_key(self) -> str:
        """Return masked API key for display."""
        if len(self.api_key) <= 8:
            return "*" * len(self.api_key)
        return f"{self.api_key[:4]}...{self.api_key[-4:]}"


class AIModel(SharedBase):
    """AI model configuration."""
    __tablename__ = "ai_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider_id: Mapped[int] = mapped_column(Integer, ForeignKey("ai_providers.id"), index=True)
    model_name: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(255))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    # Error tracking
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_error_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    provider: Mapped["AIProvider"] = relationship("AIProvider", back_populates="models")

    __table_args__ = (
        Index("idx_ai_models_provider_active", "provider_id", "is_active"),
    )
