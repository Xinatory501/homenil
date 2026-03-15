"""User FSM states."""
from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    """User interaction states."""

    # Language selection
    selecting_language = State()

    # Chat states
    chatting = State()

    # Settings
    settings = State()
    changing_language = State()
