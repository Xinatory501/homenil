"""Ban check middleware."""
import logging
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from bot.locales import get_text

logger = logging.getLogger(__name__)


class BanCheckMiddleware(BaseMiddleware):
    """
    Middleware that checks if user is banned before processing.
    Runs early in the middleware chain.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Only check for messages and callbacks from users
        if not isinstance(event, Message):
            # For callback queries, extract message if available
            if hasattr(event, 'message') and event.message:
                pass
            else:
                return await handler(event, data)

        # Get user ID
        user_id = None
        if hasattr(event, 'from_user') and event.from_user:
            user_id = event.from_user.id

        if not user_id:
            return await handler(event, data)

        # Get session
        bot_session: AsyncSession = data.get("bot_session")
        if not bot_session:
            return await handler(event, data)

        # Check ban status
        result = await bot_session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user and user.is_banned:
            # Check if ban has expired
            if user.ban_until and user.ban_until < datetime.utcnow():
                # Unban user
                user.is_banned = False
                user.ban_until = None
                user.ban_reason = None
                await bot_session.commit()
                logger.info(f"User {user_id} auto-unbanned (ban expired)")
            else:
                # User is still banned
                if isinstance(event, Message):
                    lang = user.language if user else "ru"
                    reason = user.ban_reason or "N/A"
                    await event.answer(
                        get_text("error_banned", lang, reason=reason)
                    )
                logger.debug(f"Blocked message from banned user {user_id}")
                return  # Don't process further

        return await handler(event, data)
