"""User handlers."""
from aiogram import Router

from bot.handlers.user.start import router as start_router
from bot.handlers.user.chat import router as chat_router
from bot.handlers.user.settings import router as settings_router

user_router = Router(name="user")
user_router.include_router(start_router)
user_router.include_router(chat_router)
user_router.include_router(settings_router)

__all__ = ["user_router"]
