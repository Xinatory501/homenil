"""Localization module."""
from typing import Optional
from bot.locales.ru import TEXTS as RU_TEXTS
from bot.locales.en import TEXTS as EN_TEXTS
from bot.locales.uz import TEXTS as UZ_TEXTS
from bot.locales.kz import TEXTS as KZ_TEXTS

LANGUAGES = {
    "ru": "Русский",
    "en": "English",
    "uz": "O'zbek",
    "kz": "Қазақша",
}

_TEXTS = {
    "ru": RU_TEXTS,
    "en": EN_TEXTS,
    "uz": UZ_TEXTS,
    "kz": KZ_TEXTS,
}


def get_text(key: str, lang: str = "ru", **kwargs) -> str:
    """Get localized text by key."""
    texts = _TEXTS.get(lang, _TEXTS["ru"])
    text = texts.get(key, _TEXTS["ru"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text


def get_language_name(lang: str) -> str:
    """Get language display name."""
    return LANGUAGES.get(lang, lang)


__all__ = ["get_text", "get_language_name", "LANGUAGES"]
