"""Admin keyboards."""
from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.locales import get_text
from database.models import AIProvider, AIKey, AIModel, TrainingMessage, ManagedChat


class AdminKeyboards:
    """Admin panel keyboards."""

    @staticmethod
    def main_menu(lang: str) -> InlineKeyboardMarkup:
        """Admin main menu."""
        builder = InlineKeyboardBuilder()

        buttons = [
            ("btn_ai_providers", "admin:providers"),
            ("btn_ai_keys", "admin:keys"),
            ("btn_ai_models", "admin:models"),
            ("btn_add_local_ai", "admin:local_ai"),
            ("btn_training", "admin:training"),
            ("btn_antiflood", "admin:antiflood"),
            ("btn_privacy_policy", "admin:privacy"),
            ("btn_user_info", "admin:user"),
            ("btn_reports", "admin:reports"),
            ("btn_chats", "admin:chats"),
            ("btn_database", "admin:database"),
        ]

        for text_key, callback in buttons:
            builder.add(InlineKeyboardButton(
                text=get_text(text_key, lang),
                callback_data=callback
            ))

        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def providers_list(
        providers: List[AIProvider],
        lang: str,
        page: int = 0,
        per_page: int = 5
    ) -> InlineKeyboardMarkup:
        """Providers list with pagination."""
        builder = InlineKeyboardBuilder()

        start = page * per_page
        end = start + per_page
        page_providers = providers[start:end]

        for provider in page_providers:
            status = "+" if provider.is_active else "-"
            default = "*" if provider.is_default else ""
            builder.add(InlineKeyboardButton(
                text=f"{status}{default} {provider.display_name}",
                callback_data=f"provider:{provider.id}"
            ))

        builder.adjust(1)

        # Pagination
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(
                text="<",
                callback_data=f"providers_page:{page - 1}"
            ))
        if end < len(providers):
            nav_row.append(InlineKeyboardButton(
                text=">",
                callback_data=f"providers_page:{page + 1}"
            ))
        if nav_row:
            builder.row(*nav_row)

        builder.row(InlineKeyboardButton(
            text=get_text("btn_add_provider", lang),
            callback_data="provider:add"
        ))

        builder.row(InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data="admin:menu"
        ))

        return builder.as_markup()

    @staticmethod
    def provider_actions(provider: AIProvider, lang: str) -> InlineKeyboardMarkup:
        """Provider action buttons."""
        builder = InlineKeyboardBuilder()

        # Toggle status
        builder.add(InlineKeyboardButton(
            text=get_text("btn_toggle_status", lang),
            callback_data=f"provider_toggle:{provider.id}"
        ))

        # Set default
        if not provider.is_default:
            builder.add(InlineKeyboardButton(
                text=get_text("btn_set_default", lang),
                callback_data=f"provider_default:{provider.id}"
            ))

        # Delete (only if not default)
        if not provider.is_default:
            builder.add(InlineKeyboardButton(
                text=get_text("btn_delete", lang),
                callback_data=f"provider_delete:{provider.id}"
            ))

        builder.adjust(2)

        builder.row(InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data="admin:providers"
        ))

        return builder.as_markup()

    @staticmethod
    def keys_list(
        keys: List[AIKey],
        provider_id: int,
        lang: str,
        page: int = 0
    ) -> InlineKeyboardMarkup:
        """API keys list."""
        builder = InlineKeyboardBuilder()

        per_page = 5
        start = page * per_page
        end = start + per_page
        page_keys = keys[start:end]

        for key in page_keys:
            status = "+" if key.is_active else "-"
            builder.add(InlineKeyboardButton(
                text=f"{status} {key.masked_key}",
                callback_data=f"key:{key.id}"
            ))

        builder.adjust(1)

        # Pagination
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(
                text="<",
                callback_data=f"keys_page:{provider_id}:{page - 1}"
            ))
        if end < len(keys):
            nav_row.append(InlineKeyboardButton(
                text=">",
                callback_data=f"keys_page:{provider_id}:{page + 1}"
            ))
        if nav_row:
            builder.row(*nav_row)

        builder.row(InlineKeyboardButton(
            text=get_text("btn_add_key", lang),
            callback_data=f"key:add:{provider_id}"
        ))

        builder.row(InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data="admin:providers"
        ))

        return builder.as_markup()

    @staticmethod
    def key_actions(key: AIKey, lang: str) -> InlineKeyboardMarkup:
        """Key action buttons."""
        builder = InlineKeyboardBuilder()

        if key.is_active:
            builder.add(InlineKeyboardButton(
                text=get_text("btn_deactivate", lang),
                callback_data=f"key_toggle:{key.id}"
            ))
        else:
            builder.add(InlineKeyboardButton(
                text=get_text("btn_activate", lang),
                callback_data=f"key_toggle:{key.id}"
            ))

        builder.add(InlineKeyboardButton(
            text=get_text("btn_delete", lang),
            callback_data=f"key_delete:{key.id}"
        ))

        builder.adjust(2)

        builder.row(InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data=f"keys:{key.provider_id}"
        ))

        return builder.as_markup()

    @staticmethod
    def models_list(
        models: List[AIModel],
        provider_id: int,
        lang: str,
        page: int = 0
    ) -> InlineKeyboardMarkup:
        """Models list."""
        builder = InlineKeyboardBuilder()

        per_page = 5
        start = page * per_page
        end = start + per_page
        page_models = models[start:end]

        for model in page_models:
            status = "+" if model.is_active else "-"
            default = "*" if model.is_default else ""
            builder.add(InlineKeyboardButton(
                text=f"{status}{default} {model.display_name}",
                callback_data=f"model:{model.id}"
            ))

        builder.adjust(1)

        # Pagination
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(
                text="<",
                callback_data=f"models_page:{provider_id}:{page - 1}"
            ))
        if end < len(models):
            nav_row.append(InlineKeyboardButton(
                text=">",
                callback_data=f"models_page:{provider_id}:{page + 1}"
            ))
        if nav_row:
            builder.row(*nav_row)

        builder.row(InlineKeyboardButton(
            text=get_text("btn_add_model", lang),
            callback_data=f"model:add:{provider_id}"
        ))

        builder.row(InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data="admin:providers"
        ))

        return builder.as_markup()

    @staticmethod
    def model_actions(model: AIModel, total_models: int, lang: str) -> InlineKeyboardMarkup:
        """Model action buttons."""
        builder = InlineKeyboardBuilder()

        if model.is_active:
            builder.add(InlineKeyboardButton(
                text=get_text("btn_deactivate", lang),
                callback_data=f"model_toggle:{model.id}"
            ))
        else:
            builder.add(InlineKeyboardButton(
                text=get_text("btn_activate", lang),
                callback_data=f"model_toggle:{model.id}"
            ))

        if not model.is_default:
            builder.add(InlineKeyboardButton(
                text=get_text("btn_set_default", lang),
                callback_data=f"model_default:{model.id}"
            ))

        # Allow delete only if more than one model
        if total_models > 1:
            builder.add(InlineKeyboardButton(
                text=get_text("btn_delete", lang),
                callback_data=f"model_delete:{model.id}"
            ))

        builder.adjust(2)

        builder.row(InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data=f"models:{model.provider_id}"
        ))

        return builder.as_markup()

    @staticmethod
    def training_list(
        messages: List[TrainingMessage],
        lang: str,
        page: int = 0,
        per_page: int = 5
    ) -> InlineKeyboardMarkup:
        """Training messages list."""
        builder = InlineKeyboardBuilder()

        start = page * per_page
        end = start + per_page
        page_messages = messages[start:end]
        total_pages = (len(messages) + per_page - 1) // per_page

        for msg in page_messages:
            status = "+" if msg.is_active else "-"
            preview = msg.content[:30] + "..." if len(msg.content) > 30 else msg.content
            builder.add(InlineKeyboardButton(
                text=f"{status} [{msg.priority}] {preview}",
                callback_data=f"training:{msg.id}"
            ))

        builder.adjust(1)

        # Pagination
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(
                text="<",
                callback_data=f"training_page:{page - 1}"
            ))
        if end < len(messages):
            nav_row.append(InlineKeyboardButton(
                text=">",
                callback_data=f"training_page:{page + 1}"
            ))
        if nav_row:
            builder.row(*nav_row)

        builder.row(InlineKeyboardButton(
            text=get_text("btn_add_training", lang),
            callback_data="training:add"
        ))

        builder.row(InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data="admin:menu"
        ))

        return builder.as_markup()

    @staticmethod
    def training_actions(msg: TrainingMessage, lang: str) -> InlineKeyboardMarkup:
        """Training message actions."""
        builder = InlineKeyboardBuilder()

        builder.add(InlineKeyboardButton(
            text=get_text("btn_edit_text", lang),
            callback_data=f"training_edit_text:{msg.id}"
        ))

        builder.add(InlineKeyboardButton(
            text=get_text("btn_edit_priority", lang),
            callback_data=f"training_edit_priority:{msg.id}"
        ))

        builder.add(InlineKeyboardButton(
            text=get_text("btn_toggle_active", lang),
            callback_data=f"training_toggle:{msg.id}"
        ))

        builder.add(InlineKeyboardButton(
            text=get_text("btn_delete", lang),
            callback_data=f"training_delete:{msg.id}"
        ))

        builder.adjust(2)

        builder.row(InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data="admin:training"
        ))

        return builder.as_markup()

    @staticmethod
    def user_actions(
        user_id: int,
        is_banned: bool,
        is_admin: bool,
        lang: str
    ) -> InlineKeyboardMarkup:
        """User action buttons."""
        builder = InlineKeyboardBuilder()

        if is_banned:
            builder.add(InlineKeyboardButton(
                text=get_text("btn_unban", lang),
                callback_data=f"user_unban:{user_id}"
            ))
        else:
            builder.add(InlineKeyboardButton(
                text=get_text("btn_ban", lang),
                callback_data=f"user_ban:{user_id}"
            ))

        if is_admin:
            builder.add(InlineKeyboardButton(
                text=get_text("btn_revoke_admin", lang),
                callback_data=f"user_revoke:{user_id}"
            ))
        else:
            builder.add(InlineKeyboardButton(
                text=get_text("btn_grant_admin", lang),
                callback_data=f"user_grant:{user_id}"
            ))

        builder.adjust(2)

        builder.row(InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data="admin:user"
        ))

        return builder.as_markup()

    @staticmethod
    def antiflood_menu(lang: str) -> InlineKeyboardMarkup:
        """Antiflood settings menu."""
        builder = InlineKeyboardBuilder()

        builder.add(InlineKeyboardButton(
            text=get_text("btn_edit_threshold", lang),
            callback_data="antiflood:threshold"
        ))

        builder.add(InlineKeyboardButton(
            text=get_text("btn_edit_window", lang),
            callback_data="antiflood:window"
        ))

        builder.add(InlineKeyboardButton(
            text=get_text("btn_edit_duration", lang),
            callback_data="antiflood:duration"
        ))

        builder.adjust(1)

        builder.row(InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data="admin:menu"
        ))

        return builder.as_markup()

    @staticmethod
    def privacy_menu(lang: str) -> InlineKeyboardMarkup:
        """Privacy policy menu."""
        builder = InlineKeyboardBuilder()

        builder.add(InlineKeyboardButton(
            text=get_text("btn_edit_url", lang),
            callback_data="privacy:edit"
        ))

        builder.row(InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data="admin:menu"
        ))

        return builder.as_markup()

    @staticmethod
    def database_menu(lang: str) -> InlineKeyboardMarkup:
        """Database management menu."""
        builder = InlineKeyboardBuilder()

        builder.add(InlineKeyboardButton(
            text=get_text("btn_export_db", lang),
            callback_data="db:export"
        ))

        builder.add(InlineKeyboardButton(
            text=get_text("btn_download_backup", lang),
            callback_data="db:backup"
        ))

        builder.adjust(1)

        builder.row(InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data="admin:menu"
        ))

        return builder.as_markup()

    @staticmethod
    def reports_menu(lang: str) -> InlineKeyboardMarkup:
        """Reports period selection."""
        builder = InlineKeyboardBuilder()

        builder.add(InlineKeyboardButton(
            text=get_text("btn_today", lang),
            callback_data="report:today"
        ))

        builder.add(InlineKeyboardButton(
            text=get_text("btn_7_days", lang),
            callback_data="report:7days"
        ))

        builder.add(InlineKeyboardButton(
            text=get_text("btn_30_days", lang),
            callback_data="report:30days"
        ))

        builder.adjust(3)

        builder.row(InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data="admin:menu"
        ))

        return builder.as_markup()

    @staticmethod
    def chats_list(
        chats: List[ManagedChat],
        lang: str,
        page: int = 0,
        per_page: int = 5
    ) -> InlineKeyboardMarkup:
        """Managed chats list."""
        builder = InlineKeyboardBuilder()

        start = page * per_page
        end = start + per_page
        page_chats = chats[start:end]

        for chat in page_chats:
            status = "+" if chat.is_active else "-"
            primary = "*" if chat.is_primary else ""
            title = chat.title or str(chat.id)
            builder.add(InlineKeyboardButton(
                text=f"{status}{primary} {title[:25]}",
                callback_data=f"chat:{chat.id}"
            ))

        builder.adjust(1)

        # Pagination
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(
                text="<",
                callback_data=f"chats_page:{page - 1}"
            ))
        if end < len(chats):
            nav_row.append(InlineKeyboardButton(
                text=">",
                callback_data=f"chats_page:{page + 1}"
            ))
        if nav_row:
            builder.row(*nav_row)

        builder.row(InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data="admin:menu"
        ))

        return builder.as_markup()

    @staticmethod
    def chat_actions(chat: ManagedChat, lang: str) -> InlineKeyboardMarkup:
        """Chat action buttons."""
        builder = InlineKeyboardBuilder()

        if not chat.is_primary:
            builder.add(InlineKeyboardButton(
                text=get_text("btn_set_primary", lang),
                callback_data=f"chat_primary:{chat.id}"
            ))

        builder.add(InlineKeyboardButton(
            text=get_text("btn_leave_chat", lang),
            callback_data=f"chat_leave:{chat.id}"
        ))

        builder.adjust(2)

        builder.row(InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data="admin:chats"
        ))

        return builder.as_markup()

    @staticmethod
    def back_button(lang: str, callback_data: str = "admin:menu") -> InlineKeyboardMarkup:
        """Back button."""
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data=callback_data
        ))
        return builder.as_markup()

    @staticmethod
    def support_topic_buttons(user_id: int, lang: str) -> InlineKeyboardMarkup:
        """Support topic action buttons."""
        builder = InlineKeyboardBuilder()

        builder.add(InlineKeyboardButton(
            text=get_text("btn_ai_reply", lang),
            callback_data=f"ai_reply_{user_id}"
        ))

        builder.add(InlineKeyboardButton(
            text=get_text("btn_resend_ai", lang),
            callback_data=f"resend_to_ai_{user_id}"
        ))

        builder.add(InlineKeyboardButton(
            text=get_text("btn_ban_user", lang),
            callback_data=f"ban_user_{user_id}"
        ))

        builder.adjust(3)
        return builder.as_markup()
