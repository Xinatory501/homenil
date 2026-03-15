"""Admin FSM states."""
from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    """Admin panel states."""

    # Main admin menu
    main_menu = State()

    # Providers
    providers_list = State()
    provider_view = State()
    provider_add_slug = State()
    provider_add_name = State()
    provider_add_url = State()

    # Keys
    keys_list = State()
    key_view = State()
    key_add = State()

    # Models
    models_list = State()
    model_view = State()
    model_add_name = State()
    model_add_display = State()

    # Local AI wizard
    local_ai_url = State()
    local_ai_model = State()
    local_ai_provider = State()
    local_ai_key = State()

    # Training messages
    training_list = State()
    training_view = State()
    training_add_text = State()
    training_add_priority = State()
    training_edit_text = State()
    training_edit_priority = State()

    # User management
    user_search = State()
    user_view = State()

    # Antiflood
    antiflood_menu = State()
    antiflood_threshold = State()
    antiflood_window = State()
    antiflood_duration = State()

    # Privacy policy
    privacy_menu = State()
    privacy_edit = State()

    # Database
    database_menu = State()

    # Reports
    reports_menu = State()
    reports_view = State()

    # Chats
    chats_list = State()
    chat_view = State()
