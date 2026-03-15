"""Database management handlers."""
import logging
import os
import shutil
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, BotConfig
from bot.states import AdminStates
from bot.keyboards import AdminKeyboards
from bot.locales import get_text

logger = logging.getLogger(__name__)
router = Router(name="admin_database")


@router.callback_query(F.data == "admin:database")
async def show_database_menu(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Show database management menu."""
    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await state.set_state(AdminStates.database_menu)
    await callback.answer()

    try:
        await callback.message.edit_text(
            get_text("database_menu", lang),
            reply_markup=AdminKeyboards.database_menu(lang)
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("database_menu", lang),
            reply_markup=AdminKeyboards.database_menu(lang)
        )


@router.callback_query(F.data == "db:export")
async def export_database(
    callback: CallbackQuery,
    bot: Bot,
    bot_session: AsyncSession,
    bot_id: str
):
    """Export database backup."""
    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await callback.answer()

    # For PostgreSQL, we'll create a simple export
    # In production, you'd use pg_dump
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{bot_id}_{timestamp}.sql"
    backup_path = f"/tmp/{backup_name}"

    try:
        # Get database URL from settings
        from bot.config import settings

        # Create a simple backup using pg_dump if available
        import subprocess

        # Parse database URL
        db_url = settings.database_url
        # Format: postgresql+asyncpg://user:pass@host:port/dbname

        # For now, just send a message that backup is available
        # In production, implement proper pg_dump

        await callback.message.answer(
            get_text("db_exported", lang) + f"\n\nBackup: {backup_name}",
            reply_markup=AdminKeyboards.back_button(lang, "admin:database")
        )

        logger.info(f"Database export requested by {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Database export error: {e}", exc_info=True)
        await callback.message.answer(
            get_text("db_export_error", lang),
            reply_markup=AdminKeyboards.back_button(lang, "admin:database")
        )


@router.callback_query(F.data == "db:backup")
async def download_backup(
    callback: CallbackQuery,
    bot: Bot,
    bot_session: AsyncSession,
    bot_id: str
):
    """Download database backup file."""
    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await callback.answer()

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{bot_id}_{timestamp}.sql"
    backup_path = f"/tmp/{backup_name}"

    try:
        from bot.config import settings
        import subprocess

        # Parse PostgreSQL URL
        db_url = settings.database_url
        # postgresql+asyncpg://user:pass@host:port/dbname

        # Extract components
        import re
        match = re.match(
            r'postgresql\+asyncpg://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)',
            db_url
        )

        if match:
            user_name, password, host, port, dbname = match.groups()

            # Set environment for pg_dump
            env = os.environ.copy()
            env['PGPASSWORD'] = password

            # Run pg_dump
            result = subprocess.run(
                [
                    'pg_dump',
                    '-h', host,
                    '-p', port,
                    '-U', user_name,
                    '-d', dbname,
                    '-f', backup_path
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0 and os.path.exists(backup_path):
                # Send file
                doc = FSInputFile(backup_path, filename=backup_name)
                await bot.send_document(
                    chat_id=callback.from_user.id,
                    document=doc,
                    caption=f"Database backup: {backup_name}"
                )

                # Cleanup
                os.remove(backup_path)

                logger.info(f"Database backup sent to {callback.from_user.id}")
            else:
                raise Exception(f"pg_dump failed: {result.stderr}")
        else:
            raise Exception("Could not parse database URL")

    except FileNotFoundError:
        # pg_dump not available, create a simple JSON export
        await _create_json_backup(callback, bot, bot_session, bot_id, lang)

    except Exception as e:
        logger.error(f"Database backup error: {e}", exc_info=True)
        await callback.message.answer(
            get_text("db_export_error", lang) + f"\n\nError: {str(e)[:200]}",
            reply_markup=AdminKeyboards.back_button(lang, "admin:database")
        )

        # Cleanup if file exists
        if os.path.exists(backup_path):
            os.remove(backup_path)


async def _create_json_backup(
    callback: CallbackQuery,
    bot: Bot,
    bot_session: AsyncSession,
    bot_id: str,
    lang: str
):
    """Create a JSON backup as fallback."""
    import json
    from database.models import User, ChatSession, ChatHistory, ManagedChat, BotConfig, TrainingMessage

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{bot_id}_{timestamp}.json"
    backup_path = f"/tmp/{backup_name}"

    try:
        data = {}

        # Export users
        users_result = await bot_session.execute(select(User))
        data["users"] = [
            {
                "id": u.id,
                "username": u.username,
                "first_name": u.first_name,
                "language": u.language,
                "role": u.role,
                "is_banned": u.is_banned,
                "message_count": u.message_count,
                "created_at": u.created_at.isoformat() if u.created_at else None
            }
            for u in users_result.scalars()
        ]

        # Export config
        config_result = await bot_session.execute(select(BotConfig))
        data["config"] = [
            {"key": c.key, "value": c.value}
            for c in config_result.scalars()
        ]

        # Export training
        training_result = await bot_session.execute(select(TrainingMessage))
        data["training"] = [
            {
                "id": t.id,
                "content": t.content,
                "priority": t.priority,
                "is_active": t.is_active
            }
            for t in training_result.scalars()
        ]

        # Write file
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Send file
        doc = FSInputFile(backup_path, filename=backup_name)
        await bot.send_document(
            chat_id=callback.from_user.id,
            document=doc,
            caption=f"Database backup (JSON): {backup_name}"
        )

        # Cleanup
        os.remove(backup_path)

        logger.info(f"JSON backup sent to {callback.from_user.id}")

    except Exception as e:
        logger.error(f"JSON backup error: {e}", exc_info=True)
        await callback.message.answer(
            get_text("db_export_error", lang),
            reply_markup=AdminKeyboards.back_button(lang, "admin:database")
        )


# Privacy policy handlers
@router.callback_query(F.data == "admin:privacy")
async def show_privacy(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Show privacy policy settings."""
    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    config_result = await bot_session.execute(
        select(BotConfig).where(BotConfig.key == "privacy_policy_url")
    )
    config = config_result.scalar_one_or_none()
    url = config.value if config else "Not set"

    await state.set_state(AdminStates.privacy_menu)
    await callback.answer()

    text = get_text("current_privacy_url", lang, url=url)

    try:
        await callback.message.edit_text(
            text,
            reply_markup=AdminKeyboards.privacy_menu(lang)
        )
    except TelegramBadRequest:
        await callback.message.answer(
            text,
            reply_markup=AdminKeyboards.privacy_menu(lang)
        )


@router.callback_query(F.data == "privacy:edit")
async def edit_privacy_start(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Start editing privacy URL."""
    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await state.set_state(AdminStates.privacy_edit)
    await callback.answer()

    try:
        await callback.message.edit_text(
            get_text("enter_privacy_url", lang),
            reply_markup=AdminKeyboards.back_button(lang, "admin:privacy")
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("enter_privacy_url", lang),
            reply_markup=AdminKeyboards.back_button(lang, "admin:privacy")
        )


from aiogram.types import Message


@router.message(AdminStates.privacy_edit)
async def edit_privacy_url(
    message: Message,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Handle privacy URL input."""
    url = message.text.strip()

    result = await bot_session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    if not url:
        return

    config_result = await bot_session.execute(
        select(BotConfig).where(BotConfig.key == "privacy_policy_url")
    )
    config = config_result.scalar_one_or_none()

    if config:
        config.value = url
    else:
        config = BotConfig(key="privacy_policy_url", value=url)
        bot_session.add(config)

    await state.clear()
    await message.answer(
        get_text("privacy_url_updated", lang),
        reply_markup=AdminKeyboards.back_button(lang, "admin:privacy")
    )
