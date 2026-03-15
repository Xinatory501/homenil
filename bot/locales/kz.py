"""Kazakh localization."""

TEXTS = {
    # Welcome
    "welcome_new": "CartaMe-ге қош келдіңіз!\n\nҚұпиялылық саясатымен танысып, тілді таңдаңыз.",
    "welcome_back": "Қайта оралғаныңызбен, {name}!",
    "privacy_policy": "Құпиялылық саясаты: {url}",
    "select_language": "Тілді таңдаңыз:",
    "language_set": "Тіл орнатылды: Қазақша",

    # Main menu
    "main_menu": "Басты мәзір",
    "btn_new_chat": "Жаңа чат",
    "btn_continue_chat": "Чатты жалғастыру",
    "btn_settings": "Баптаулар",
    "btn_back": "Артқа",
    "btn_main_menu": "Басты мәзір",

    # Chat
    "chat_started": "Жаңа чат басталды. Сұрағыңызды жазыңыз.",
    "chat_continued": "Чат жалғасуда. Сұрағыңызды жазыңыз.",
    "no_active_chat": "Белсенді чат жоқ. Жаңасын бастаңыз.",
    "only_text": "Тек мәтіндік хабарламалар жіберіңіз.",
    "ai_thinking": "Сұрауыңыз өңделуде...",

    # Operator
    "operator_requested": "Оператор сұрауы жіберілді. Күтіңіз.",
    "operator_connected": "Оператор чатқа қосылды.",
    "support_reply": "Қолдау жауабы:\n{message}",
    "btn_return_ai": "AI қайтару",
    "ai_returned": "AI қайта белсенді. Сұрақтар қоюға болады.",
    "ai_auto_returned": "AI оператор жауабынсыз {minutes} минуттан кейін автоматты түрде қайтарылды.",

    # Errors
    "error_general": "Қате орын алды. Кейінірек қайталап көріңіз.",
    "error_ai_unavailable": "AI уақытша қол жетімсіз. Сұрауыңыз қолдауға жіберілді.",
    "error_banned": "Сіз бұғатталғансыз. Себеп: {reason}",
    "error_flood": "Тым көп хабарлама. Күтіңіз.",

    # Settings
    "settings_menu": "Баптаулар",
    "btn_change_language": "Тілді өзгерту",

    # Off-topic
    "offtopic_response": "Кешіріңіз, мен тек қызметімізге қатысты сұрақтарға көмектесе аламын.",

    # Admin
    "admin_menu": "Әкімші панелі",
    "admin_only": "Тек әкімшілер үшін.",
    "btn_ai_providers": "AI провайдерлер",
    "btn_ai_keys": "API кілттер",
    "btn_ai_models": "AI модельдер",
    "btn_antiflood": "Антифлуд",
    "btn_privacy_policy": "Құпиялылық саясаты",
    "btn_training": "AI оқыту",
    "btn_database": "Дерекқор",
    "btn_user_info": "Пайдаланушы",
    "btn_reports": "Есептер",
    "btn_chats": "Чаттарды басқару",
    "btn_add_local_ai": "Жергілікті AI",

    # Providers
    "providers_list": "AI провайдерлер тізімі:",
    "provider_info": "Провайдер: {name}\nSlug: {slug}\nURL: {url}\nКүй: {status}\nӘдепкі: {default}",
    "btn_add_provider": "Провайдер қосу",
    "btn_set_default": "Әдепкі ету",
    "btn_toggle_status": "Қосу/Өшіру",
    "btn_delete": "Жою",
    "enter_provider_slug": "Провайдер slug енгізіңіз (латын әріптерімен):",
    "enter_provider_name": "Провайдер атауын енгізіңіз:",
    "enter_provider_url": "Провайдер base_url енгізіңіз:",
    "provider_added": "Провайдер қосылды.",
    "provider_deleted": "Провайдер жойылды.",
    "provider_is_default": "Әдепкі провайдерді жою мүмкін емес.",
    "provider_set_default": "Провайдер әдепкі етіп орнатылды.",

    # Keys
    "keys_list": "{provider} провайдері үшін API кілттер:",
    "key_info": "Кілт: {masked}\nКүй: {status}\nСұраулар: {requests}/{limit}\nСоңғы қате: {error}",
    "btn_add_key": "Кілт қосу",
    "btn_activate": "Белсендіру",
    "btn_deactivate": "Өшіру",
    "enter_api_key": "API кілтін енгізіңіз:",
    "key_added": "Кілт қосылды.",
    "key_deleted": "Кілт жойылды.",
    "key_empty": "Кілт бос болмауы керек.",
    "key_activated": "Кілт белсендірілді.",
    "key_deactivated": "Кілт өшірілді.",

    # Models
    "models_list": "{provider} провайдері үшін AI модельдер:",
    "model_info": "Модель: {name}\nКөрсету: {display}\nКүй: {status}\nӘдепкі: {default}\nҚателер: {errors}\nСоңғы қолдану: {last_used}",
    "btn_add_model": "Модель қосу",
    "enter_model_name": "Модель атауын енгізіңіз (API-дағыдай):",
    "enter_model_display": "Модельдің көрсету атауын енгізіңіз:",
    "model_added": "Модель қосылды.",
    "model_deleted": "Модель жойылды.",
    "model_is_last": "Соңғы модельді жою мүмкін емес.",
    "model_set_default": "Модель әдепкі етіп орнатылды.",
    "model_activated": "Модель белсендірілді.",
    "model_deactivated": "Модель өшірілді.",

    # Local AI
    "local_ai_wizard": "Жергілікті AI орнату шебері",
    "enter_local_base_url": "base_url енгізіңіз (мысалы: http://localhost:11434/v1):",
    "enter_local_model_name": "Модель атауын енгізіңіз:",
    "enter_local_provider_name": "Провайдер атауын енгізіңіз:",
    "enter_local_api_key": 'API кілтін енгізіңіз (немесе "-" егер талап етілмесе):',
    "local_ai_added": "Жергілікті AI қосылды:\nПровайдер: {provider}\nМодель: {model}",

    # Training
    "training_list": "Оқыту хабарламалары (бет {page}/{total}):",
    "training_info": "Хабарлама #{id}\nБасымдық: {priority}\nКүй: {status}\n\n{content}",
    "btn_add_training": "Хабарлама қосу",
    "btn_edit_text": "Мәтінді өңдеу",
    "btn_edit_priority": "Басымдықты өзгерту",
    "btn_toggle_active": "Қосу/Өшіру",
    "enter_training_text": "Оқыту хабарламасының мәтінін енгізіңіз:",
    "enter_training_priority": "Басымдықты енгізіңіз (1-10):\n1-3: жоғары\n4-7: орташа\n8-10: төмен",
    "training_added": "Хабарлама қосылды.",
    "training_updated": "Хабарлама жаңартылды.",
    "training_deleted": "Хабарлама жойылды.",
    "training_activated": "Хабарлама белсендірілді.",
    "training_deactivated": "Хабарлама өшірілді.",
    "priority_invalid": "Басымдық 1-ден 10-ға дейінгі сан болуы керек.",

    # User info
    "enter_user_search": "Пайдаланушы ID немесе @username енгізіңіз:",
    "user_not_found": "Пайдаланушы табылмады.",
    "similar_users": "Ұқсас пайдаланушылар:",
    "user_info": """Пайдаланушы:
ID: {id}
Username: @{username}
Аты: {name}
Тіл: {language}
Рөл: {role}
Хабарламалар: {messages}
Сессиялар: {sessions}
Бұғатталған: {banned}
Тақырып: {topic}
Тіркелген: {created}""",
    "btn_ban": "Бұғаттау",
    "btn_unban": "Бұғаттан шығару",
    "btn_grant_admin": "Әкімші беру",
    "btn_revoke_admin": "Әкімшіні алып тастау",
    "user_banned": "Пайдаланушы бұғатталды.",
    "user_unbanned": "Пайдаланушы бұғаттан шығарылды.",
    "admin_granted": "Әкімші құқықтары берілді.",
    "admin_revoked": "Әкімші құқықтары алынды.",

    # Antiflood
    "antiflood_settings": "Антифлуд баптаулары:\nШек: {threshold} хабарлама\nТерезе: {window} секунд\nБан: {duration} секунд",
    "enter_threshold": "Шекті енгізіңіз (хабарламалар саны):",
    "enter_window": "Уақыт терезесін енгізіңіз (секунд):",
    "enter_duration": "Бан ұзақтығын енгізіңіз (секунд):",
    "antiflood_updated": "Антифлуд баптаулары жаңартылды.",
    "invalid_number": "Дұрыс сан енгізіңіз.",
    "btn_edit_threshold": "Шекті өңдеу",
    "btn_edit_window": "Терезені өңдеу",
    "btn_edit_duration": "Бан ұзақтығын өңдеу",

    # Privacy policy
    "current_privacy_url": "Ағымдағы құпиялылық саясаты URL:\n{url}",
    "enter_privacy_url": "Жаңа URL енгізіңіз:",
    "privacy_url_updated": "Құпиялылық саясаты URL жаңартылды.",
    "btn_edit_url": "URL өңдеу",

    # Database
    "database_menu": "Дерекқорды басқару",
    "btn_export_db": "ДҚ экспорттау",
    "btn_download_backup": "Резервтік көшірмені жүктеу",
    "db_exported": "Дерекқор экспортталды.",
    "db_export_error": "Дерекқорды экспорттау қатесі.",

    # Reports
    "select_period": "Есеп кезеңін таңдаңыз:",
    "btn_today": "Бүгін",
    "btn_7_days": "7 күн",
    "btn_30_days": "30 күн",
    "report": """Есеп {period}:

Барлық пайдаланушылар: {total_users}
Кезеңдегі жаңалар: {new_users}
Барлық хабарламалар: {total_messages}
Пайдаланушы хабарламалары: {user_messages}
Адам жауаптары: {human_replies}
AI жауаптары: {ai_replies}
AI үлесі: {ai_percent}%

Топ 10 сұрақтар:
{top_questions}""",

    # Chats
    "chats_list": "Басқарылатын чаттар (бет {page}/{total}):",
    "chat_info": "Чат: {title}\nID: {id}\nТүрі: {type}\nБелсенді: {active}\nНегізгі: {primary}",
    "btn_set_primary": "Негізгі ету",
    "btn_leave_chat": "Чаттан шығу",
    "chat_set_primary": "Чат негізгі етіп белгіленді.",
    "chat_left": "Бот чаттан шықты.",
    "no_chats": "Басқарылатын чаттар жоқ.",

    # Support group
    "topic_created": "Пайдаланушы үшін тақырып жасалды {name} ({id})",
    "user_message_header": "Пайдаланушыдан хабарлама:",
    "ai_response_header": "AI жауабы:",
    "operator_alert": "Пайдаланушы {name} ({id}) оператор сұрады!",
    "btn_ai_reply": "AI жауап",
    "btn_resend_ai": "AI қосу",
    "btn_ban_user": "Бұғаттау",

    # Group commands
    "group_info": """Чат ақпараты:
Chat ID: {chat_id}
Түрі: {type}
Атауы: {title}
Thread ID: {thread_id}
Message ID: {message_id}
Жауап: {reply_to}
Шақырған: {user}""",
}
