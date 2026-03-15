"""Database middleware for injecting sessions."""
import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from sqlalchemy import select

from database.base import get_bot_session_factory, get_shared_session_factory
from database.models import BotConfig

logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    """
    Middleware that provides database sessions for each update.
    Injects bot_id, bot_session, shared_session, and support_group_id into handler data.
    """

    def __init__(self, bot_id: str):
        self.bot_id = bot_id
        self.bot_session_factory = get_bot_session_factory(bot_id)
        self.shared_session_factory = get_shared_session_factory()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Create sessions
        async with self.bot_session_factory() as bot_session:
            async with self.shared_session_factory() as shared_session:
                # Inject bot_id and sessions
                data["bot_id"] = self.bot_id
                data["bot_session"] = bot_session
                data["shared_session"] = shared_session

                # Get support_group_id from config
                result = await bot_session.execute(
                    select(BotConfig).where(BotConfig.key == "support_group_id")
                )
                config = result.scalar_one_or_none()
                data["support_group_id"] = int(config.value) if config and config.value else None

                try:
                    result = await handler(event, data)
                    await bot_session.commit()
                    await shared_session.commit()
                    return result
                except Exception as e:
                    await bot_session.rollback()
                    await shared_session.rollback()
                    logger.error(f"Handler error: {e}", exc_info=True)
                    raise
