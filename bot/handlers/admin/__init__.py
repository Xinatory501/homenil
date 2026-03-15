"""Admin handlers."""
from aiogram import Router

from bot.handlers.admin.main import router as main_router
from bot.handlers.admin.providers import router as providers_router
from bot.handlers.admin.keys import router as keys_router
from bot.handlers.admin.models import router as models_router
from bot.handlers.admin.training import router as training_router
from bot.handlers.admin.users import router as users_router
from bot.handlers.admin.antiflood import router as antiflood_router
from bot.handlers.admin.reports import router as reports_router
from bot.handlers.admin.chats import router as chats_router
from bot.handlers.admin.database import router as database_router

admin_router = Router(name="admin")
admin_router.include_router(main_router)
admin_router.include_router(providers_router)
admin_router.include_router(keys_router)
admin_router.include_router(models_router)
admin_router.include_router(training_router)
admin_router.include_router(users_router)
admin_router.include_router(antiflood_router)
admin_router.include_router(reports_router)
admin_router.include_router(chats_router)
admin_router.include_router(database_router)

__all__ = ["admin_router"]
