"""Uzbek localization."""

TEXTS = {
    # Welcome
    "welcome_new": "CartaMe xizmatiga xush kelibsiz!\n\nMaxfiylik siyosatini ko'rib chiqing va tilni tanlang.",
    "welcome_back": "Qaytganingiz bilan, {name}!",
    "privacy_policy": "Maxfiylik siyosati: {url}",
    "select_language": "Tilni tanlang:",
    "language_set": "Til o'rnatildi: O'zbek",

    # Main menu
    "main_menu": "Asosiy menyu",
    "btn_new_chat": "Yangi chat",
    "btn_continue_chat": "Chatni davom ettirish",
    "btn_settings": "Sozlamalar",
    "btn_back": "Orqaga",
    "btn_main_menu": "Asosiy menyu",

    # Chat
    "chat_started": "Yangi chat boshlandi. Savolingizni yozing.",
    "chat_continued": "Chat davom etmoqda. Savolingizni yozing.",
    "no_active_chat": "Faol chat yo'q. Yangisini boshlang.",
    "only_text": "Iltimos, faqat matnli xabarlar yuboring.",
    "ai_thinking": "So'rovingiz qayta ishlanmoqda...",

    # Operator
    "operator_requested": "Operator uchun so'rov yuborildi. Iltimos, kuting.",
    "operator_connected": "Operator chatga ulandi.",
    "support_reply": "Qo'llab-quvvatlash javobi:\n{message}",
    "btn_return_ai": "AI qaytarish",
    "ai_returned": "AI yana faol. Savollar berishingiz mumkin.",
    "ai_auto_returned": "AI {minutes} daqiqa operator javobisiz avtomatik qaytarildi.",

    # Errors
    "error_general": "Xatolik yuz berdi. Keyinroq qayta urinib ko'ring.",
    "error_ai_unavailable": "AI vaqtincha mavjud emas. So'rovingiz qo'llab-quvvatlashga yuborildi.",
    "error_banned": "Siz bloklangansiz. Sabab: {reason}",
    "error_flood": "Juda ko'p xabarlar. Iltimos, kuting.",

    # Settings
    "settings_menu": "Sozlamalar",
    "btn_change_language": "Tilni o'zgartirish",

    # Off-topic
    "offtopic_response": "Kechirasiz, men faqat xizmatimiz bilan bog'liq savollarga yordam bera olaman.",

    # Admin
    "admin_menu": "Administrator paneli",
    "admin_only": "Faqat administratorlar uchun.",
    "btn_ai_providers": "AI provayderlar",
    "btn_ai_keys": "API kalitlar",
    "btn_ai_models": "AI modellar",
    "btn_antiflood": "Antiflyud",
    "btn_privacy_policy": "Maxfiylik siyosati",
    "btn_training": "AI o'qitish",
    "btn_database": "Ma'lumotlar bazasi",
    "btn_user_info": "Foydalanuvchi",
    "btn_reports": "Hisobotlar",
    "btn_chats": "Chatlarni boshqarish",
    "btn_add_local_ai": "Lokal AI",

    # Providers
    "providers_list": "AI provayderlar ro'yxati:",
    "provider_info": "Provayder: {name}\nSlug: {slug}\nURL: {url}\nHolat: {status}\nStandart: {default}",
    "btn_add_provider": "Provayder qo'shish",
    "btn_set_default": "Standart qilish",
    "btn_toggle_status": "Yoq/O'ch",
    "btn_delete": "O'chirish",
    "enter_provider_slug": "Provayder slug kiriting (lotin harflarida):",
    "enter_provider_name": "Provayder nomini kiriting:",
    "enter_provider_url": "Provayder base_url kiriting:",
    "provider_added": "Provayder qo'shildi.",
    "provider_deleted": "Provayder o'chirildi.",
    "provider_is_default": "Standart provayderni o'chirib bo'lmaydi.",
    "provider_set_default": "Provayder standart qilib o'rnatildi.",

    # Keys
    "keys_list": "{provider} provayderi uchun API kalitlar:",
    "key_info": "Kalit: {masked}\nHolat: {status}\nSo'rovlar: {requests}/{limit}\nOxirgi xato: {error}",
    "btn_add_key": "Kalit qo'shish",
    "btn_activate": "Faollashtirish",
    "btn_deactivate": "O'chirish",
    "enter_api_key": "API kalit kiriting:",
    "key_added": "Kalit qo'shildi.",
    "key_deleted": "Kalit o'chirildi.",
    "key_empty": "Kalit bo'sh bo'lishi mumkin emas.",
    "key_activated": "Kalit faollashtirildi.",
    "key_deactivated": "Kalit o'chirildi.",

    # Models
    "models_list": "{provider} provayderi uchun AI modellar:",
    "model_info": "Model: {name}\nKo'rsatish: {display}\nHolat: {status}\nStandart: {default}\nXatolar: {errors}\nOxirgi foydalanish: {last_used}",
    "btn_add_model": "Model qo'shish",
    "enter_model_name": "Model nomini kiriting (API da bo'lgandek):",
    "enter_model_display": "Model ko'rsatish nomini kiriting:",
    "model_added": "Model qo'shildi.",
    "model_deleted": "Model o'chirildi.",
    "model_is_last": "Oxirgi modelni o'chirib bo'lmaydi.",
    "model_set_default": "Model standart qilib o'rnatildi.",
    "model_activated": "Model faollashtirildi.",
    "model_deactivated": "Model o'chirildi.",

    # Local AI
    "local_ai_wizard": "Lokal AI o'rnatish ustasi",
    "enter_local_base_url": "base_url kiriting (masalan: http://localhost:11434/v1):",
    "enter_local_model_name": "Model nomini kiriting:",
    "enter_local_provider_name": "Provayder nomini kiriting:",
    "enter_local_api_key": 'API kalit kiriting (yoki "-" agar talab qilinmasa):',
    "local_ai_added": "Lokal AI qo'shildi:\nProvayder: {provider}\nModel: {model}",

    # Training
    "training_list": "O'qitish xabarlari (sahifa {page}/{total}):",
    "training_info": "Xabar #{id}\nUstuvorlik: {priority}\nHolat: {status}\n\n{content}",
    "btn_add_training": "Xabar qo'shish",
    "btn_edit_text": "Matnni tahrirlash",
    "btn_edit_priority": "Ustuvorlikni o'zgartirish",
    "btn_toggle_active": "Yoq/O'ch",
    "enter_training_text": "O'qitish xabari matnini kiriting:",
    "enter_training_priority": "Ustuvorlikni kiriting (1-10):\n1-3: yuqori\n4-7: o'rta\n8-10: past",
    "training_added": "Xabar qo'shildi.",
    "training_updated": "Xabar yangilandi.",
    "training_deleted": "Xabar o'chirildi.",
    "training_activated": "Xabar faollashtirildi.",
    "training_deactivated": "Xabar o'chirildi.",
    "priority_invalid": "Ustuvorlik 1 dan 10 gacha bo'lgan raqam bo'lishi kerak.",

    # User info
    "enter_user_search": "Foydalanuvchi ID yoki @username kiriting:",
    "user_not_found": "Foydalanuvchi topilmadi.",
    "similar_users": "O'xshash foydalanuvchilar:",
    "user_info": """Foydalanuvchi:
ID: {id}
Username: @{username}
Ism: {name}
Til: {language}
Rol: {role}
Xabarlar: {messages}
Sessiyalar: {sessions}
Bloklangan: {banned}
Mavzu: {topic}
Ro'yxatdan o'tgan: {created}""",
    "btn_ban": "Bloklash",
    "btn_unban": "Blokdan chiqarish",
    "btn_grant_admin": "Admin berish",
    "btn_revoke_admin": "Adminni olish",
    "user_banned": "Foydalanuvchi bloklandi.",
    "user_unbanned": "Foydalanuvchi blokdan chiqarildi.",
    "admin_granted": "Admin huquqlari berildi.",
    "admin_revoked": "Admin huquqlari olib qo'yildi.",

    # Antiflood
    "antiflood_settings": "Antiflyud sozlamalari:\nChegarasi: {threshold} xabar\nOyna: {window} soniya\nBan: {duration} soniya",
    "enter_threshold": "Chegarani kiriting (xabarlar soni):",
    "enter_window": "Vaqt oynasini kiriting (soniyalar):",
    "enter_duration": "Ban davomiyligini kiriting (soniyalar):",
    "antiflood_updated": "Antiflyud sozlamalari yangilandi.",
    "invalid_number": "To'g'ri raqam kiriting.",
    "btn_edit_threshold": "Chegarani tahrirlash",
    "btn_edit_window": "Oynani tahrirlash",
    "btn_edit_duration": "Ban davomiyligini tahrirlash",

    # Privacy policy
    "current_privacy_url": "Joriy maxfiylik siyosati URL:\n{url}",
    "enter_privacy_url": "Yangi URL kiriting:",
    "privacy_url_updated": "Maxfiylik siyosati URL yangilandi.",
    "btn_edit_url": "URLni tahrirlash",

    # Database
    "database_menu": "Ma'lumotlar bazasini boshqarish",
    "btn_export_db": "BDni eksport qilish",
    "btn_download_backup": "Zaxira nusxasini yuklab olish",
    "db_exported": "Ma'lumotlar bazasi eksport qilindi.",
    "db_export_error": "Ma'lumotlar bazasini eksport qilishda xato.",

    # Reports
    "select_period": "Hisobot davrini tanlang:",
    "btn_today": "Bugun",
    "btn_7_days": "7 kun",
    "btn_30_days": "30 kun",
    "report": """Hisobot {period}:

Jami foydalanuvchilar: {total_users}
Davrda yangi: {new_users}
Jami xabarlar: {total_messages}
Foydalanuvchi xabarlari: {user_messages}
Inson javoblari: {human_replies}
AI javoblari: {ai_replies}
AI ulushi: {ai_percent}%

Top 10 savollar:
{top_questions}""",

    # Chats
    "chats_list": "Boshqariladigan chatlar (sahifa {page}/{total}):",
    "chat_info": "Chat: {title}\nID: {id}\nTur: {type}\nFaol: {active}\nAsosiy: {primary}",
    "btn_set_primary": "Asosiy qilish",
    "btn_leave_chat": "Chatdan chiqish",
    "chat_set_primary": "Chat asosiy qilib belgilandi.",
    "chat_left": "Bot chatdan chiqdi.",
    "no_chats": "Boshqariladigan chatlar yo'q.",

    # Support group
    "topic_created": "Foydalanuvchi uchun mavzu yaratildi {name} ({id})",
    "user_message_header": "Foydalanuvchidan xabar:",
    "ai_response_header": "AI javobi:",
    "operator_alert": "Foydalanuvchi {name} ({id}) operator so'radi!",
    "btn_ai_reply": "AI javob",
    "btn_resend_ai": "AIni yoqish",
    "btn_ban_user": "Bloklash",

    # Group commands
    "group_info": """Chat ma'lumotlari:
Chat ID: {chat_id}
Tur: {type}
Nom: {title}
Thread ID: {thread_id}
Message ID: {message_id}
Javob: {reply_to}
Chaqirgan: {user}""",
}
