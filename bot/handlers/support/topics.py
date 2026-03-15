"""Topic message handlers for support group."""
import logging
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, ChatHistory, ChatSession, AdminAction, BotUserThread
from database.models.chat import MessageRole
from database.models.user import UserRole
from bot.services import AIService, TopicService
from bot.keyboards import AdminKeyboards
from bot.locales import get_text
from bot.config import settings

logger = logging.getLogger(__name__)
router = Router(name="support_topics")


@router.message(F.chat.type.in_({"group", "supergroup"}), F.message_thread_id)
async def handle_topic_message(
    message: Message,
    bot: Bot,
    bot_session: AsyncSession,
    shared_session: AsyncSession,
    bot_id: str,
    support_group_id: int = None
):
    """
    Handle messages in support topics.
    Routes operator messages to users.
    """
    # Skip if not in support group
    if support_group_id and message.chat.id != support_group_id:
        return

    # Skip bot messages
    if message.from_user.is_bot:
        return

    # Skip commands
    if message.text and message.text.startswith("/"):
        # Handle /ai command
        if message.text.strip().lower() == "/ai":
            await _enable_ai_for_topic(message, bot_session, shared_session, bot_id)
        return

    # Find user by thread_id
    topic_service = TopicService(bot, bot_id, bot_session, shared_session)
    user = await topic_service.find_user_by_thread(message.message_thread_id)

    if not user:
        # Not a user topic, ignore
        return

    # Skip if message is from the user themselves (anti-loop)
    if message.from_user.id == user.id:
        return

    sender_id = message.from_user.id

    # Check if first operator message after AI was active
    first_operator_msg = user.ai_enabled

    # Disable AI
    if user.ai_enabled:
        user.ai_enabled = False
        user.ai_disabled_at = datetime.utcnow()

    # Send notification to user if first operator message
    if first_operator_msg:
        try:
            await bot.send_message(
                chat_id=user.id,
                text=get_text("operator_connected", user.language)
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user.id}: {e}")

    # Forward message to user
    try:
        if message.text:
            # Text message
            await bot.send_message(
                chat_id=user.id,
                text=get_text("support_reply", user.language, message=message.text)
            )
        else:
            # Media message - copy it
            await message.copy_to(
                chat_id=user.id
            )

        # Save to history
        content = message.text or "[media]"
        session_result = await bot_session.execute(
            select(ChatSession).where(
                ChatSession.user_id == user.id,
                ChatSession.is_active == True
            )
        )
        session = session_result.scalar_one_or_none()

        if session:
            history_entry = ChatHistory(
                session_id=session.id,
                user_id=user.id,
                role=MessageRole.SUPPORT.value,
                content=content,
                is_ai_handled=False,
                message_id=message.message_id
            )
            bot_session.add(history_entry)

        logger.info(f"Operator message forwarded to user {user.id}")

    except TelegramBadRequest as e:
        logger.error(f"Failed to forward message to user {user.id}: {e}")
        await message.reply(f"Could not send to user: {e}")


async def _enable_ai_for_topic(
    message: Message,
    bot_session: AsyncSession,
    shared_session: AsyncSession,
    bot_id: str
):
    """Enable AI for user via /ai command in topic."""
    # Find user by thread
    result = await shared_session.execute(
        select(BotUserThread).where(
            BotUserThread.thread_id == message.message_thread_id,
            BotUserThread.bot_id == bot_id
        )
    )
    thread_record = result.scalar_one_or_none()

    if not thread_record:
        return

    user_result = await bot_session.execute(
        select(User).where(User.id == thread_record.user_id)
    )
    user = user_result.scalar_one_or_none()

    if user:
        user.ai_enabled = True
        user.ai_disabled_at = None
        await message.reply(f"AI enabled for user {user.id}")
        logger.info(f"AI enabled for user {user.id} via /ai command")


@router.callback_query(F.data.startswith("ai_reply_"))
async def ai_reply_callback(
    callback: CallbackQuery,
    bot: Bot,
    bot_session: AsyncSession,
    shared_session: AsyncSession,
    bot_id: str
):
    """Generate AI reply for user from topic."""
    user_id = int(callback.data.split("_")[-1])

    # Get user
    result = await bot_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        await callback.answer("User not found")
        return

    # Get last user message
    history_result = await bot_session.execute(
        select(ChatHistory)
        .where(
            ChatHistory.user_id == user_id,
            ChatHistory.role == MessageRole.USER.value
        )
        .order_by(ChatHistory.created_at.desc())
        .limit(1)
    )
    last_msg = history_result.scalar_one_or_none()

    if not last_msg:
        await callback.answer("No message to reply to")
        return

    # Get or create session
    session_result = await bot_session.execute(
        select(ChatSession).where(
            ChatSession.user_id == user_id,
            ChatSession.is_active == True
        )
    )
    session = session_result.scalar_one_or_none()

    if not session:
        session = ChatSession(user_id=user_id, is_active=True)
        bot_session.add(session)
        await bot_session.flush()

    await callback.answer("Generating AI response...")

    # Get AI response
    ai_service = AIService(shared_session, bot_session)
    response = await ai_service.get_response(
        user_id=user_id,
        message=last_msg.content,
        session_id=session.id,
        lang=user.language
    )

    if response.error:
        await callback.message.reply(f"AI Error: {response.error}")
        return

    # Send to user
    try:
        await bot.send_message(
            chat_id=user_id,
            text=response.content
        )
    except Exception as e:
        await callback.message.reply(f"Failed to send to user: {e}")
        return

    # Send to topic
    topic_service = TopicService(bot, bot_id, bot_session, shared_session)
    await topic_service.send_to_topic(
        user,
        response.content,
        get_text("ai_response_header", user.language)
    )

    # Save to history
    history_entry = ChatHistory(
        session_id=session.id,
        user_id=user_id,
        role=MessageRole.ASSISTANT.value,
        content=response.content,
        is_ai_handled=True
    )
    bot_session.add(history_entry)

    logger.info(f"AI reply sent to user {user_id} from topic")


@router.callback_query(F.data.startswith("resend_to_ai_"))
async def resend_to_ai_callback(
    callback: CallbackQuery,
    bot_session: AsyncSession
):
    """Enable AI for user (admin only)."""
    user_id = int(callback.data.split("_")[-1])

    # Check if caller is admin
    if callback.from_user.id not in settings.admin_id_list:
        caller_result = await bot_session.execute(
            select(User).where(User.id == callback.from_user.id)
        )
        caller = caller_result.scalar_one_or_none()
        if not caller or caller.role != UserRole.ADMIN.value:
            await callback.answer("Admin only")
            return

    # Get user
    result = await bot_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user:
        user.ai_enabled = True
        user.ai_disabled_at = None
        await callback.answer(f"AI enabled for user {user_id}")
        logger.info(f"AI enabled for user {user_id} by admin {callback.from_user.id}")
    else:
        await callback.answer("User not found")


@router.callback_query(F.data.startswith("ban_user_"))
async def ban_user_callback(
    callback: CallbackQuery,
    bot: Bot,
    bot_session: AsyncSession
):
    """Ban user from topic (admin only)."""
    user_id = int(callback.data.split("_")[-1])

    # Check if caller is admin
    if callback.from_user.id not in settings.admin_id_list:
        caller_result = await bot_session.execute(
            select(User).where(User.id == callback.from_user.id)
        )
        caller = caller_result.scalar_one_or_none()
        if not caller or caller.role != UserRole.ADMIN.value:
            await callback.answer("Admin only")
            return

    # Get user
    result = await bot_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user:
        user.is_banned = True
        user.ban_reason = "Banned by admin from support topic"

        # Log action
        action = AdminAction(
            admin_id=callback.from_user.id,
            target_user_id=user_id,
            action="ban",
            details="Banned from support topic"
        )
        bot_session.add(action)

        # Notify user
        try:
            await bot.send_message(
                chat_id=user_id,
                text=get_text("error_banned", user.language, reason=user.ban_reason)
            )
        except Exception:
            pass

        await callback.answer(f"User {user_id} banned")
        logger.info(f"User {user_id} banned by admin {callback.from_user.id}")
    else:
        await callback.answer("User not found")
