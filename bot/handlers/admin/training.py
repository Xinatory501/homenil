"""Training messages management handlers."""
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, TrainingMessage
from bot.states import AdminStates
from bot.keyboards import AdminKeyboards
from bot.locales import get_text
from bot.services import TrainingService

logger = logging.getLogger(__name__)
router = Router(name="admin_training")


@router.callback_query(F.data == "admin:training")
async def show_training(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Show training messages list."""
    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    service = TrainingService(bot_session)
    messages = await service.get_all_messages()

    total_pages = max(1, (len(messages) + 4) // 5)

    await state.set_state(AdminStates.training_list)
    await callback.answer()

    text = get_text("training_list", lang, page=1, total=total_pages)
    if not messages:
        text += "\n\n(empty)"

    try:
        await callback.message.edit_text(
            text,
            reply_markup=AdminKeyboards.training_list(messages, lang)
        )
    except TelegramBadRequest:
        await callback.message.answer(
            text,
            reply_markup=AdminKeyboards.training_list(messages, lang)
        )


@router.callback_query(F.data.startswith("training_page:"))
async def training_page(
    callback: CallbackQuery,
    bot_session: AsyncSession
):
    """Handle training pagination."""
    page = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    service = TrainingService(bot_session)
    messages = await service.get_all_messages()
    total_pages = max(1, (len(messages) + 4) // 5)

    text = get_text("training_list", lang, page=page + 1, total=total_pages)

    await callback.answer()
    try:
        await callback.message.edit_text(
            text,
            reply_markup=AdminKeyboards.training_list(messages, lang, page)
        )
    except TelegramBadRequest:
        pass


@router.callback_query(F.data.startswith("training:") & ~F.data.startswith("training:add"))
async def view_training(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """View training message details."""
    msg_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    service = TrainingService(bot_session)
    msg = await service.get_message(msg_id)

    if not msg:
        await callback.answer("Message not found")
        return

    await state.set_state(AdminStates.training_view)
    await state.update_data(training_id=msg_id)

    status = "Active" if msg.is_active else "Inactive"
    content_preview = msg.content[:500] + "..." if len(msg.content) > 500 else msg.content

    text = get_text(
        "training_info", lang,
        id=msg.id,
        priority=msg.priority,
        status=status,
        content=content_preview
    )

    await callback.answer()
    try:
        await callback.message.edit_text(
            text,
            reply_markup=AdminKeyboards.training_actions(msg, lang)
        )
    except TelegramBadRequest:
        await callback.message.answer(
            text,
            reply_markup=AdminKeyboards.training_actions(msg, lang)
        )


@router.callback_query(F.data == "training:add")
async def add_training_start(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Start adding training message."""
    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await state.set_state(AdminStates.training_add_text)
    await callback.answer()

    try:
        await callback.message.edit_text(
            get_text("enter_training_text", lang),
            reply_markup=AdminKeyboards.back_button(lang, "admin:training")
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("enter_training_text", lang),
            reply_markup=AdminKeyboards.back_button(lang, "admin:training")
        )


@router.message(AdminStates.training_add_text)
async def add_training_text(
    message: Message,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Handle training text input."""
    text = message.text.strip()
    if not text:
        return

    await state.update_data(training_text=text)
    await state.set_state(AdminStates.training_add_priority)

    result = await bot_session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await message.answer(
        get_text("enter_training_priority", lang),
        reply_markup=AdminKeyboards.back_button(lang, "admin:training")
    )


@router.message(AdminStates.training_add_priority)
async def add_training_priority(
    message: Message,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Handle training priority input and create message."""
    result = await bot_session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    try:
        priority = int(message.text.strip())
        if priority < 1 or priority > 10:
            raise ValueError()
    except ValueError:
        await message.answer(
            get_text("priority_invalid", lang),
            reply_markup=AdminKeyboards.back_button(lang, "admin:training")
        )
        return

    data = await state.get_data()
    service = TrainingService(bot_session)
    await service.create_message(data["training_text"], priority)

    await state.clear()
    await message.answer(
        get_text("training_added", lang),
        reply_markup=AdminKeyboards.back_button(lang, "admin:training")
    )


@router.callback_query(F.data.startswith("training_edit_text:"))
async def edit_training_text_start(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Start editing training text."""
    msg_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await state.set_state(AdminStates.training_edit_text)
    await state.update_data(training_id=msg_id)

    await callback.answer()
    try:
        await callback.message.edit_text(
            get_text("enter_training_text", lang),
            reply_markup=AdminKeyboards.back_button(lang, f"training:{msg_id}")
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("enter_training_text", lang),
            reply_markup=AdminKeyboards.back_button(lang, f"training:{msg_id}")
        )


@router.message(AdminStates.training_edit_text)
async def edit_training_text(
    message: Message,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Handle training text edit."""
    text = message.text.strip()
    if not text:
        return

    result = await bot_session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    data = await state.get_data()
    service = TrainingService(bot_session)
    await service.update_content(data["training_id"], text)

    await state.clear()
    await message.answer(
        get_text("training_updated", lang),
        reply_markup=AdminKeyboards.back_button(lang, "admin:training")
    )


@router.callback_query(F.data.startswith("training_edit_priority:"))
async def edit_training_priority_start(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Start editing training priority."""
    msg_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await state.set_state(AdminStates.training_edit_priority)
    await state.update_data(training_id=msg_id)

    await callback.answer()
    try:
        await callback.message.edit_text(
            get_text("enter_training_priority", lang),
            reply_markup=AdminKeyboards.back_button(lang, f"training:{msg_id}")
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("enter_training_priority", lang),
            reply_markup=AdminKeyboards.back_button(lang, f"training:{msg_id}")
        )


@router.message(AdminStates.training_edit_priority)
async def edit_training_priority(
    message: Message,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Handle training priority edit."""
    result = await bot_session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    try:
        priority = int(message.text.strip())
        if priority < 1 or priority > 10:
            raise ValueError()
    except ValueError:
        data = await state.get_data()
        await message.answer(
            get_text("priority_invalid", lang),
            reply_markup=AdminKeyboards.back_button(lang, f"training:{data['training_id']}")
        )
        return

    data = await state.get_data()
    service = TrainingService(bot_session)
    await service.update_priority(data["training_id"], priority)

    await state.clear()
    await message.answer(
        get_text("training_updated", lang),
        reply_markup=AdminKeyboards.back_button(lang, "admin:training")
    )


@router.callback_query(F.data.startswith("training_toggle:"))
async def toggle_training(
    callback: CallbackQuery,
    bot_session: AsyncSession
):
    """Toggle training message active status."""
    msg_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    service = TrainingService(bot_session)
    new_status = await service.toggle_active(msg_id)

    if new_status is not None:
        if new_status:
            await callback.answer(get_text("training_activated", lang))
        else:
            await callback.answer(get_text("training_deactivated", lang))

    await view_training(callback, None, bot_session)


@router.callback_query(F.data.startswith("training_delete:"))
async def delete_training(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Delete training message."""
    msg_id = int(callback.data.split(":")[1])

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    service = TrainingService(bot_session)
    await service.delete_message(msg_id)

    await callback.answer(get_text("training_deleted", lang))
    await show_training(callback, state, bot_session)
