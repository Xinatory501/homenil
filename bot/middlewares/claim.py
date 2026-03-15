"""Claim middleware for multi-bot coordination."""
import logging
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import RequestClaim, UserOwnerLock
from database.models.claims import ClaimStatus
from bot.config import settings

logger = logging.getLogger(__name__)


class ClaimMiddleware(BaseMiddleware):
    """
    Middleware that implements claim-based multi-bot coordination.

    Ensures only one bot processes each user message by:
    1. Using sticky user ownership (user_owner_lock)
    2. Message-level claims (request_claims)

    This prevents duplicate responses when multiple bots receive the same update.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Only apply to private messages
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)

        # Extract message and user info
        message: Optional[Message] = None
        if isinstance(event, Message):
            message = event
        elif isinstance(event, CallbackQuery) and event.message:
            # For callbacks, we don't need claim (it's a response to existing interaction)
            return await handler(event, data)

        if not message:
            return await handler(event, data)

        # Skip group messages (claims only for private chats)
        if message.chat.type != "private":
            return await handler(event, data)

        user = message.from_user
        if not user:
            return await handler(event, data)

        bot_id: str = data.get("bot_id", "bot1")
        shared_session: AsyncSession = data.get("shared_session")

        if not shared_session:
            return await handler(event, data)

        user_id = user.id
        chat_id = message.chat.id
        message_id = message.message_id
        now = datetime.utcnow()

        # Step 1: Check/acquire user ownership lock
        can_process = await self._check_user_ownership(
            shared_session, user_id, bot_id, now
        )

        if not can_process:
            logger.debug(
                f"Bot {bot_id} skipping message {message_id} from user {user_id}: "
                "another bot owns this user"
            )
            return  # Skip processing

        # Step 2: Try to claim this specific message
        claim_key = f"{chat_id}:{user_id}:{message_id}"
        claimed = await self._try_claim_message(
            shared_session, claim_key, user_id, chat_id, message_id,
            data.get("event_update", {}).get("update_id", 0), bot_id, now
        )

        if not claimed:
            logger.debug(
                f"Bot {bot_id} skipping message {message_id}: "
                "already claimed by another bot"
            )
            return  # Skip processing

        logger.debug(f"Bot {bot_id} claimed message {message_id} from user {user_id}")

        # Store claim key for completion/failure handling
        data["claim_key"] = claim_key

        try:
            result = await handler(event, data)

            # Mark claim as completed
            await self._complete_claim(shared_session, claim_key)

            return result
        except Exception as e:
            # Mark claim as failed
            await self._fail_claim(shared_session, claim_key)
            raise

    async def _check_user_ownership(
        self,
        session: AsyncSession,
        user_id: int,
        bot_id: str,
        now: datetime,
    ) -> bool:
        """
        Check if this bot can process messages from this user.
        Implements sticky user ownership.
        """
        # Clean expired locks first
        await session.execute(
            delete(UserOwnerLock).where(UserOwnerLock.locked_until < now)
        )
        await session.flush()

        # Check existing lock
        result = await session.execute(
            select(UserOwnerLock).where(UserOwnerLock.user_id == user_id)
        )
        lock = result.scalar_one_or_none()

        if lock:
            if lock.owner_bot_id == bot_id:
                # Extend lock
                lock.locked_until = now + timedelta(minutes=settings.user_lock_minutes)
                return True
            else:
                # Another bot owns this user
                return False

        # No lock exists, try to acquire
        lock_until = now + timedelta(minutes=settings.user_lock_minutes)
        new_lock = UserOwnerLock(
            user_id=user_id,
            owner_bot_id=bot_id,
            locked_until=lock_until,
        )

        try:
            session.add(new_lock)
            await session.flush()
            logger.info(f"Bot {bot_id} acquired ownership of user {user_id}")
            return True
        except IntegrityError:
            # Another bot acquired the lock first
            await session.rollback()
            return False

    async def _try_claim_message(
        self,
        session: AsyncSession,
        claim_key: str,
        user_id: int,
        chat_id: int,
        message_id: int,
        update_id: int,
        bot_id: str,
        now: datetime,
    ) -> bool:
        """Try to claim a specific message for processing."""
        # Clean expired claims
        await session.execute(
            delete(RequestClaim).where(RequestClaim.expires_at < now)
        )
        await session.flush()

        # Try to insert claim
        expires_at = now + timedelta(seconds=settings.claim_expire_seconds)
        claim = RequestClaim(
            claim_key=claim_key,
            user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            update_id=update_id,
            bot_id=bot_id,
            status=ClaimStatus.PROCESSING.value,
            expires_at=expires_at,
        )

        try:
            session.add(claim)
            await session.flush()
            return True
        except IntegrityError:
            # Another bot already claimed this message
            await session.rollback()
            return False

    async def _complete_claim(self, session: AsyncSession, claim_key: str) -> None:
        """Mark a claim as completed."""
        result = await session.execute(
            select(RequestClaim).where(RequestClaim.claim_key == claim_key)
        )
        claim = result.scalar_one_or_none()
        if claim:
            claim.status = ClaimStatus.COMPLETED.value
            await session.flush()

    async def _fail_claim(self, session: AsyncSession, claim_key: str) -> None:
        """Mark a claim as failed."""
        try:
            result = await session.execute(
                select(RequestClaim).where(RequestClaim.claim_key == claim_key)
            )
            claim = result.scalar_one_or_none()
            if claim:
                claim.status = ClaimStatus.FAILED.value
                await session.flush()
        except Exception as e:
            logger.error(f"Failed to mark claim as failed: {e}")
