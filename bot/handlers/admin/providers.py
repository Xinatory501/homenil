"""AI providers management handlers."""
import logging
import re

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AIProvider, User
from database.models.user import UserRole
from bot.states import AdminStates
from bot.keyboards import AdminKeyboards
from bot.locales import get_text
from bot.config import settings

logger = logging.getLogger(__name__)
router = Router(name="admin_providers")


async def is_admin(user_id: int, bot_session: AsyncSession) -> bool:
    """Check if user is admin."""
    if user_id in settings.admin_id_list:
        return True
    result = await bot_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    return user and user.role == UserRole.ADMIN.value


@router.callback_query(F.data == "admin:providers")
async def show_providers(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession,
    shared_session: AsyncSession
):
    """Show providers list."""
    user_id = callback.from_user.id

    if not await is_admin(user_id, bot_session):
        await callback.answer(get_text("admin_only", "ru"))
        return

    result = await bot_session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    # Get providers
    providers_result = await shared_session.execute(
        select(AIProvider).order_by(AIProvider.is_default.desc(), AIProvider.display_name)
    )
    providers = list(providers_result.scalars().all())

    await state.set_state(AdminStates.providers_list)
    await callback.answer()

    text = get_text("providers_list", lang)
    if not providers:
        text += "\n\n(empty)"

    try:
        await callback.message.edit_text(
            text,
            reply_markup=AdminKeyboards.providers_list(providers, lang)
        )
    except TelegramBadRequest:
        await callback.message.answer(
            text,
            reply_markup=AdminKeyboards.providers_list(providers, lang)
        )


@router.callback_query(F.data.startswith("providers_page:"))
async def providers_page(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession,
    shared_session: AsyncSession
):
    """Handle providers pagination."""
    page = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    providers_result = await shared_session.execute(
        select(AIProvider).order_by(AIProvider.is_default.desc(), AIProvider.display_name)
    )
    providers = list(providers_result.scalars().all())

    await callback.answer()
    try:
        await callback.message.edit_reply_markup(
            reply_markup=AdminKeyboards.providers_list(providers, lang, page)
        )
    except TelegramBadRequest:
        pass


@router.callback_query(F.data.startswith("provider:") & ~F.data.startswith("provider:add"))
async def view_provider(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession,
    shared_session: AsyncSession
):
    """View provider details."""
    provider_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    provider_result = await shared_session.execute(
        select(AIProvider).where(AIProvider.id == provider_id)
    )
    provider = provider_result.scalar_one_or_none()

    if not provider:
        await callback.answer("Provider not found")
        return

    await state.set_state(AdminStates.provider_view)
    await state.update_data(provider_id=provider_id)

    status = "Active" if provider.is_active else "Inactive"
    default = "Yes" if provider.is_default else "No"

    text = get_text(
        "provider_info", lang,
        name=provider.display_name,
        slug=provider.slug,
        url=provider.base_url,
        status=status,
        default=default
    )

    await callback.answer()
    try:
        await callback.message.edit_text(
            text,
            reply_markup=AdminKeyboards.provider_actions(provider, lang)
        )
    except TelegramBadRequest:
        await callback.message.answer(
            text,
            reply_markup=AdminKeyboards.provider_actions(provider, lang)
        )


@router.callback_query(F.data == "provider:add")
async def add_provider_start(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Start adding provider."""
    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await state.set_state(AdminStates.provider_add_slug)
    await callback.answer()

    try:
        await callback.message.edit_text(
            get_text("enter_provider_slug", lang),
            reply_markup=AdminKeyboards.back_button(lang, "admin:providers")
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("enter_provider_slug", lang),
            reply_markup=AdminKeyboards.back_button(lang, "admin:providers")
        )


@router.message(AdminStates.provider_add_slug)
async def add_provider_slug(
    message: Message,
    state: FSMContext,
    bot_session: AsyncSession,
    shared_session: AsyncSession
):
    """Handle provider slug input."""
    slug = message.text.strip().lower()

    # Validate slug (latin letters, numbers, underscores)
    if not re.match(r'^[a-z0-9_]+$', slug):
        result = await bot_session.execute(select(User).where(User.id == message.from_user.id))
        user = result.scalar_one_or_none()
        lang = user.language if user else "ru"
        await message.answer(
            get_text("enter_provider_slug", lang),
            reply_markup=AdminKeyboards.back_button(lang, "admin:providers")
        )
        return

    # Check uniqueness and generate unique name if needed
    base_slug = slug
    counter = 1
    while True:
        result = await shared_session.execute(
            select(AIProvider).where(AIProvider.slug == slug)
        )
        if not result.scalar_one_or_none():
            break
        counter += 1
        slug = f"{base_slug}_{counter}"

    await state.update_data(provider_slug=slug)
    await state.set_state(AdminStates.provider_add_name)

    result = await bot_session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await message.answer(
        get_text("enter_provider_name", lang),
        reply_markup=AdminKeyboards.back_button(lang, "admin:providers")
    )


@router.message(AdminStates.provider_add_name)
async def add_provider_name(
    message: Message,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Handle provider display name input."""
    name = message.text.strip()

    if not name:
        return

    await state.update_data(provider_name=name)
    await state.set_state(AdminStates.provider_add_url)

    result = await bot_session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await message.answer(
        get_text("enter_provider_url", lang),
        reply_markup=AdminKeyboards.back_button(lang, "admin:providers")
    )


@router.message(AdminStates.provider_add_url)
async def add_provider_url(
    message: Message,
    state: FSMContext,
    bot_session: AsyncSession,
    shared_session: AsyncSession
):
    """Handle provider URL input and create provider."""
    url = message.text.strip()

    if not url:
        return

    result = await bot_session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    data = await state.get_data()

    # Check if this is the first provider
    count_result = await shared_session.execute(select(func.count(AIProvider.id)))
    count = count_result.scalar() or 0

    provider = AIProvider(
        slug=data["provider_slug"],
        display_name=data["provider_name"],
        base_url=url,
        is_active=True,
        is_default=(count == 0)  # First provider is default
    )
    shared_session.add(provider)
    await shared_session.commit()

    await state.clear()
    await message.answer(
        get_text("provider_added", lang),
        reply_markup=AdminKeyboards.back_button(lang, "admin:providers")
    )

    logger.info(f"Provider {provider.slug} created by user {message.from_user.id}")


@router.callback_query(F.data.startswith("provider_toggle:"))
async def toggle_provider(
    callback: CallbackQuery,
    bot_session: AsyncSession,
    shared_session: AsyncSession
):
    """Toggle provider active status."""
    provider_id = int(callback.data.split(":")[1])

    result = await shared_session.execute(
        select(AIProvider).where(AIProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()

    if provider:
        provider.is_active = not provider.is_active
        await shared_session.commit()

    await callback.answer()
    # Refresh view
    await view_provider(callback, None, bot_session, shared_session)


@router.callback_query(F.data.startswith("provider_default:"))
async def set_default_provider(
    callback: CallbackQuery,
    bot_session: AsyncSession,
    shared_session: AsyncSession
):
    """Set provider as default."""
    provider_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    # Remove default from all
    all_providers = await shared_session.execute(select(AIProvider))
    for p in all_providers.scalars():
        p.is_default = (p.id == provider_id)

    await shared_session.commit()
    await callback.answer(get_text("provider_set_default", lang))

    # Refresh view
    await view_provider(callback, None, bot_session, shared_session)


@router.callback_query(F.data.startswith("provider_delete:"))
async def delete_provider(
    callback: CallbackQuery,
    bot_session: AsyncSession,
    shared_session: AsyncSession
):
    """Delete provider."""
    provider_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    provider_result = await shared_session.execute(
        select(AIProvider).where(AIProvider.id == provider_id)
    )
    provider = provider_result.scalar_one_or_none()

    if provider and provider.is_default:
        await callback.answer(get_text("provider_is_default", lang))
        return

    if provider:
        await shared_session.delete(provider)
        await shared_session.commit()
        await callback.answer(get_text("provider_deleted", lang))

    # Return to list
    await show_providers(callback, None, bot_session, shared_session)
