"""AI models management handlers."""
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AIProvider, AIModel, AIKey, User
from database.models.user import UserRole
from bot.states import AdminStates
from bot.keyboards import AdminKeyboards
from bot.locales import get_text
from bot.config import settings

logger = logging.getLogger(__name__)
router = Router(name="admin_models")


@router.callback_query(F.data == "admin:models")
async def select_provider_for_models(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession,
    shared_session: AsyncSession
):
    """Show provider selection for model management."""
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
            get_text("providers_list", lang) + "\n\nSelect provider to manage models:",
            reply_markup=AdminKeyboards.providers_list(providers, lang)
        )
    except TelegramBadRequest:
        pass


@router.callback_query(F.data.startswith("models:"))
async def show_models(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession,
    shared_session: AsyncSession
):
    """Show models for provider."""
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

    models_result = await shared_session.execute(
        select(AIModel).where(AIModel.provider_id == provider_id).order_by(AIModel.is_default.desc())
    )
    models = list(models_result.scalars().all())

    await state.set_state(AdminStates.models_list)
    await state.update_data(provider_id=provider_id)

    text = get_text("models_list", lang, provider=provider.display_name)
    if not models:
        text += "\n\n(empty)"

    await callback.answer()
    try:
        await callback.message.edit_text(
            text,
            reply_markup=AdminKeyboards.models_list(models, provider_id, lang)
        )
    except TelegramBadRequest:
        await callback.message.answer(
            text,
            reply_markup=AdminKeyboards.models_list(models, provider_id, lang)
        )


@router.callback_query(F.data.startswith("model:") & ~F.data.startswith("model:add:"))
async def view_model(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession,
    shared_session: AsyncSession
):
    """View model details."""
    model_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    model_result = await shared_session.execute(
        select(AIModel).where(AIModel.id == model_id)
    )
    model = model_result.scalar_one_or_none()

    if not model:
        await callback.answer("Model not found")
        return

    # Count total models for provider
    count_result = await shared_session.execute(
        select(func.count(AIModel.id)).where(AIModel.provider_id == model.provider_id)
    )
    total_models = count_result.scalar() or 0

    await state.set_state(AdminStates.model_view)
    await state.update_data(model_id=model_id)

    status = "Active" if model.is_active else "Inactive"
    default = "Yes" if model.is_default else "No"
    last_used = model.last_used_at.strftime("%Y-%m-%d %H:%M") if model.last_used_at else "Never"

    text = get_text(
        "model_info", lang,
        name=model.model_name,
        display=model.display_name,
        status=status,
        default=default,
        errors=model.error_count,
        last_used=last_used
    )

    if model.last_error:
        error_preview = model.last_error[:200] + "..." if len(model.last_error) > 200 else model.last_error
        text += f"\n\nLast error:\n{error_preview}"

    await callback.answer()
    try:
        await callback.message.edit_text(
            text,
            reply_markup=AdminKeyboards.model_actions(model, total_models, lang)
        )
    except TelegramBadRequest:
        await callback.message.answer(
            text,
            reply_markup=AdminKeyboards.model_actions(model, total_models, lang)
        )


@router.callback_query(F.data.startswith("model:add:"))
async def add_model_start(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Start adding model."""
    provider_id = int(callback.data.split(":")[2])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await state.set_state(AdminStates.model_add_name)
    await state.update_data(provider_id=provider_id)

    await callback.answer()
    try:
        await callback.message.edit_text(
            get_text("enter_model_name", lang),
            reply_markup=AdminKeyboards.back_button(lang, f"models:{provider_id}")
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("enter_model_name", lang),
            reply_markup=AdminKeyboards.back_button(lang, f"models:{provider_id}")
        )


@router.message(AdminStates.model_add_name)
async def add_model_name(
    message: Message,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Handle model name input."""
    model_name = message.text.strip()

    if not model_name:
        return

    await state.update_data(model_name=model_name)
    await state.set_state(AdminStates.model_add_display)

    result = await bot_session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    data = await state.get_data()
    provider_id = data.get("provider_id")

    await message.answer(
        get_text("enter_model_display", lang),
        reply_markup=AdminKeyboards.back_button(lang, f"models:{provider_id}")
    )


@router.message(AdminStates.model_add_display)
async def add_model_display(
    message: Message,
    state: FSMContext,
    bot_session: AsyncSession,
    shared_session: AsyncSession
):
    """Handle model display name input and create model."""
    display_name = message.text.strip()

    if not display_name:
        return

    result = await bot_session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    data = await state.get_data()
    provider_id = data.get("provider_id")

    # Check if this is the first model for provider
    count_result = await shared_session.execute(
        select(func.count(AIModel.id)).where(AIModel.provider_id == provider_id)
    )
    count = count_result.scalar() or 0

    model = AIModel(
        provider_id=provider_id,
        model_name=data["model_name"],
        display_name=display_name,
        is_active=True,
        is_default=(count == 0)
    )
    shared_session.add(model)
    await shared_session.commit()

    await state.clear()
    await message.answer(
        get_text("model_added", lang),
        reply_markup=AdminKeyboards.back_button(lang, f"models:{provider_id}")
    )

    logger.info(f"Model {model.model_name} created for provider {provider_id}")


@router.callback_query(F.data.startswith("model_toggle:"))
async def toggle_model(
    callback: CallbackQuery,
    bot_session: AsyncSession,
    shared_session: AsyncSession
):
    """Toggle model active status."""
    model_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    model_result = await shared_session.execute(
        select(AIModel).where(AIModel.id == model_id)
    )
    model = model_result.scalar_one_or_none()

    if model:
        model.is_active = not model.is_active
        await shared_session.commit()

        if model.is_active:
            await callback.answer(get_text("model_activated", lang))
        else:
            await callback.answer(get_text("model_deactivated", lang))

    await view_model(callback, None, bot_session, shared_session)


@router.callback_query(F.data.startswith("model_default:"))
async def set_default_model(
    callback: CallbackQuery,
    bot_session: AsyncSession,
    shared_session: AsyncSession
):
    """Set model as default."""
    model_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    model_result = await shared_session.execute(
        select(AIModel).where(AIModel.id == model_id)
    )
    model = model_result.scalar_one_or_none()

    if model:
        # Remove default from all models of same provider
        all_models = await shared_session.execute(
            select(AIModel).where(AIModel.provider_id == model.provider_id)
        )
        for m in all_models.scalars():
            m.is_default = (m.id == model_id)

        await shared_session.commit()
        await callback.answer(get_text("model_set_default", lang))

    await view_model(callback, None, bot_session, shared_session)


@router.callback_query(F.data.startswith("model_delete:"))
async def delete_model(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession,
    shared_session: AsyncSession
):
    """Delete model."""
    model_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    model_result = await shared_session.execute(
        select(AIModel).where(AIModel.id == model_id)
    )
    model = model_result.scalar_one_or_none()

    if model:
        # Check if last model
        count_result = await shared_session.execute(
            select(func.count(AIModel.id)).where(AIModel.provider_id == model.provider_id)
        )
        count = count_result.scalar() or 0

        if count <= 1:
            await callback.answer(get_text("model_is_last", lang))
            return

        provider_id = model.provider_id
        await shared_session.delete(model)
        await shared_session.commit()
        await callback.answer(get_text("model_deleted", lang))

        callback.data = f"models:{provider_id}"
        await show_models(callback, state, bot_session, shared_session)


# Local AI wizard
@router.callback_query(F.data == "admin:local_ai")
async def local_ai_start(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Start local AI wizard."""
    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await state.set_state(AdminStates.local_ai_url)
    await callback.answer()

    try:
        await callback.message.edit_text(
            get_text("local_ai_wizard", lang) + "\n\n" + get_text("enter_local_base_url", lang),
            reply_markup=AdminKeyboards.back_button(lang, "admin:menu")
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("local_ai_wizard", lang) + "\n\n" + get_text("enter_local_base_url", lang),
            reply_markup=AdminKeyboards.back_button(lang, "admin:menu")
        )


@router.message(AdminStates.local_ai_url)
async def local_ai_url(message: Message, state: FSMContext, bot_session: AsyncSession):
    """Handle local AI URL input."""
    url = message.text.strip()
    if not url:
        return

    await state.update_data(local_url=url)
    await state.set_state(AdminStates.local_ai_model)

    result = await bot_session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await message.answer(
        get_text("enter_local_model_name", lang),
        reply_markup=AdminKeyboards.back_button(lang, "admin:menu")
    )


@router.message(AdminStates.local_ai_model)
async def local_ai_model(message: Message, state: FSMContext, bot_session: AsyncSession):
    """Handle local AI model name input."""
    model_name = message.text.strip()
    if not model_name:
        return

    await state.update_data(local_model=model_name)
    await state.set_state(AdminStates.local_ai_provider)

    result = await bot_session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await message.answer(
        get_text("enter_local_provider_name", lang),
        reply_markup=AdminKeyboards.back_button(lang, "admin:menu")
    )


@router.message(AdminStates.local_ai_provider)
async def local_ai_provider(message: Message, state: FSMContext, bot_session: AsyncSession):
    """Handle local AI provider name input."""
    provider_name = message.text.strip()
    if not provider_name:
        return

    await state.update_data(local_provider=provider_name)
    await state.set_state(AdminStates.local_ai_key)

    result = await bot_session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await message.answer(
        get_text("enter_local_api_key", lang),
        reply_markup=AdminKeyboards.back_button(lang, "admin:menu")
    )


@router.message(AdminStates.local_ai_key)
async def local_ai_key(
    message: Message,
    state: FSMContext,
    bot_session: AsyncSession,
    shared_session: AsyncSession
):
    """Handle local AI API key input and create everything."""
    api_key = message.text.strip()
    if not api_key:
        api_key = "-"

    result = await bot_session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    data = await state.get_data()

    # Create unique slug
    base_slug = data["local_provider"].lower().replace(" ", "_")
    slug = base_slug
    counter = 1
    while True:
        check = await shared_session.execute(
            select(AIProvider).where(AIProvider.slug == slug)
        )
        if not check.scalar_one_or_none():
            break
        counter += 1
        slug = f"{base_slug}_{counter}"

    # Check if first provider
    count_result = await shared_session.execute(select(func.count(AIProvider.id)))
    is_first = (count_result.scalar() or 0) == 0

    # Create provider
    provider = AIProvider(
        slug=slug,
        display_name=data["local_provider"],
        base_url=data["local_url"],
        is_active=True,
        is_default=is_first
    )
    shared_session.add(provider)
    await shared_session.flush()

    # Create key
    key = AIKey(
        provider_id=provider.id,
        api_key=api_key,
        is_active=True
    )
    shared_session.add(key)

    # Create model
    model = AIModel(
        provider_id=provider.id,
        model_name=data["local_model"],
        display_name=data["local_model"],
        is_active=True,
        is_default=True
    )
    shared_session.add(model)

    await shared_session.commit()
    await state.clear()

    await message.answer(
        get_text("local_ai_added", lang, provider=data["local_provider"], model=data["local_model"]),
        reply_markup=AdminKeyboards.back_button(lang, "admin:menu")
    )

    logger.info(f"Local AI setup complete: provider={slug}, model={data['local_model']}")
