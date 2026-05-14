"""Главное меню участника — постоянная reply-клавиатура внизу чата."""

from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

CLIENT_NAV_KARMA = "Где взять карму"
CLIENT_NAV_OFFICE_MAP = "Карта офиса"
CLIENT_NAV_BALANCE = "Мой баланс"
CLIENT_NAV_SPEND = "Списать карму"
CLIENT_NAV_DEMO_PROGRAM = "Программа демо-дня"
CLIENT_NAV_OPEN_MIC = "Задать вопрос на открытый микрофон"

CLIENT_NAV_TEXTS: frozenset[str] = frozenset(
    {
        CLIENT_NAV_KARMA,
        CLIENT_NAV_OFFICE_MAP,
        CLIENT_NAV_BALANCE,
        CLIENT_NAV_SPEND,
        CLIENT_NAV_DEMO_PROGRAM,
        CLIENT_NAV_OPEN_MIC,
    }
)


def strip_reply_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def client_main_nav_reply_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура постоянно видна внизу чата участника."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=CLIENT_NAV_KARMA),
                KeyboardButton(text=CLIENT_NAV_OFFICE_MAP),
            ],
            [
                KeyboardButton(text=CLIENT_NAV_BALANCE),
                KeyboardButton(text=CLIENT_NAV_SPEND),
            ],
            [
                KeyboardButton(text=CLIENT_NAV_DEMO_PROGRAM),
                KeyboardButton(text=CLIENT_NAV_OPEN_MIC),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
