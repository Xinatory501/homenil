"""User management handlers."""
import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, AdminAction
from database.models.user import UserRole
from bot.states import AdminStates
from bot.keyboards import AdminKeyboards
from bot.locales import get_text
from bot.config import settings

logger = logging.getLogger(__name__)
router = Router(name="admin_users")


@router.callback_query(F.data == "admin:user")
async def user_search_start(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Start user search."""
    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await state.set_state(AdminStates.user_search)
    await callback.answer()

    try:
        await callback.message.edit_text(
            get_text("enter_user_search", lang),
            reply_markup=AdminKeyboards.back_button(lang, "admin:menu")
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("enter_user_search", lang),
            reply_markup=AdminKeyboards.back_button(lang, "admin:menu")
        )


@router.message(AdminStates.user_search)
async def search_user(
    message: Message,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Handle user search."""
    query = message.text.strip()

    result = await bot_session.execute(select(User).where(User.id == message.from_user.id))
    admin = result.scalar_one_or_none()
    lang = admin.language if admin else "ru"

    found_user = None

    # Try by ID
    if query.isdigit():
        result = await bot_session.execute(
            select(User).where(User.id == int(query))
        )
        found_user = result.scalar_one_or_none()

    # Try by @username
    if not found_user and query.startswith("@"):
        username = query[1:]
        result = await bot_session.execute(
            select(User).where(User.username == username)
        )
        found_user = result.scalar_one_or_none()

    # Try by username without @
    if not found_user:
        result = await bot_session.execute(
            select(User).where(User.username == query)
        )
        found_user = result.scalar_one_or_none()

    if found_user:
        await _show_user_info(message, found_user, lang)
        await state.set_state(AdminStates.user_view)
        await state.update_data(target_user_id=found_user.id)
        return

    # Search for similar usernames
    result = await bot_session.execute(
        select(User).where(User.username.ilike(f"%{query}%")).limit(5)
    )
    similar = list(result.scalars().all())

    if similar:
        text = get_text("similar_users", lang) + "\n\n"
        for u in similar:
            text += f"@{u.username} (ID: {u.id})\n"
        await message.answer(
            text,
            reply_markup=AdminKeyboards.back_button(lang, "admin:menu")
        )
    else:
        await message.answer(
            get_text("user_not_found", lang),
            reply_markup=AdminKeyboards.back_button(lang, "admin:menu")
        )


async def _show_user_info(
    message_or_callback,
    user: User,
    lang: str
):
    """Show user information card."""
    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "N/A"
    username = user.username or "N/A"
    banned = "Yes" if user.is_banned else "No"
    if user.is_banned and user.ban_until:
        banned += f" (until {user.ban_until.strftime('%Y-%m-%d %H:%M')})"

    # Format topic link
    topic = "N/A"
    if user.thread_id:
        topic = f"#{user.thread_id}"

    text = get_text(
        "user_info", lang,
        id=user.id,
        username=username,
        name=name,
        language=user.language,
        role=user.role,
        messages=user.message_count,
        sessions=user.session_count,
        banned=banned,
        topic=topic,
        created=user.created_at.strftime("%Y-%m-%d %H:%M")
    )

    is_admin = user.role == UserRole.ADMIN.value
    keyboard = AdminKeyboards.user_actions(user.id, user.is_banned, is_admin, lang)

    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(text, reply_markup=keyboard)
    else:
        try:
            await message_or_callback.message.edit_text(text, reply_markup=keyboard)
        except TelegramBadRequest:
            await message_or_callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("user_ban:"))
async def ban_user(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Ban user."""
    target_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    admin = result.scalar_one_or_none()
    lang = admin.language if admin else "ru"

    result = await bot_session.execute(select(User).where(User.id == target_id))
    target = result.scalar_one_or_none()

    if target:
        target.is_banned = True
        target.ban_reason = "Banned by admin"

        # Log action
        action = AdminAction(
            admin_id=callback.from_user.id,
            target_user_id=target_id,
            action="ban",
            details="User banned"
        )
        bot_session.add(action)

        await callback.answer(get_text("user_banned", lang))
        await _show_user_info(callback, target, lang)

        logger.info(f"User {target_id} banned by admin {callback.from_user.id}")


@router.callback_query(F.data.startswith("user_unban:"))
async def unban_user(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Unban user."""
    target_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    admin = result.scalar_one_or_none()
    lang = admin.language if admin else "ru"

    result = await bot_session.execute(select(User).where(User.id == target_id))
    target = result.scalar_one_or_none()

    if target:
        target.is_banned = False
        target.ban_until = None
        target.ban_reason = None

        action = AdminAction(
            admin_id=callback.from_user.id,
            target_user_id=target_id,
            action="unban",
            details="User unbanned"
        )
        bot_session.add(action)

        await callback.answer(get_text("user_unbanned", lang))
        await _show_user_info(callback, target, lang)

        logger.info(f"User {target_id} unbanned by admin {callback.from_user.id}")


@router.callback_query(F.data.startswith("user_grant:"))
async def grant_admin(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Grant admin rights."""
    target_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    admin = result.scalar_one_or_none()
    lang = admin.language if admin else "ru"

    # Check if caller is in env admins (only env admins can grant admin)
    if callback.from_user.id not in settings.admin_id_list:
        await callback.answer("Only primary admins can grant admin rights")
        return

    result = await bot_session.execute(select(User).where(User.id == target_id))
    target = result.scalar_one_or_none()

    if target:
        target.role = UserRole.ADMIN.value

        action = AdminAction(
            admin_id=callback.from_user.id,
            target_user_id=target_id,
            action="grant_admin",
            details="Admin rights granted"
        )
        bot_session.add(action)

        await callback.answer(get_text("admin_granted", lang))
        await _show_user_info(callback, target, lang)

        logger.info(f"User {target_id} granted admin by {callback.from_user.id}")


@router.callback_query(F.data.startswith("user_revoke:"))
async def revoke_admin(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Revoke admin rights."""
    target_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    admin = result.scalar_one_or_none()
    lang = admin.language if admin else "ru"

    # Check if caller is in env admins
    if callback.from_user.id not in settings.admin_id_list:
        await callback.answer("Only primary admins can revoke admin rights")
        return

    # Prevent revoking env admin
    if target_id in settings.admin_id_list:
        await callback.answer("Cannot revoke primary admin")
        return

    result = await bot_session.execute(select(User).where(User.id == target_id))
    target = result.scalar_one_or_none()

    if target:
        target.role = UserRole.USER.value

        action = AdminAction(
            admin_id=callback.from_user.id,
            target_user_id=target_id,
            action="revoke_admin",
            details="Admin rights revoked"
        )
        bot_session.add(action)

        await callback.answer(get_text("admin_revoked", lang))
        await _show_user_info(callback, target, lang)

        logger.info(f"User {target_id} admin revoked by {callback.from_user.id}")
