"""Antiflood middleware."""
import logging
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, FloodLog, BotConfig
from database.models.user import UserRole
from bot.locales import get_text
from bot.config import settings

logger = logging.getLogger(__name__)


class AntiFloodMiddleware(BaseMiddleware):
    """
    Middleware that implements anti-flood protection.
    Tracks message frequency and auto-bans users who exceed limits.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Only check messages
        if not isinstance(event, Message):
            return await handler(event, data)

        # Skip for groups (only check private messages)
        if event.chat.type != "private":
            return await handler(event, data)

        user = event.from_user
        if not user:
            return await handler(event, data)

        user_id = user.id
        bot_session: AsyncSession = data.get("bot_session")

        if not bot_session:
            return await handler(event, data)

        # Check if user is admin (skip antiflood for admins)
        result = await bot_session.execute(
            select(User).where(User.id == user_id)
        )
        db_user = result.scalar_one_or_none()

        if db_user and db_user.role == UserRole.ADMIN.value:
            return await handler(event, data)

        # Get antiflood settings from config
        threshold = settings.antiflood_threshold
        time_window = settings.antiflood_time_window
        ban_duration = settings.autoban_duration

        # Try to get from database config
        for key, default in [
            ("antiflood_threshold", threshold),
            ("antiflood_time_window", time_window),
            ("autoban_duration", ban_duration),
        ]:
            result = await bot_session.execute(
                select(BotConfig).where(BotConfig.key == key)
            )
            config = result.scalar_one_or_none()
            if config:
                try:
                    if key == "antiflood_threshold":
                        threshold = int(config.value)
                    elif key == "antiflood_time_window":
                        time_window = int(config.value)
                    elif key == "autoban_duration":
                        ban_duration = int(config.value)
                except ValueError:
                    pass

        now = datetime.utcnow()
        window_start = now - timedelta(seconds=time_window)

        # Clean old flood logs
        await bot_session.execute(
            delete(FloodLog).where(FloodLog.window_start < window_start)
        )

        # Get current flood log for user
        result = await bot_session.execute(
            select(FloodLog).where(
                FloodLog.user_id == user_id,
                FloodLog.window_start >= window_start
            )
        )
        flood_log = result.scalar_one_or_none()

        if flood_log:
            flood_log.message_count += 1
        else:
            flood_log = FloodLog(
                user_id=user_id,
                message_count=1,
                window_start=now
            )
            bot_session.add(flood_log)

        await bot_session.flush()

        # Check if threshold exceeded
        if flood_log.message_count > threshold:
            # Ban user
            if db_user:
                db_user.is_banned = True
                db_user.ban_until = now + timedelta(seconds=ban_duration)
                db_user.ban_reason = "Antiflood: too many messages"
                logger.warning(
                    f"User {user_id} auto-banned for flooding "
                    f"({flood_log.message_count} messages in {time_window}s)"
                )
            else:
                # Create user and ban
                db_user = User(
                    id=user_id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    is_banned=True,
                    ban_until=now + timedelta(seconds=ban_duration),
                    ban_reason="Antiflood: too many messages"
                )
                bot_session.add(db_user)

            await bot_session.commit()

            lang = db_user.language if db_user else "ru"
            await event.answer(get_text("error_flood", lang))
            return  # Don't process further

        return await handler(event, data)
