"""Bot configuration module."""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Required
    bot1_token: str = Field(..., env="BOT1_TOKEN")
    admin_ids: str = Field(..., env="ADMIN_IDS")

    # Optional additional bots
    bot2_token: Optional[str] = Field(None, env="BOT2_TOKEN")
    bot3_token: Optional[str] = Field(None, env="BOT3_TOKEN")

    # Database
    database_url: str = Field(
        "postgresql+asyncpg://postgres:postgres@db:5432/cartame",
        env="DATABASE_URL"
    )
    shared_database_url: str = Field(
        "postgresql+asyncpg://postgres:postgres@db:5432/cartame_shared",
        env="SHARED_DATABASE_URL"
    )

    # Redis
    redis_url: Optional[str] = Field(None, env="REDIS_URL")

    # Defaults
    default_language: str = Field("ru", env="DEFAULT_LANGUAGE")
    banner_timeout: int = Field(5, env="BANNER_TIMEOUT")
    ai_auto_return_minutes: int = Field(10, env="AI_AUTO_RETURN_MINUTES")
    claim_expire_seconds: int = Field(300, env="CLAIM_EXPIRE_SECONDS")
    user_lock_minutes: int = Field(15, env="USER_LOCK_MINUTES")

    # Antiflood defaults
    antiflood_threshold: int = Field(10, env="ANTIFLOOD_THRESHOLD")
    antiflood_time_window: int = Field(60, env="ANTIFLOOD_TIME_WINDOW")
    autoban_duration: int = Field(3600, env="AUTOBAN_DURATION")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def admin_id_list(self) -> list[int]:
        """Parse admin IDs from comma-separated string."""
        if not self.admin_ids:
            return []
        return [int(x.strip()) for x in self.admin_ids.split(",") if x.strip()]

    @property
    def bot_tokens(self) -> dict[str, str]:
        """Get all configured bot tokens."""
        tokens = {"bot1": self.bot1_token}
        if self.bot2_token:
            tokens["bot2"] = self.bot2_token
        if self.bot3_token:
            tokens["bot3"] = self.bot3_token
        return tokens


settings = Settings()
