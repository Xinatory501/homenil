"""Antiflood settings handlers."""
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, BotConfig
from bot.states import AdminStates
from bot.keyboards import AdminKeyboards
from bot.locales import get_text
from bot.config import settings

logger = logging.getLogger(__name__)
router = Router(name="admin_antiflood")


async def _get_antiflood_settings(bot_session: AsyncSession) -> dict:
    """Get current antiflood settings."""
    result = {}
    for key, default in [
        ("antiflood_threshold", settings.antiflood_threshold),
        ("antiflood_time_window", settings.antiflood_time_window),
        ("autoban_duration", settings.autoban_duration),
    ]:
        config_result = await bot_session.execute(
            select(BotConfig).where(BotConfig.key == key)
        )
        config = config_result.scalar_one_or_none()
        result[key] = int(config.value) if config else default
    return result


@router.callback_query(F.data == "admin:antiflood")
async def show_antiflood(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Show antiflood settings."""
    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    settings_data = await _get_antiflood_settings(bot_session)

    await state.set_state(AdminStates.antiflood_menu)
    await callback.answer()

    text = get_text(
        "antiflood_settings", lang,
        threshold=settings_data["antiflood_threshold"],
        window=settings_data["antiflood_time_window"],
        duration=settings_data["autoban_duration"]
    )

    try:
        await callback.message.edit_text(
            text,
            reply_markup=AdminKeyboards.antiflood_menu(lang)
        )
    except TelegramBadRequest:
        await callback.message.answer(
            text,
            reply_markup=AdminKeyboards.antiflood_menu(lang)
        )


@router.callback_query(F.data == "antiflood:threshold")
async def edit_threshold_start(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Start editing threshold."""
    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await state.set_state(AdminStates.antiflood_threshold)
    await callback.answer()

    try:
        await callback.message.edit_text(
            get_text("enter_threshold", lang),
            reply_markup=AdminKeyboards.back_button(lang, "admin:antiflood")
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("enter_threshold", lang),
            reply_markup=AdminKeyboards.back_button(lang, "admin:antiflood")
        )


@router.message(AdminStates.antiflood_threshold)
async def edit_threshold(
    message: Message,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Handle threshold input."""
    result = await bot_session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    try:
        value = int(message.text.strip())
        if value < 1 or value > 1000:
            raise ValueError()
    except ValueError:
        await message.answer(
            get_text("invalid_number", lang) + " (1-1000)",
            reply_markup=AdminKeyboards.back_button(lang, "admin:antiflood")
        )
        return

    # Save to config
    config_result = await bot_session.execute(
        select(BotConfig).where(BotConfig.key == "antiflood_threshold")
    )
    config = config_result.scalar_one_or_none()

    if config:
        config.value = str(value)
    else:
        config = BotConfig(key="antiflood_threshold", value=str(value))
        bot_session.add(config)

    await state.clear()
    await message.answer(
        get_text("antiflood_updated", lang),
        reply_markup=AdminKeyboards.back_button(lang, "admin:antiflood")
    )


@router.callback_query(F.data == "antiflood:window")
async def edit_window_start(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Start editing time window."""
    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await state.set_state(AdminStates.antiflood_window)
    await callback.answer()

    try:
        await callback.message.edit_text(
            get_text("enter_window", lang),
            reply_markup=AdminKeyboards.back_button(lang, "admin:antiflood")
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("enter_window", lang),
            reply_markup=AdminKeyboards.back_button(lang, "admin:antiflood")
        )


@router.message(AdminStates.antiflood_window)
async def edit_window(
    message: Message,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Handle window input."""
    result = await bot_session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    try:
        value = int(message.text.strip())
        if value < 1 or value > 3600:
            raise ValueError()
    except ValueError:
        await message.answer(
            get_text("invalid_number", lang) + " (1-3600)",
            reply_markup=AdminKeyboards.back_button(lang, "admin:antiflood")
        )
        return

    config_result = await bot_session.execute(
        select(BotConfig).where(BotConfig.key == "antiflood_time_window")
    )
    config = config_result.scalar_one_or_none()

    if config:
        config.value = str(value)
    else:
        config = BotConfig(key="antiflood_time_window", value=str(value))
        bot_session.add(config)

    await state.clear()
    await message.answer(
        get_text("antiflood_updated", lang),
        reply_markup=AdminKeyboards.back_button(lang, "admin:antiflood")
    )


@router.callback_query(F.data == "antiflood:duration")
async def edit_duration_start(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Start editing ban duration."""
    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await state.set_state(AdminStates.antiflood_duration)
    await callback.answer()

    try:
        await callback.message.edit_text(
            get_text("enter_duration", lang),
            reply_markup=AdminKeyboards.back_button(lang, "admin:antiflood")
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("enter_duration", lang),
            reply_markup=AdminKeyboards.back_button(lang, "admin:antiflood")
        )


@router.message(AdminStates.antiflood_duration)
async def edit_duration(
    message: Message,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Handle duration input."""
    result = await bot_session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    try:
        value = int(message.text.strip())
        if value < 60 or value > 86400:
            raise ValueError()
    except ValueError:
        await message.answer(
            get_text("invalid_number", lang) + " (60-86400)",
            reply_markup=AdminKeyboards.back_button(lang, "admin:antiflood")
        )
        return

    config_result = await bot_session.execute(
        select(BotConfig).where(BotConfig.key == "autoban_duration")
    )
    config = config_result.scalar_one_or_none()

    if config:
        config.value = str(value)
    else:
        config = BotConfig(key="autoban_duration", value=str(value))
        bot_session.add(config)

    await state.clear()
    await message.answer(
        get_text("antiflood_updated", lang),
        reply_markup=AdminKeyboards.back_button(lang, "admin:antiflood")
    )
