"""Group management handlers."""
import logging

from aiogram import Router, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import Command
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ManagedChat, BotConfig, User
from bot.locales import get_text

logger = logging.getLogger(__name__)
router = Router(name="support_group")


@router.message(Command("id"))
async def cmd_id(
    message: Message,
    bot_session: AsyncSession
):
    """Handle ?id or /id command in groups."""
    # Get chat info
    chat = message.chat
    thread_id = message.message_thread_id
    reply_to = message.reply_to_message.message_id if message.reply_to_message else None
    user = message.from_user

    # Get user language
    result = await bot_session.execute(
        select(User).where(User.id == user.id)
    )
    db_user = result.scalar_one_or_none()
    lang = db_user.language if db_user else "ru"

    text = get_text(
        "group_info", lang,
        chat_id=chat.id,
        type=chat.type,
        title=chat.title or "N/A",
        thread_id=thread_id or "N/A",
        message_id=message.message_id,
        reply_to=reply_to or "N/A",
        user=f"@{user.username}" if user.username else user.first_name
    )

    await message.answer(text)

    # Upsert chat to managed_chats
    existing = await bot_session.execute(
        select(ManagedChat).where(ManagedChat.id == chat.id)
    )
    managed = existing.scalar_one_or_none()

    if managed:
        managed.title = chat.title
        managed.type = chat.type
        managed.is_active = True
    else:
        managed = ManagedChat(
            id=chat.id,
            type=chat.type,
            title=chat.title,
            is_active=True
        )
        bot_session.add(managed)

    logger.info(f"Chat {chat.id} registered via /id command")


@router.message(F.text == "?id")
async def cmd_qid(
    message: Message,
    bot_session: AsyncSession
):
    """Handle ?id text command (alias for /id)."""
    await cmd_id(message, bot_session)


@router.my_chat_member()
async def on_my_chat_member(
    event: ChatMemberUpdated,
    bot_session: AsyncSession
):
    """Track bot membership changes in chats."""
    chat = event.chat
    new_status = event.new_chat_member.status
    old_status = event.old_chat_member.status

    logger.info(
        f"Bot membership changed in {chat.id}: {old_status} -> {new_status}"
    )

    # Get or create managed chat
    result = await bot_session.execute(
        select(ManagedChat).where(ManagedChat.id == chat.id)
    )
    managed = result.scalar_one_or_none()

    if new_status in ("member", "administrator"):
        # Bot added to chat
        if managed:
            managed.title = chat.title
            managed.type = chat.type
            managed.is_active = True
        else:
            managed = ManagedChat(
                id=chat.id,
                type=chat.type,
                title=chat.title,
                is_active=True
            )
            bot_session.add(managed)

        logger.info(f"Bot joined chat {chat.id}")

    elif new_status in ("left", "kicked"):
        # Bot removed from chat
        if managed:
            managed.is_active = False

            # If this was primary chat, clear support_group_id
            if managed.is_primary:
                managed.is_primary = False

                config_result = await bot_session.execute(
                    select(BotConfig).where(BotConfig.key == "support_group_id")
                )
                config = config_result.scalar_one_or_none()
                if config:
                    config.value = ""

                logger.warning(
                    f"Bot removed from primary support group {chat.id}, "
                    "support_group_id cleared"
                )

        logger.info(f"Bot left chat {chat.id}")
