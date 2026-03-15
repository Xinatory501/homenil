"""Support handlers."""
from aiogram import Router

from bot.handlers.support.group import router as group_router
from bot.handlers.support.topics import router as topics_router

support_router = Router(name="support")
support_router.include_router(group_router)
support_router.include_router(topics_router)

__all__ = ["support_router"]
