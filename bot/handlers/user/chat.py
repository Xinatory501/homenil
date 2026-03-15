"""Chat with AI handlers."""
import logging
from datetime import datetime, timedelta
from typing import Optional

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, ChatSession, ChatHistory
from database.models.chat import MessageRole
from bot.states import UserStates
from bot.keyboards import UserKeyboards, AdminKeyboards
from bot.locales import get_text
from bot.services import AIService, TopicService
from bot.config import settings

logger = logging.getLogger(__name__)
router = Router(name="chat")


@router.callback_query(F.data == "chat:new")
async def start_new_chat(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Start a new chat session."""
    user_id = callback.from_user.id

    # Get user
    result = await bot_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        await callback.answer("Please use /start")
        return

    lang = user.language

    # Deactivate any existing sessions
    await bot_session.execute(
        update(ChatSession)
        .where(ChatSession.user_id == user_id, ChatSession.is_active == True)
        .values(is_active=False)
    )

    # Create new session
    session = ChatSession(user_id=user_id, is_active=True)
    bot_session.add(session)
    await bot_session.flush()

    # Update user stats
    user.session_count += 1
    user.ai_enabled = True
    user.ai_disabled_at = None

    await state.set_state(UserStates.chatting)
    await state.update_data(session_id=session.id)

    await callback.answer()
    try:
        await callback.message.edit_text(
            get_text("chat_started", lang),
            reply_markup=UserKeyboards.back_to_main(lang)
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("chat_started", lang),
            reply_markup=UserKeyboards.back_to_main(lang)
        )


@router.callback_query(F.data == "chat:continue")
async def continue_chat(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Continue existing chat session."""
    user_id = callback.from_user.id

    # Get user
    result = await bot_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        await callback.answer("Please use /start")
        return

    lang = user.language

    # Get active session
    session_result = await bot_session.execute(
        select(ChatSession).where(
            ChatSession.user_id == user_id,
            ChatSession.is_active == True
        )
    )
    session = session_result.scalar_one_or_none()

    if not session:
        await callback.answer(get_text("no_active_chat", lang))
        return

    await state.set_state(UserStates.chatting)
    await state.update_data(session_id=session.id)

    await callback.answer()
    try:
        await callback.message.edit_text(
            get_text("chat_continued", lang),
            reply_markup=UserKeyboards.back_to_main(lang)
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("chat_continued", lang),
            reply_markup=UserKeyboards.back_to_main(lang)
        )


@router.message(UserStates.chatting, F.text)
async def handle_chat_message(
    message: Message,
    state: FSMContext,
    bot: Bot,
    bot_session: AsyncSession,
    shared_session: AsyncSession,
    bot_id: str,
    support_group_id: Optional[int] = None
):
    """Handle user message in chat state."""
    user_id = message.from_user.id
    text = message.text

    # Get user
    result = await bot_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        await message.answer("Please use /start")
        return

    lang = user.language
    user.message_count += 1
    user.last_activity_at = datetime.utcnow()

    # Get session ID from state
    state_data = await state.get_data()
    session_id = state_data.get("session_id")

    if not session_id:
        # Try to get active session
        session_result = await bot_session.execute(
            select(ChatSession).where(
                ChatSession.user_id == user_id,
                ChatSession.is_active == True
            )
        )
        session = session_result.scalar_one_or_none()
        if not session:
            await message.answer(get_text("no_active_chat", lang))
            return
        session_id = session.id
        await state.update_data(session_id=session_id)

    # Save user message
    user_msg = ChatHistory(
        session_id=session_id,
        user_id=user_id,
        role=MessageRole.USER.value,
        content=text,
        message_id=message.message_id
    )
    bot_session.add(user_msg)
    await bot_session.flush()

    # Initialize services
    topic_service = TopicService(bot, bot_id, bot_session, shared_session)

    # Duplicate to support topic
    if support_group_id:
        await topic_service.send_to_topic(
            user,
            text,
            get_text("user_message_header", lang),
            buttons=AdminKeyboards.support_topic_buttons(user_id, lang)
        )

    # Check if AI is enabled for this user
    if not user.ai_enabled:
        # AI disabled (operator mode), don't respond
        logger.debug(f"AI disabled for user {user_id}, not responding")
        return

    # Check for auto-return of AI
    if user.ai_disabled_at:
        minutes_since_disable = (datetime.utcnow() - user.ai_disabled_at).total_seconds() / 60
        if minutes_since_disable >= settings.ai_auto_return_minutes:
            user.ai_enabled = True
            user.ai_disabled_at = None
            await message.answer(
                get_text("ai_auto_returned", lang, minutes=settings.ai_auto_return_minutes)
            )

    # Send thinking indicator
    thinking_msg = await message.answer(get_text("ai_thinking", lang))

    # Get AI response
    ai_service = AIService(shared_session, bot_session)
    response = await ai_service.get_response(
        user_id=user_id,
        message=text,
        session_id=session_id,
        lang=lang
    )

    # Delete thinking message
    try:
        await thinking_msg.delete()
    except TelegramBadRequest:
        pass

    # Handle special actions
    if response.action == "call_people":
        await _handle_operator_request(
            message, user, topic_service, bot_session, support_group_id, lang
        )
        return

    if response.action == "ignore_offtopic":
        await message.answer(get_text("offtopic_response", lang))
        # Save AI response
        ai_msg = ChatHistory(
            session_id=session_id,
            user_id=user_id,
            role=MessageRole.ASSISTANT.value,
            content=get_text("offtopic_response", lang),
            is_ai_handled=True,
            ai_action="ignore_offtopic"
        )
        bot_session.add(ai_msg)
        return

    if response.error:
        # AI failed, notify user and support
        await message.answer(get_text("error_ai_unavailable", lang))

        # Disable AI and request operator
        await _handle_operator_request(
            message, user, topic_service, bot_session, support_group_id, lang
        )

        logger.error(f"AI error for user {user_id}: {response.error}")
        return

    # Send AI response to user
    await message.answer(response.content)

    # Save AI response
    ai_msg = ChatHistory(
        session_id=session_id,
        user_id=user_id,
        role=MessageRole.ASSISTANT.value,
        content=response.content,
        is_ai_handled=True
    )
    bot_session.add(ai_msg)

    # Duplicate AI response to support topic
    if support_group_id:
        await topic_service.send_to_topic(
            user,
            response.content,
            get_text("ai_response_header", lang)
        )

    # Check if context compression needed
    await ai_service.compress_context(session_id)


@router.message(UserStates.chatting)
async def handle_non_text(message: Message, bot_session: AsyncSession):
    """Handle non-text messages in chat state."""
    user_id = message.from_user.id

    result = await bot_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    lang = user.language if user else "ru"
    await message.answer(get_text("only_text", lang))


async def _handle_operator_request(
    message: Message,
    user: User,
    topic_service: TopicService,
    bot_session: AsyncSession,
    support_group_id: Optional[int],
    lang: str
):
    """Handle request for human operator."""
    # Disable AI
    user.ai_enabled = False
    user.ai_disabled_at = datetime.utcnow()

    await message.answer(
        get_text("operator_requested", lang),
        reply_markup=UserKeyboards.return_ai(lang)
    )

    # Send alert to support
    if support_group_id:
        await topic_service.send_operator_alert(
            user, settings.admin_id_list
        )

    logger.info(f"User {user.id} requested operator")


@router.callback_query(F.data == "return_ai")
async def return_ai(
    callback: CallbackQuery,
    bot_session: AsyncSession
):
    """Return AI after operator request."""
    user_id = callback.from_user.id

    result = await bot_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        await callback.answer()
        return

    user.ai_enabled = True
    user.ai_disabled_at = None

    await callback.answer(get_text("ai_returned", user.language))
    try:
        await callback.message.edit_text(
            get_text("ai_returned", user.language),
            reply_markup=UserKeyboards.back_to_main(user.language)
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("ai_returned", user.language)
        )

    logger.info(f"User {user_id} returned AI")
