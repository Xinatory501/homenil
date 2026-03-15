"""User keyboards."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.locales import get_text, LANGUAGES


class UserKeyboards:
    """User-facing keyboards."""

    @staticmethod
    def language_selection() -> InlineKeyboardMarkup:
        """Language selection keyboard."""
        builder = InlineKeyboardBuilder()
        for code, name in LANGUAGES.items():
            builder.add(InlineKeyboardButton(
                text=name,
                callback_data=f"lang:{code}"
            ))
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def main_menu(lang: str, has_active_chat: bool = False) -> InlineKeyboardMarkup:
        """Main menu keyboard."""
        builder = InlineKeyboardBuilder()

        builder.add(InlineKeyboardButton(
            text=get_text("btn_new_chat", lang),
            callback_data="chat:new"
        ))

        if has_active_chat:
            builder.add(InlineKeyboardButton(
                text=get_text("btn_continue_chat", lang),
                callback_data="chat:continue"
            ))

        builder.add(InlineKeyboardButton(
            text=get_text("btn_settings", lang),
            callback_data="settings"
        ))

        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def settings_menu(lang: str) -> InlineKeyboardMarkup:
        """Settings menu keyboard."""
        builder = InlineKeyboardBuilder()

        builder.add(InlineKeyboardButton(
            text=get_text("btn_change_language", lang),
            callback_data="settings:language"
        ))

        builder.add(InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data="back:main"
        ))

        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def return_ai(lang: str) -> InlineKeyboardMarkup:
        """Return AI button."""
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text=get_text("btn_return_ai", lang),
            callback_data="return_ai"
        ))
        return builder.as_markup()

    @staticmethod
    def back_to_main(lang: str) -> InlineKeyboardMarkup:
        """Back to main menu button."""
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text=get_text("btn_main_menu", lang),
            callback_data="back:main"
        ))
        return builder.as_markup()

    @staticmethod
    def back_button(lang: str, callback_data: str = "back") -> InlineKeyboardMarkup:
        """Generic back button."""
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data=callback_data
        ))
        return builder.as_markup()
