"""Handlers module."""
from aiogram import Router

from bot.handlers.user import user_router
from bot.handlers.admin import admin_router
from bot.handlers.support import support_router


def get_all_routers() -> list[Router]:
    """Get all handler routers."""
    return [user_router, admin_router, support_router]


__all__ = ["get_all_routers", "user_router", "admin_router", "support_router"]
