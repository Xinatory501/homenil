"""AI API keys management handlers."""
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AIProvider, AIKey, User
from database.models.user import UserRole
from bot.states import AdminStates
from bot.keyboards import AdminKeyboards
from bot.locales import get_text
from bot.config import settings

logger = logging.getLogger(__name__)
router = Router(name="admin_keys")


async def is_admin(user_id: int, bot_session: AsyncSession) -> bool:
    """Check if user is admin."""
    if user_id in settings.admin_id_list:
        return True
    result = await bot_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    return user and user.role == UserRole.ADMIN.value


@router.callback_query(F.data == "admin:keys")
async def select_provider_for_keys(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession,
    shared_session: AsyncSession
):
    """Show provider selection for key management."""
    # Redirect to providers list - keys are managed per provider
    await callback.answer("Select a provider first")

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    providers_result = await shared_session.execute(
        select(AIProvider).order_by(AIProvider.is_default.desc(), AIProvider.display_name)
    )
    providers = list(providers_result.scalars().all())

    try:
        await callback.message.edit_text(
            get_text("providers_list", lang) + "\n\nSelect provider to manage keys:",
            reply_markup=AdminKeyboards.providers_list(providers, lang)
        )
    except TelegramBadRequest:
        pass


@router.callback_query(F.data.startswith("keys:"))
async def show_keys(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession,
    shared_session: AsyncSession
):
    """Show keys for provider."""
    provider_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    # Get provider
    provider_result = await shared_session.execute(
        select(AIProvider).where(AIProvider.id == provider_id)
    )
    provider = provider_result.scalar_one_or_none()

    if not provider:
        await callback.answer("Provider not found")
        return

    # Get keys
    keys_result = await shared_session.execute(
        select(AIKey).where(AIKey.provider_id == provider_id)
    )
    keys = list(keys_result.scalars().all())

    await state.set_state(AdminStates.keys_list)
    await state.update_data(provider_id=provider_id)

    text = get_text("keys_list", lang, provider=provider.display_name)
    if not keys:
        text += "\n\n(empty)"

    await callback.answer()
    try:
        await callback.message.edit_text(
            text,
            reply_markup=AdminKeyboards.keys_list(keys, provider_id, lang)
        )
    except TelegramBadRequest:
        await callback.message.answer(
            text,
            reply_markup=AdminKeyboards.keys_list(keys, provider_id, lang)
        )


@router.callback_query(F.data.startswith("key:") & ~F.data.startswith("key:add:"))
async def view_key(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession,
    shared_session: AsyncSession
):
    """View key details."""
    key_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    key_result = await shared_session.execute(
        select(AIKey).where(AIKey.id == key_id)
    )
    key = key_result.scalar_one_or_none()

    if not key:
        await callback.answer("Key not found")
        return

    await state.set_state(AdminStates.key_view)
    await state.update_data(key_id=key_id)

    status = "Active" if key.is_active else "Inactive"
    limit = str(key.requests_limit) if key.requests_limit else "unlimited"
    error = key.last_error or "None"
    if len(error) > 200:
        error = error[:200] + "..."

    text = get_text(
        "key_info", lang,
        masked=key.masked_key,
        status=status,
        requests=key.requests_made,
        limit=limit,
        error=error
    )

    await callback.answer()
    try:
        await callback.message.edit_text(
            text,
            reply_markup=AdminKeyboards.key_actions(key, lang)
        )
    except TelegramBadRequest:
        await callback.message.answer(
            text,
            reply_markup=AdminKeyboards.key_actions(key, lang)
        )


@router.callback_query(F.data.startswith("key:add:"))
async def add_key_start(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Start adding key."""
    provider_id = int(callback.data.split(":")[2])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await state.set_state(AdminStates.key_add)
    await state.update_data(provider_id=provider_id)

    await callback.answer()
    try:
        await callback.message.edit_text(
            get_text("enter_api_key", lang),
            reply_markup=AdminKeyboards.back_button(lang, f"keys:{provider_id}")
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("enter_api_key", lang),
            reply_markup=AdminKeyboards.back_button(lang, f"keys:{provider_id}")
        )


@router.message(AdminStates.key_add)
async def add_key(
    message: Message,
    state: FSMContext,
    bot_session: AsyncSession,
    shared_session: AsyncSession
):
    """Handle API key input."""
    api_key = message.text.strip()

    result = await bot_session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    if not api_key:
        await message.answer(get_text("key_empty", lang))
        return

    data = await state.get_data()
    provider_id = data.get("provider_id")

    key = AIKey(
        provider_id=provider_id,
        api_key=api_key,
        is_active=True
    )
    shared_session.add(key)
    await shared_session.commit()

    await state.clear()
    await message.answer(
        get_text("key_added", lang),
        reply_markup=AdminKeyboards.back_button(lang, f"keys:{provider_id}")
    )

    logger.info(f"API key added for provider {provider_id}")


@router.callback_query(F.data.startswith("key_toggle:"))
async def toggle_key(
    callback: CallbackQuery,
    bot_session: AsyncSession,
    shared_session: AsyncSession
):
    """Toggle key active status."""
    key_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    key_result = await shared_session.execute(
        select(AIKey).where(AIKey.id == key_id)
    )
    key = key_result.scalar_one_or_none()

    if key:
        key.is_active = not key.is_active
        await shared_session.commit()

        if key.is_active:
            await callback.answer(get_text("key_activated", lang))
        else:
            await callback.answer(get_text("key_deactivated", lang))

    # Refresh view
    await view_key(callback, None, bot_session, shared_session)


@router.callback_query(F.data.startswith("key_delete:"))
async def delete_key(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession,
    shared_session: AsyncSession
):
    """Delete key."""
    key_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    key_result = await shared_session.execute(
        select(AIKey).where(AIKey.id == key_id)
    )
    key = key_result.scalar_one_or_none()

    if key:
        provider_id = key.provider_id
        await shared_session.delete(key)
        await shared_session.commit()
        await callback.answer(get_text("key_deleted", lang))

        # Return to keys list
        callback.data = f"keys:{provider_id}"
        await show_keys(callback, state, bot_session, shared_session)
