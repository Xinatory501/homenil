"""Training messages service."""
import logging
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import TrainingMessage

logger = logging.getLogger(__name__)


class TrainingService:
    """Service for managing training/system messages for AI."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_messages(self) -> List[TrainingMessage]:
        """Get all active training messages sorted by priority."""
        result = await self.session.execute(
            select(TrainingMessage)
            .where(TrainingMessage.is_active == True)
            .order_by(TrainingMessage.priority.asc())
        )
        return list(result.scalars().all())

    async def get_all_messages(self) -> List[TrainingMessage]:
        """Get all training messages sorted by priority."""
        result = await self.session.execute(
            select(TrainingMessage)
            .order_by(TrainingMessage.priority.asc(), TrainingMessage.id.asc())
        )
        return list(result.scalars().all())

    async def get_message(self, message_id: int) -> Optional[TrainingMessage]:
        """Get training message by ID."""
        result = await self.session.execute(
            select(TrainingMessage).where(TrainingMessage.id == message_id)
        )
        return result.scalar_one_or_none()

    async def create_message(self, content: str, priority: int = 5) -> TrainingMessage:
        """Create new training message."""
        message = TrainingMessage(
            content=content,
            priority=max(1, min(10, priority)),  # Clamp to 1-10
            is_active=True
        )
        self.session.add(message)
        await self.session.flush()
        logger.info(f"Created training message #{message.id}")
        return message

    async def update_content(self, message_id: int, content: str) -> bool:
        """Update message content."""
        message = await self.get_message(message_id)
        if not message:
            return False

        message.content = content
        await self.session.flush()
        logger.info(f"Updated content of training message #{message_id}")
        return True

    async def update_priority(self, message_id: int, priority: int) -> bool:
        """Update message priority."""
        if priority < 1 or priority > 10:
            return False

        message = await self.get_message(message_id)
        if not message:
            return False

        message.priority = priority
        await self.session.flush()
        logger.info(f"Updated priority of training message #{message_id} to {priority}")
        return True

    async def toggle_active(self, message_id: int) -> Optional[bool]:
        """Toggle message active status. Returns new status."""
        message = await self.get_message(message_id)
        if not message:
            return None

        message.is_active = not message.is_active
        await self.session.flush()
        logger.info(f"Toggled training message #{message_id} active={message.is_active}")
        return message.is_active

    async def delete_message(self, message_id: int) -> bool:
        """Delete training message."""
        message = await self.get_message(message_id)
        if not message:
            return False

        await self.session.delete(message)
        await self.session.flush()
        logger.info(f"Deleted training message #{message_id}")
        return True

    async def get_count(self) -> int:
        """Get total count of training messages."""
        result = await self.session.execute(
            select(func.count(TrainingMessage.id))
        )
        return result.scalar() or 0

    async def get_active_count(self) -> int:
        """Get count of active training messages."""
        result = await self.session.execute(
            select(func.count(TrainingMessage.id))
            .where(TrainingMessage.is_active == True)
        )
        return result.scalar() or 0
