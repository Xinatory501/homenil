"""Chat management handlers."""
import logging

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, ManagedChat, BotConfig
from bot.states import AdminStates
from bot.keyboards import AdminKeyboards
from bot.locales import get_text

logger = logging.getLogger(__name__)
router = Router(name="admin_chats")


@router.callback_query(F.data == "admin:chats")
async def show_chats(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Show managed chats list."""
    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    chats_result = await bot_session.execute(
        select(ManagedChat).order_by(ManagedChat.is_primary.desc(), ManagedChat.title)
    )
    chats = list(chats_result.scalars().all())

    total_pages = max(1, (len(chats) + 4) // 5)

    await state.set_state(AdminStates.chats_list)
    await callback.answer()

    text = get_text("chats_list", lang, page=1, total=total_pages)
    if not chats:
        text = get_text("no_chats", lang)

    try:
        await callback.message.edit_text(
            text,
            reply_markup=AdminKeyboards.chats_list(chats, lang)
        )
    except TelegramBadRequest:
        await callback.message.answer(
            text,
            reply_markup=AdminKeyboards.chats_list(chats, lang)
        )


@router.callback_query(F.data.startswith("chats_page:"))
async def chats_page(
    callback: CallbackQuery,
    bot_session: AsyncSession
):
    """Handle chats pagination."""
    page = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    chats_result = await bot_session.execute(
        select(ManagedChat).order_by(ManagedChat.is_primary.desc(), ManagedChat.title)
    )
    chats = list(chats_result.scalars().all())
    total_pages = max(1, (len(chats) + 4) // 5)

    text = get_text("chats_list", lang, page=page + 1, total=total_pages)

    await callback.answer()
    try:
        await callback.message.edit_text(
            text,
            reply_markup=AdminKeyboards.chats_list(chats, lang, page)
        )
    except TelegramBadRequest:
        pass


@router.callback_query(F.data.startswith("chat:") & ~F.data.startswith("chat:new"))
async def view_chat(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """View chat details."""
    chat_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    chat_result = await bot_session.execute(
        select(ManagedChat).where(ManagedChat.id == chat_id)
    )
    chat = chat_result.scalar_one_or_none()

    if not chat:
        await callback.answer("Chat not found")
        return

    await state.set_state(AdminStates.chat_view)
    await state.update_data(chat_id=chat_id)

    active = "Yes" if chat.is_active else "No"
    primary = "Yes" if chat.is_primary else "No"

    text = get_text(
        "chat_info", lang,
        title=chat.title or "N/A",
        id=chat.id,
        type=chat.type,
        active=active,
        primary=primary
    )

    await callback.answer()
    try:
        await callback.message.edit_text(
            text,
            reply_markup=AdminKeyboards.chat_actions(chat, lang)
        )
    except TelegramBadRequest:
        await callback.message.answer(
            text,
            reply_markup=AdminKeyboards.chat_actions(chat, lang)
        )


@router.callback_query(F.data.startswith("chat_primary:"))
async def set_primary_chat(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Set chat as primary (support group)."""
    chat_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    # Remove primary from all
    await bot_session.execute(
        update(ManagedChat).values(is_primary=False)
    )

    # Set new primary
    chat_result = await bot_session.execute(
        select(ManagedChat).where(ManagedChat.id == chat_id)
    )
    chat = chat_result.scalar_one_or_none()

    if chat:
        chat.is_primary = True

        # Update support_group_id in config
        config_result = await bot_session.execute(
            select(BotConfig).where(BotConfig.key == "support_group_id")
        )
        config = config_result.scalar_one_or_none()

        if config:
            config.value = str(chat_id)
        else:
            config = BotConfig(key="support_group_id", value=str(chat_id))
            bot_session.add(config)

        await callback.answer(get_text("chat_set_primary", lang))

        logger.info(f"Chat {chat_id} set as primary support group")

    await view_chat(callback, state, bot_session)


@router.callback_query(F.data.startswith("chat_leave:"))
async def leave_chat(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    bot_session: AsyncSession
):
    """Leave chat."""
    chat_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    chat_result = await bot_session.execute(
        select(ManagedChat).where(ManagedChat.id == chat_id)
    )
    chat = chat_result.scalar_one_or_none()

    if chat:
        # If leaving primary chat, reset support_group_id
        if chat.is_primary:
            config_result = await bot_session.execute(
                select(BotConfig).where(BotConfig.key == "support_group_id")
            )
            config = config_result.scalar_one_or_none()
            if config:
                config.value = ""

        # Try to leave
        try:
            await bot.leave_chat(chat_id)
        except Exception as e:
            logger.warning(f"Could not leave chat {chat_id}: {e}")

        # Update status
        chat.is_active = False
        chat.is_primary = False

        await callback.answer(get_text("chat_left", lang))

        logger.info(f"Bot left chat {chat_id}")

    await show_chats(callback, state, bot_session)
