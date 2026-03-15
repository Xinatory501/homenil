"""Russian localization."""

TEXTS = {
    # Welcome
    "welcome_new": "Добро пожаловать в CartaMe!\n\nПожалуйста, ознакомьтесь с политикой конфиденциальности и выберите язык.",
    "welcome_back": "С возвращением, {name}!",
    "privacy_policy": "Политика конфиденциальности: {url}",
    "select_language": "Выберите язык:",
    "language_set": "Язык установлен: Русский",

    # Main menu
    "main_menu": "Главное меню",
    "btn_new_chat": "Новый чат",
    "btn_continue_chat": "Продолжить чат",
    "btn_settings": "Настройки",
    "btn_back": "Назад",
    "btn_main_menu": "Главное меню",

    # Chat
    "chat_started": "Начат новый чат. Напишите ваш вопрос.",
    "chat_continued": "Продолжаем чат. Напишите ваш вопрос.",
    "no_active_chat": "Нет активного чата. Начните новый.",
    "only_text": "Пожалуйста, отправляйте только текстовые сообщения.",
    "ai_thinking": "Обрабатываю ваш запрос...",

    # Operator
    "operator_requested": "Запрос на подключение оператора отправлен. Пожалуйста, подождите.",
    "operator_connected": "Оператор подключен к чату.",
    "support_reply": "Ответ поддержки:\n{message}",
    "btn_return_ai": "Вернуть AI",
    "ai_returned": "AI снова активен. Можете задавать вопросы.",
    "ai_auto_returned": "AI автоматически возвращен после {minutes} минут без ответа оператора.",

    # Errors
    "error_general": "Произошла ошибка. Попробуйте позже.",
    "error_ai_unavailable": "AI временно недоступен. Ваш запрос передан в поддержку.",
    "error_banned": "Вы заблокированы. Причина: {reason}",
    "error_flood": "Слишком много сообщений. Подождите немного.",

    # Settings
    "settings_menu": "Настройки",
    "btn_change_language": "Изменить язык",

    # Off-topic
    "offtopic_response": "Извините, я могу помочь только с вопросами, связанными с нашим сервисом.",

    # Admin
    "admin_menu": "Панель администратора",
    "admin_only": "Доступ только для администраторов.",
    "btn_ai_providers": "AI провайдеры",
    "btn_ai_keys": "API ключи",
    "btn_ai_models": "AI модели",
    "btn_antiflood": "Антифлуд",
    "btn_privacy_policy": "Политика конф.",
    "btn_training": "Обучение AI",
    "btn_database": "База данных",
    "btn_user_info": "Пользователь",
    "btn_reports": "Отчеты",
    "btn_chats": "Управление чатами",
    "btn_add_local_ai": "Локальная нейросеть",

    # Providers
    "providers_list": "Список AI провайдеров:",
    "provider_info": "Провайдер: {name}\nSlug: {slug}\nURL: {url}\nСтатус: {status}\nПо умолчанию: {default}",
    "btn_add_provider": "Добавить провайдер",
    "btn_set_default": "Установить по умолчанию",
    "btn_toggle_status": "Вкл/Выкл",
    "btn_delete": "Удалить",
    "enter_provider_slug": "Введите slug провайдера (латиницей):",
    "enter_provider_name": "Введите отображаемое имя провайдера:",
    "enter_provider_url": "Введите base_url провайдера:",
    "provider_added": "Провайдер добавлен.",
    "provider_deleted": "Провайдер удален.",
    "provider_is_default": "Нельзя удалить провайдер по умолчанию.",
    "provider_set_default": "Провайдер установлен по умолчанию.",

    # Keys
    "keys_list": "API ключи провайдера {provider}:",
    "key_info": "Ключ: {masked}\nСтатус: {status}\nЗапросов: {requests}/{limit}\nПоследняя ошибка: {error}",
    "btn_add_key": "Добавить ключ",
    "btn_activate": "Активировать",
    "btn_deactivate": "Деактивировать",
    "enter_api_key": "Введите API ключ:",
    "key_added": "Ключ добавлен.",
    "key_deleted": "Ключ удален.",
    "key_empty": "Ключ не может быть пустым.",
    "key_activated": "Ключ активирован.",
    "key_deactivated": "Ключ деактивирован.",

    # Models
    "models_list": "AI модели провайдера {provider}:",
    "model_info": "Модель: {name}\nОтображение: {display}\nСтатус: {status}\nПо умолчанию: {default}\nОшибок: {errors}\nПоследнее использование: {last_used}",
    "btn_add_model": "Добавить модель",
    "enter_model_name": "Введите имя модели (как в API):",
    "enter_model_display": "Введите отображаемое имя модели:",
    "model_added": "Модель добавлена.",
    "model_deleted": "Модель удалена.",
    "model_is_last": "Нельзя удалить последнюю модель.",
    "model_set_default": "Модель установлена по умолчанию.",
    "model_activated": "Модель активирована.",
    "model_deactivated": "Модель деактивирована.",

    # Local AI
    "local_ai_wizard": "Мастер добавления локальной нейросети",
    "enter_local_base_url": "Введите base_url (например: http://localhost:11434/v1):",
    "enter_local_model_name": "Введите имя модели:",
    "enter_local_provider_name": "Введите название провайдера:",
    "enter_local_api_key": 'Введите API ключ (или "-" если не требуется):',
    "local_ai_added": "Локальная нейросеть добавлена:\nПровайдер: {provider}\nМодель: {model}",

    # Training
    "training_list": "Обучающие сообщения (стр. {page}/{total}):",
    "training_info": "Сообщение #{id}\nПриоритет: {priority}\nСтатус: {status}\n\n{content}",
    "btn_add_training": "Добавить сообщение",
    "btn_edit_text": "Редактировать текст",
    "btn_edit_priority": "Изменить приоритет",
    "btn_toggle_active": "Вкл/Выкл",
    "enter_training_text": "Введите текст обучающего сообщения:",
    "enter_training_priority": "Введите приоритет (1-10):\n1-3: высокий\n4-7: средний\n8-10: низкий",
    "training_added": "Сообщение добавлено.",
    "training_updated": "Сообщение обновлено.",
    "training_deleted": "Сообщение удалено.",
    "training_activated": "Сообщение активировано.",
    "training_deactivated": "Сообщение деактивировано.",
    "priority_invalid": "Приоритет должен быть числом от 1 до 10.",

    # User info
    "enter_user_search": "Введите ID пользователя или @username:",
    "user_not_found": "Пользователь не найден.",
    "similar_users": "Похожие пользователи:",
    "user_info": """Пользователь:
ID: {id}
Username: @{username}
Имя: {name}
Язык: {language}
Роль: {role}
Сообщений: {messages}
Сессий: {sessions}
Бан: {banned}
Топик: {topic}
Регистрация: {created}""",
    "btn_ban": "Заблокировать",
    "btn_unban": "Разблокировать",
    "btn_grant_admin": "Назначить админом",
    "btn_revoke_admin": "Снять админа",
    "user_banned": "Пользователь заблокирован.",
    "user_unbanned": "Пользователь разблокирован.",
    "admin_granted": "Права администратора выданы.",
    "admin_revoked": "Права администратора отозваны.",

    # Antiflood
    "antiflood_settings": "Настройки антифлуда:\nПорог: {threshold} сообщений\nОкно: {window} секунд\nБан: {duration} секунд",
    "enter_threshold": "Введите порог (количество сообщений):",
    "enter_window": "Введите окно времени (секунды):",
    "enter_duration": "Введите длительность бана (секунды):",
    "antiflood_updated": "Настройки антифлуда обновлены.",
    "invalid_number": "Введите корректное число.",
    "btn_edit_threshold": "Изменить порог",
    "btn_edit_window": "Изменить окно",
    "btn_edit_duration": "Изменить длительность бана",

    # Privacy policy
    "current_privacy_url": "Текущий URL политики конфиденциальности:\n{url}",
    "enter_privacy_url": "Введите новый URL:",
    "privacy_url_updated": "URL политики обновлен.",
    "btn_edit_url": "Изменить URL",

    # Database
    "database_menu": "Управление базой данных",
    "btn_export_db": "Выгрузить БД",
    "btn_download_backup": "Скачать бекап",
    "db_exported": "База данных экспортирована.",
    "db_export_error": "Ошибка экспорта базы данных.",

    # Reports
    "select_period": "Выберите период отчета:",
    "btn_today": "Сегодня",
    "btn_7_days": "7 дней",
    "btn_30_days": "30 дней",
    "report": """Отчет за {period}:

Всего пользователей: {total_users}
Новых за период: {new_users}
Всего сообщений: {total_messages}
Сообщений пользователей: {user_messages}
Ответов людей: {human_replies}
Автоответов AI: {ai_replies}
Доля AI: {ai_percent}%

Топ-10 вопросов:
{top_questions}""",

    # Chats
    "chats_list": "Управляемые чаты (стр. {page}/{total}):",
    "chat_info": "Чат: {title}\nID: {id}\nТип: {type}\nАктивен: {active}\nОсновной: {primary}",
    "btn_set_primary": "Установить основным",
    "btn_leave_chat": "Покинуть чат",
    "chat_set_primary": "Чат установлен как основной.",
    "chat_left": "Бот покинул чат.",
    "no_chats": "Нет управляемых чатов.",

    # Support group
    "topic_created": "Создан топик для пользователя {name} ({id})",
    "user_message_header": "Сообщение от пользователя:",
    "ai_response_header": "Ответ AI:",
    "operator_alert": "Пользователь {name} ({id}) запросил оператора!",
    "btn_ai_reply": "AI ответ",
    "btn_resend_ai": "Включить AI",
    "btn_ban_user": "Заблокировать",

    # Group commands
    "group_info": """Информация о чате:
Chat ID: {chat_id}
Тип: {type}
Название: {title}
Thread ID: {thread_id}
Message ID: {message_id}
Reply to: {reply_to}
Вызвал: {user}""",
}
