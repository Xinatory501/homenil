#!/usr/bin/env python3
"""CartaMe Telegram Bot - Main entry point."""
import asyncio
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict

from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, and_

from bot.config import settings
from bot.loader import (
    create_bot,
    init_databases,
    init_defaults,
    init_default_ai_providers,
    get_bot_ids,
    get_bot_tokens,
)
from database.base import close_all_engines, get_bot_session
from database.models import User
from bot.locales import get_text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

# Reduce noise from libraries
logging.getLogger("aiogram").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: AsyncIOScheduler = None
# Global bots reference for scheduler
_bots: Dict[str, Bot] = {}


async def auto_return_ai() -> None:
    """
    Scheduled task to auto-return AI for users after timeout.
    Runs every minute, checks users with disabled AI.
    """
    for bot_id in get_bot_ids():
        try:
            async with get_bot_session(bot_id) as session:
                timeout = datetime.utcnow() - timedelta(
                    minutes=settings.ai_auto_return_minutes
                )

                # Find users with AI disabled for too long
                result = await session.execute(
                    select(User).where(
                        and_(
                            User.ai_enabled == False,
                            User.ai_disabled_at != None,
                            User.ai_disabled_at < timeout
                        )
                    )
                )
                users = list(result.scalars().all())

                for user in users:
                    user.ai_enabled = True
                    user.ai_disabled_at = None

                    # Notify user
                    if bot_id in _bots:
                        try:
                            await _bots[bot_id].send_message(
                                chat_id=user.id,
                                text=get_text(
                                    "ai_auto_returned",
                                    user.language,
                                    minutes=settings.ai_auto_return_minutes
                                )
                            )
                        except Exception as e:
                            logger.debug(f"Could not notify user {user.id}: {e}")

                    logger.info(
                        f"AI auto-returned for user {user.id} "
                        f"(bot: {bot_id})"
                    )

                await session.commit()

        except Exception as e:
            logger.error(f"Error in auto_return_ai for {bot_id}: {e}")


async def cleanup_expired_claims() -> None:
    """Clean up expired request claims from shared DB."""
    from database.base import get_shared_session
    from database.models import RequestClaim, UserOwnerLock
    from sqlalchemy import delete

    try:
        async with get_shared_session() as session:
            now = datetime.utcnow()

            # Delete expired claims
            await session.execute(
                delete(RequestClaim).where(RequestClaim.expires_at < now)
            )

            # Delete expired user locks
            await session.execute(
                delete(UserOwnerLock).where(UserOwnerLock.locked_until < now)
            )

            await session.commit()

    except Exception as e:
        logger.error(f"Error in cleanup_expired_claims: {e}")


async def process_pending_requests(bot_id: str) -> None:
    """Process any pending requests from previous run."""
    from database import get_bot_session
    from database.models import PendingRequest
    from database.models.chat import RequestStatus
    from sqlalchemy import select, update

    async with get_bot_session(bot_id) as session:
        # Mark stale processing requests as failed
        await session.execute(
            update(PendingRequest)
            .where(PendingRequest.status == RequestStatus.PROCESSING.value)
            .values(status=RequestStatus.FAILED.value)
        )

        # Get pending requests
        result = await session.execute(
            select(PendingRequest)
            .where(PendingRequest.status == RequestStatus.PENDING.value)
            .order_by(PendingRequest.created_at)
            .limit(10)
        )
        pending = list(result.scalars().all())

        if pending:
            logger.info(f"Found {len(pending)} pending requests for {bot_id}")
            # Mark as processing for now, actual processing would need more context
            for req in pending:
                req.status = RequestStatus.FAILED.value
                req.error_message = "Bot restarted, request expired"

        await session.commit()


async def on_startup(bots: Dict[str, Bot]) -> None:
    """Startup handler."""
    global scheduler, _bots
    logger.info("Starting CartaMe bots...")

    _bots = bots
    bot_ids = list(bots.keys())

    # Initialize databases
    await init_databases(bot_ids)

    # Initialize defaults for each bot
    for bot_id in bot_ids:
        await init_defaults(bot_id)
        await process_pending_requests(bot_id)

    # Initialize default AI providers (shared)
    await init_default_ai_providers()

    # Start scheduler for background tasks
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        auto_return_ai,
        "interval",
        minutes=1,
        id="auto_return_ai",
        replace_existing=True
    )
    scheduler.add_job(
        cleanup_expired_claims,
        "interval",
        minutes=5,
        id="cleanup_claims",
        replace_existing=True
    )
    scheduler.start()
    logger.info("Background scheduler started")

    # Log bot info
    for bot_id, bot in bots.items():
        try:
            me = await bot.get_me()
            logger.info(f"{bot_id}: @{me.username} ({me.id})")
        except Exception as e:
            logger.error(f"Failed to get info for {bot_id}: {e}")

    logger.info("All bots started successfully")


async def on_shutdown(bots: Dict[str, Bot]) -> None:
    """Shutdown handler."""
    global scheduler
    logger.info("Shutting down CartaMe bots...")

    # Stop scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

    for bot_id, bot in bots.items():
        try:
            await bot.session.close()
            logger.info(f"{bot_id} session closed")
        except Exception as e:
            logger.error(f"Error closing {bot_id}: {e}")

    await close_all_engines()
    logger.info("All connections closed")


async def main() -> None:
    """Main entry point."""
    # Validate configuration
    if not settings.bot1_token:
        logger.error("BOT1_TOKEN is required")
        sys.exit(1)

    if not settings.admin_ids:
        logger.error("ADMIN_IDS is required")
        sys.exit(1)

    # Get configured bots
    tokens = get_bot_tokens()
    logger.info(f"Configured bots: {list(tokens.keys())}")

    # Create bot instances
    bots: Dict[str, Bot] = {}
    dispatchers: Dict[str, Dispatcher] = {}

    for bot_id, token in tokens.items():
        try:
            bot, dp = await create_bot(token, bot_id)
            bots[bot_id] = bot
            dispatchers[bot_id] = dp
            logger.info(f"Created bot: {bot_id}")
        except Exception as e:
            logger.error(f"Failed to create {bot_id}: {e}")
            sys.exit(1)

    # Register startup/shutdown handlers
    for bot_id, dp in dispatchers.items():
        dp.startup.register(lambda: on_startup(bots))
        dp.shutdown.register(lambda: on_shutdown(bots))

    try:
        # Start all bots
        if len(bots) == 1:
            # Single bot mode
            bot_id = list(bots.keys())[0]
            await dispatchers[bot_id].start_polling(bots[bot_id])
        else:
            # Multi-bot mode - run all dispatchers
            tasks = []
            for bot_id in bots:
                tasks.append(
                    dispatchers[bot_id].start_polling(
                        bots[bot_id],
                        allowed_updates=[
                            "message",
                            "callback_query",
                            "my_chat_member",
                            "chat_member",
                        ]
                    )
                )

            await asyncio.gather(*tasks)

    except (KeyboardInterrupt, SystemExit):
        logger.info("Received shutdown signal")
    finally:
        await on_shutdown(bots)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
