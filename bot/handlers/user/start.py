"""Start command and language selection handlers."""
import logging
import asyncio
from typing import Optional

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, ChatSession, BotConfig
from database.models.user import UserRole
from bot.states import UserStates
from bot.keyboards import UserKeyboards
from bot.locales import get_text, LANGUAGES
from bot.config import settings
from bot.services import TopicService

logger = logging.getLogger(__name__)
router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext,
    bot: Bot,
    bot_session: AsyncSession,
    shared_session: AsyncSession,
    bot_id: str,
    support_group_id: Optional[int] = None
):
    """Handle /start command."""
    # Clear FSM state
    await state.clear()

    user_id = message.from_user.id

    # Check if user exists
    result = await bot_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user:
        # Existing user - show welcome back message
        lang = user.language
        name = user.first_name or message.from_user.first_name or "User"

        # Update user info
        user.username = message.from_user.username
        user.first_name = message.from_user.first_name
        user.last_name = message.from_user.last_name

        # Check if has active chat
        session_result = await bot_session.execute(
            select(ChatSession).where(
                ChatSession.user_id == user_id,
                ChatSession.is_active == True
            )
        )
        has_active_chat = session_result.scalar_one_or_none() is not None

        # Try to send banner
        await _send_welcome(
            message,
            get_text("welcome_back", lang, name=name),
            UserKeyboards.main_menu(lang, has_active_chat),
            bot_session
        )

    else:
        # New user - show privacy policy and language selection
        # Get privacy policy URL
        result = await bot_session.execute(
            select(BotConfig).where(BotConfig.key == "privacy_policy_url")
        )
        config = result.scalar_one_or_none()
        privacy_url = config.value if config else "https://example.com/privacy"

        text = get_text("welcome_new", "ru")
        text += "\n\n" + get_text("privacy_policy", "ru", url=privacy_url)
        text += "\n\n" + get_text("select_language", "ru")

        await _send_welcome(
            message,
            text,
            UserKeyboards.language_selection(),
            bot_session
        )

        await state.set_state(UserStates.selecting_language)


async def _send_welcome(
    message: Message,
    text: str,
    keyboard,
    bot_session: AsyncSession
):
    """Send welcome message, trying banner first."""
    # Try to get banner path from config
    result = await bot_session.execute(
        select(BotConfig).where(BotConfig.key == "banner_path")
    )
    config = result.scalar_one_or_none()
    banner_path = config.value if config else None

    if banner_path:
        try:
            # Try to send with banner
            await asyncio.wait_for(
                message.answer_photo(
                    photo=FSInputFile(banner_path),
                    caption=text,
                    reply_markup=keyboard
                ),
                timeout=settings.banner_timeout
            )
            return
        except asyncio.TimeoutError:
            logger.warning("Banner send timed out, falling back to text")
        except Exception as e:
            logger.warning(f"Failed to send banner: {e}")

    # Fallback to text only
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("lang:"))
async def select_language(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    bot_session: AsyncSession,
    shared_session: AsyncSession,
    bot_id: str,
    support_group_id: Optional[int] = None
):
    """Handle language selection."""
    lang = callback.data.split(":")[1]

    if lang not in LANGUAGES:
        await callback.answer("Invalid language")
        return

    user_id = callback.from_user.id

    # Check if user exists
    result = await bot_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        # Create new user
        user = User(
            id=user_id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            last_name=callback.from_user.last_name,
            language=lang,
            role=UserRole.USER.value
        )

        # Check if user should be admin
        if user_id in settings.admin_id_list:
            user.role = UserRole.ADMIN.value
            logger.info(f"User {user_id} auto-granted admin role")

        bot_session.add(user)
        await bot_session.flush()

        # Create support topic
        if support_group_id:
            topic_service = TopicService(
                bot, bot_id, bot_session, shared_session
            )
            await topic_service.get_or_create_topic(user, support_group_id)

    else:
        # Update language
        old_lang = user.language
        user.language = lang

        # Update topic name if language changed
        if old_lang != lang and support_group_id:
            topic_service = TopicService(
                bot, bot_id, bot_session, shared_session
            )
            await topic_service.update_topic_language(user, lang)

    await bot_session.commit()

    # Clear state
    await state.clear()

    # Show confirmation and main menu
    await callback.answer(get_text("language_set", lang))

    try:
        await callback.message.edit_text(
            get_text("main_menu", lang),
            reply_markup=UserKeyboards.main_menu(lang, False)
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("main_menu", lang),
            reply_markup=UserKeyboards.main_menu(lang, False)
        )


@router.callback_query(F.data == "back:main")
async def back_to_main(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Return to main menu."""
    await state.clear()

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

    # Check for active chat
    session_result = await bot_session.execute(
        select(ChatSession).where(
            ChatSession.user_id == user_id,
            ChatSession.is_active == True
        )
    )
    has_active_chat = session_result.scalar_one_or_none() is not None

    await callback.answer()

    try:
        await callback.message.edit_text(
            get_text("main_menu", lang),
            reply_markup=UserKeyboards.main_menu(lang, has_active_chat)
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("main_menu", lang),
            reply_markup=UserKeyboards.main_menu(lang, has_active_chat)
        )
