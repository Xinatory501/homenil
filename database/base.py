"""Database base configuration and session management."""
import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase

from bot.config import settings

logger = logging.getLogger(__name__)


class BotBase(DeclarativeBase):
    """Base class for bot-specific tables."""
    pass


class SharedBase(DeclarativeBase):
    """Base class for shared tables across bots."""
    pass


# Engine cache
_bot_engines: dict[str, AsyncEngine] = {}
_shared_engine: AsyncEngine | None = None

# Session factories
_bot_session_factories: dict[str, async_sessionmaker[AsyncSession]] = {}
_shared_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_bot_engine(bot_id: str) -> AsyncEngine:
    """Get or create engine for bot-specific database."""
    if bot_id not in _bot_engines:
        # Use bot-specific database URL
        base_url = settings.database_url
        if bot_id != "bot1":
            # Append bot suffix to database name
            base_url = base_url.replace("/cartame", f"/cartame_{bot_id}")

        _bot_engines[bot_id] = create_async_engine(
            base_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    return _bot_engines[bot_id]


def get_shared_engine() -> AsyncEngine:
    """Get or create engine for shared database."""
    global _shared_engine
    if _shared_engine is None:
        _shared_engine = create_async_engine(
            settings.shared_database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    return _shared_engine


def get_bot_session_factory(bot_id: str) -> async_sessionmaker[AsyncSession]:
    """Get session factory for bot database."""
    if bot_id not in _bot_session_factories:
        engine = get_bot_engine(bot_id)
        _bot_session_factories[bot_id] = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _bot_session_factories[bot_id]


def get_shared_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get session factory for shared database."""
    global _shared_session_factory
    if _shared_session_factory is None:
        engine = get_shared_engine()
        _shared_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _shared_session_factory


@asynccontextmanager
async def get_bot_session(bot_id: str) -> AsyncGenerator[AsyncSession, None]:
    """Get async session for bot database."""
    factory = get_bot_session_factory(bot_id)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_shared_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async session for shared database."""
    factory = get_shared_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_bot_db(bot_id: str) -> None:
    """Initialize bot-specific database tables."""
    engine = get_bot_engine(bot_id)
    async with engine.begin() as conn:
        await conn.run_sync(BotBase.metadata.create_all)
    logger.info(f"Bot database initialized: {bot_id}")


async def init_shared_db() -> None:
    """Initialize shared database tables."""
    engine = get_shared_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SharedBase.metadata.create_all)
    logger.info("Shared database initialized")


async def close_all_engines() -> None:
    """Close all database engines."""
    global _shared_engine

    for engine in _bot_engines.values():
        await engine.dispose()
    _bot_engines.clear()
    _bot_session_factories.clear()

    if _shared_engine:
        await _shared_engine.dispose()
        _shared_engine = None
