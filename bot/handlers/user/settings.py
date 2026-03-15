"""User settings handlers."""
import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from bot.states import UserStates
from bot.keyboards import UserKeyboards
from bot.locales import get_text

logger = logging.getLogger(__name__)
router = Router(name="settings")


@router.callback_query(F.data == "settings")
async def show_settings(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Show settings menu."""
    user_id = callback.from_user.id

    result = await bot_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        await callback.answer("Please use /start")
        return

    lang = user.language

    await state.set_state(UserStates.settings)
    await callback.answer()

    try:
        await callback.message.edit_text(
            get_text("settings_menu", lang),
            reply_markup=UserKeyboards.settings_menu(lang)
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("settings_menu", lang),
            reply_markup=UserKeyboards.settings_menu(lang)
        )


@router.callback_query(F.data == "settings:language")
async def change_language(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Show language selection."""
    user_id = callback.from_user.id

    result = await bot_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        await callback.answer("Please use /start")
        return

    lang = user.language

    await state.set_state(UserStates.changing_language)
    await callback.answer()

    try:
        await callback.message.edit_text(
            get_text("select_language", lang),
            reply_markup=UserKeyboards.language_selection()
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("select_language", lang),
            reply_markup=UserKeyboards.language_selection()
        )
