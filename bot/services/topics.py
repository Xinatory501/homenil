"""Topic management service for support groups."""
import logging
from typing import Optional, Tuple

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, BotUserThread, BotConfig
from bot.locales import get_text

logger = logging.getLogger(__name__)


class TopicService:
    """Service for managing support topics in supergroups."""

    def __init__(
        self,
        bot: Bot,
        bot_id: str,
        bot_session: AsyncSession,
        shared_session: AsyncSession
    ):
        self.bot = bot
        self.bot_id = bot_id
        self.bot_session = bot_session
        self.shared_session = shared_session

    async def get_support_group_id(self) -> Optional[int]:
        """Get configured support group ID."""
        result = await self.bot_session.execute(
            select(BotConfig).where(BotConfig.key == "support_group_id")
        )
        config = result.scalar_one_or_none()
        return int(config.value) if config and config.value else None

    async def get_or_create_topic(
        self,
        user: User,
        support_group_id: int
    ) -> Optional[int]:
        """
        Get existing topic or create new one for user.
        Each bot maintains its own topic per user.
        """
        # Check for existing topic in shared DB
        result = await self.shared_session.execute(
            select(BotUserThread).where(
                BotUserThread.user_id == user.id,
                BotUserThread.bot_id == self.bot_id,
                BotUserThread.support_chat_id == support_group_id
            )
        )
        thread_record = result.scalar_one_or_none()

        if thread_record:
            # Verify topic still exists
            try:
                # Try to get chat info (will fail if topic deleted)
                # For now, just try to send a test message or use the thread
                return thread_record.thread_id
            except TelegramBadRequest:
                # Topic was deleted, need to recreate
                logger.info(f"Topic {thread_record.thread_id} no longer exists, recreating")
                await self.shared_session.delete(thread_record)
                await self.shared_session.flush()

        # Create new topic
        return await self._create_topic(user, support_group_id)

    async def _create_topic(
        self,
        user: User,
        support_group_id: int
    ) -> Optional[int]:
        """Create new topic for user in support group."""
        # Build topic name: [B1][ru] Name (ID)
        bot_label = self.bot_id.upper().replace("BOT", "B")
        lang_label = user.language.upper()
        name = user.first_name or user.username or "User"
        topic_name = f"[{bot_label}][{lang_label}] {name} ({user.id})"

        try:
            # Create forum topic
            result = await self.bot.create_forum_topic(
                chat_id=support_group_id,
                name=topic_name[:128]  # Telegram limit
            )

            thread_id = result.message_thread_id

            # Save to shared DB
            thread_record = BotUserThread(
                user_id=user.id,
                bot_id=self.bot_id,
                support_chat_id=support_group_id,
                thread_id=thread_id,
                language=user.language
            )
            self.shared_session.add(thread_record)
            await self.shared_session.flush()

            # Also update user's thread_id in bot DB for quick lookup
            user.thread_id = thread_id

            logger.info(
                f"Created topic {thread_id} for user {user.id} "
                f"in bot {self.bot_id}"
            )

            # Send initial message
            await self.bot.send_message(
                chat_id=support_group_id,
                message_thread_id=thread_id,
                text=get_text("topic_created", user.language, name=name, id=user.id)
            )

            return thread_id

        except TelegramBadRequest as e:
            logger.error(f"Failed to create topic: {e}")
            return None
        except TelegramForbiddenError as e:
            logger.error(f"Bot not allowed to create topics: {e}")
            return None

    async def send_to_topic(
        self,
        user: User,
        text: str,
        header: str,
        is_ai: bool = False,
        buttons=None
    ) -> bool:
        """
        Send message to user's support topic.
        Handles topic recreation if deleted.
        """
        support_group_id = await self.get_support_group_id()
        if not support_group_id:
            logger.warning("No support group configured")
            return False

        thread_id = await self.get_or_create_topic(user, support_group_id)
        if not thread_id:
            return False

        formatted_text = f"<b>{header}</b>\n\n{text}"

        try:
            await self.bot.send_message(
                chat_id=support_group_id,
                message_thread_id=thread_id,
                text=formatted_text,
                parse_mode="HTML",
                reply_markup=buttons
            )
            return True

        except TelegramBadRequest as e:
            if "thread not found" in str(e).lower() or "message thread not found" in str(e).lower():
                # Topic was deleted, clear and retry
                logger.info(f"Topic {thread_id} deleted, recreating...")

                # Clear old thread record
                await self._clear_thread_record(user.id)

                # Try again with new topic
                new_thread_id = await self.get_or_create_topic(user, support_group_id)
                if new_thread_id:
                    try:
                        await self.bot.send_message(
                            chat_id=support_group_id,
                            message_thread_id=new_thread_id,
                            text=formatted_text,
                            parse_mode="HTML",
                            reply_markup=buttons
                        )
                        return True
                    except Exception as e2:
                        logger.error(f"Failed to send after topic recreation: {e2}")
                        return False

            logger.error(f"Failed to send to topic: {e}")
            return False

    async def _clear_thread_record(self, user_id: int) -> None:
        """Clear thread record for user."""
        # Clear from shared DB
        result = await self.shared_session.execute(
            select(BotUserThread).where(
                BotUserThread.user_id == user_id,
                BotUserThread.bot_id == self.bot_id
            )
        )
        thread_record = result.scalar_one_or_none()
        if thread_record:
            await self.shared_session.delete(thread_record)

        # Clear from user record
        result = await self.bot_session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.thread_id = None

    async def update_topic_language(self, user: User, new_language: str) -> None:
        """Update topic name when user changes language."""
        support_group_id = await self.get_support_group_id()
        if not support_group_id:
            return

        result = await self.shared_session.execute(
            select(BotUserThread).where(
                BotUserThread.user_id == user.id,
                BotUserThread.bot_id == self.bot_id
            )
        )
        thread_record = result.scalar_one_or_none()

        if not thread_record:
            return

        # Build new topic name
        bot_label = self.bot_id.upper().replace("BOT", "B")
        lang_label = new_language.upper()
        name = user.first_name or user.username or "User"
        new_topic_name = f"[{bot_label}][{lang_label}] {name} ({user.id})"

        try:
            await self.bot.edit_forum_topic(
                chat_id=support_group_id,
                message_thread_id=thread_record.thread_id,
                name=new_topic_name[:128]
            )

            # Update record
            thread_record.language = new_language

            logger.info(
                f"Updated topic language for user {user.id} to {new_language}"
            )

        except TelegramBadRequest as e:
            logger.error(f"Failed to update topic name: {e}")

    async def find_user_by_thread(self, thread_id: int) -> Optional[User]:
        """Find user by their support thread ID."""
        # First check shared DB for multi-bot
        result = await self.shared_session.execute(
            select(BotUserThread).where(
                BotUserThread.thread_id == thread_id,
                BotUserThread.bot_id == self.bot_id
            )
        )
        thread_record = result.scalar_one_or_none()

        if thread_record:
            user_result = await self.bot_session.execute(
                select(User).where(User.id == thread_record.user_id)
            )
            return user_result.scalar_one_or_none()

        # Fallback to direct user lookup
        result = await self.bot_session.execute(
            select(User).where(User.thread_id == thread_id)
        )
        return result.scalar_one_or_none()

    async def send_operator_alert(
        self,
        user: User,
        admin_ids: list[int]
    ) -> None:
        """Send alert when user requests operator."""
        support_group_id = await self.get_support_group_id()
        if not support_group_id:
            return

        thread_id = await self.get_or_create_topic(user, support_group_id)
        if not thread_id:
            return

        name = user.first_name or user.username or "User"
        alert_text = get_text("operator_alert", user.language, name=name, id=user.id)

        # Build mentions for admins (excluding bots)
        mentions = []
        for admin_id in admin_ids:
            try:
                member = await self.bot.get_chat_member(support_group_id, admin_id)
                if not member.user.is_bot:
                    mentions.append(f'<a href="tg://user?id={admin_id}">{member.user.first_name}</a>')
            except Exception:
                continue

        if mentions:
            alert_text += "\n\n" + " ".join(mentions)

        try:
            await self.bot.send_message(
                chat_id=support_group_id,
                message_thread_id=thread_id,
                text=alert_text,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to send operator alert: {e}")
