"""Middlewares module."""
from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.ban_check import BanCheckMiddleware
from bot.middlewares.antiflood import AntiFloodMiddleware
from bot.middlewares.claim import ClaimMiddleware

__all__ = [
    "DatabaseMiddleware",
    "BanCheckMiddleware",
    "AntiFloodMiddleware",
    "ClaimMiddleware",
]
