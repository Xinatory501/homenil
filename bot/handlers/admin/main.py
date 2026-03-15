"""Admin main menu handlers."""
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from database.models.user import UserRole
from bot.states import AdminStates
from bot.keyboards import AdminKeyboards
from bot.locales import get_text
from bot.config import settings

logger = logging.getLogger(__name__)
router = Router(name="admin_main")


async def is_admin(user_id: int, bot_session: AsyncSession) -> bool:
    """Check if user is admin."""
    # Check env admins
    if user_id in settings.admin_id_list:
        return True

    # Check DB role
    result = await bot_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    return user and user.role == UserRole.ADMIN.value


@router.message(Command("admin"))
async def cmd_admin(
    message: Message,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Handle /admin command."""
    user_id = message.from_user.id

    if not await is_admin(user_id, bot_session):
        await message.answer(get_text("admin_only", "ru"))
        return

    # Ensure admin user exists in DB
    result = await bot_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            role=UserRole.ADMIN.value
        )
        bot_session.add(user)
        await bot_session.flush()

    lang = user.language

    await state.set_state(AdminStates.main_menu)
    await message.answer(
        get_text("admin_menu", lang),
        reply_markup=AdminKeyboards.main_menu(lang)
    )


@router.callback_query(F.data == "admin:menu")
async def show_admin_menu(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Show admin main menu."""
    user_id = callback.from_user.id

    if not await is_admin(user_id, bot_session):
        await callback.answer(get_text("admin_only", "ru"))
        return

    result = await bot_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await state.set_state(AdminStates.main_menu)
    await callback.answer()

    try:
        await callback.message.edit_text(
            get_text("admin_menu", lang),
            reply_markup=AdminKeyboards.main_menu(lang)
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("admin_menu", lang),
            reply_markup=AdminKeyboards.main_menu(lang)
        )
