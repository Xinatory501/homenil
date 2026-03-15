"""Bot loader and initialization."""
import logging
from typing import Dict, Optional

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy import select

from bot.config import settings
from bot.handlers import get_all_routers
from bot.middlewares import (
    DatabaseMiddleware,
    BanCheckMiddleware,
    AntiFloodMiddleware,
    ClaimMiddleware,
)
from database import init_bot_db, init_shared_db, get_bot_session, get_shared_session
from database.models import AIProvider, AIKey, AIModel, BotConfig, User
from database.models.user import UserRole

logger = logging.getLogger(__name__)


async def create_bot(token: str, bot_id: str) -> tuple[Bot, Dispatcher]:
    """Create and configure a bot instance."""
    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=MemoryStorage())

    # Register middlewares in order
    dp.message.middleware(DatabaseMiddleware(bot_id))
    dp.callback_query.middleware(DatabaseMiddleware(bot_id))
    dp.my_chat_member.middleware(DatabaseMiddleware(bot_id))

    dp.message.middleware(BanCheckMiddleware())
    dp.callback_query.middleware(BanCheckMiddleware())

    dp.message.middleware(AntiFloodMiddleware())

    # Claim middleware for multi-bot coordination
    dp.message.middleware(ClaimMiddleware())

    # Register routers
    for router in get_all_routers():
        dp.include_router(router)

    return bot, dp


async def init_databases(bot_ids: list[str]) -> None:
    """Initialize all databases and create tables."""
    # Initialize shared DB first
    await init_shared_db()
    logger.info("Shared database initialized")

    # Initialize bot-specific DBs
    for bot_id in bot_ids:
        await init_bot_db(bot_id)
        logger.info(f"Bot database initialized: {bot_id}")


async def init_defaults(bot_id: str) -> None:
    """Initialize default configuration for a bot."""
    async with get_bot_session(bot_id) as session:
        # Default config values
        defaults = {
            "privacy_policy_url": "https://example.com/privacy",
            "support_group_id": "",
            "antiflood_threshold": str(settings.antiflood_threshold),
            "antiflood_time_window": str(settings.antiflood_time_window),
            "autoban_duration": str(settings.autoban_duration),
        }

        for key, value in defaults.items():
            result = await session.execute(
                select(BotConfig).where(BotConfig.key == key)
            )
            if not result.scalar_one_or_none():
                config = BotConfig(key=key, value=value)
                session.add(config)
                logger.debug(f"Default config set: {key}={value}")

        # Create admin users from env
        for admin_id in settings.admin_id_list:
            result = await session.execute(
                select(User).where(User.id == admin_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                user = User(
                    id=admin_id,
                    role=UserRole.ADMIN.value
                )
                session.add(user)
                logger.info(f"Admin user created: {admin_id}")
            elif user.role != UserRole.ADMIN.value:
                user.role = UserRole.ADMIN.value
                logger.info(f"User {admin_id} promoted to admin")

        await session.commit()


async def init_default_ai_providers() -> None:
    """Initialize default AI providers if shared DB is empty."""
    async with get_shared_session() as session:
        # Check if any providers exist
        result = await session.execute(select(AIProvider))
        if result.scalar_one_or_none():
            logger.debug("AI providers already exist, skipping defaults")
            return

        # Create default OpenAI provider
        provider = AIProvider(
            slug="openai",
            display_name="OpenAI",
            base_url="https://api.openai.com/v1",
            is_active=True,
            is_default=True
        )
        session.add(provider)
        await session.flush()

        # Create default model
        model = AIModel(
            provider_id=provider.id,
            model_name="gpt-4o-mini",
            display_name="GPT-4o Mini",
            is_active=True,
            is_default=True
        )
        session.add(model)

        await session.commit()
        logger.info("Default AI provider and model created")


def get_bot_ids() -> list[str]:
    """Get list of configured bot IDs."""
    bot_ids = ["bot1"]
    if settings.bot2_token:
        bot_ids.append("bot2")
    if settings.bot3_token:
        bot_ids.append("bot3")
    return bot_ids


def get_bot_tokens() -> Dict[str, str]:
    """Get mapping of bot IDs to tokens."""
    return settings.bot_tokens
