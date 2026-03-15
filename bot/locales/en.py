"""English localization."""

TEXTS = {
    # Welcome
    "welcome_new": "Welcome to CartaMe!\n\nPlease review the privacy policy and select your language.",
    "welcome_back": "Welcome back, {name}!",
    "privacy_policy": "Privacy Policy: {url}",
    "select_language": "Select language:",
    "language_set": "Language set: English",

    # Main menu
    "main_menu": "Main Menu",
    "btn_new_chat": "New Chat",
    "btn_continue_chat": "Continue Chat",
    "btn_settings": "Settings",
    "btn_back": "Back",
    "btn_main_menu": "Main Menu",

    # Chat
    "chat_started": "New chat started. Write your question.",
    "chat_continued": "Continuing chat. Write your question.",
    "no_active_chat": "No active chat. Start a new one.",
    "only_text": "Please send text messages only.",
    "ai_thinking": "Processing your request...",

    # Operator
    "operator_requested": "Request for operator sent. Please wait.",
    "operator_connected": "Operator connected to chat.",
    "support_reply": "Support reply:\n{message}",
    "btn_return_ai": "Return AI",
    "ai_returned": "AI is active again. You can ask questions.",
    "ai_auto_returned": "AI automatically returned after {minutes} minutes without operator response.",

    # Errors
    "error_general": "An error occurred. Please try again later.",
    "error_ai_unavailable": "AI is temporarily unavailable. Your request has been forwarded to support.",
    "error_banned": "You are banned. Reason: {reason}",
    "error_flood": "Too many messages. Please wait.",

    # Settings
    "settings_menu": "Settings",
    "btn_change_language": "Change Language",

    # Off-topic
    "offtopic_response": "Sorry, I can only help with questions related to our service.",

    # Admin
    "admin_menu": "Admin Panel",
    "admin_only": "Admin access only.",
    "btn_ai_providers": "AI Providers",
    "btn_ai_keys": "API Keys",
    "btn_ai_models": "AI Models",
    "btn_antiflood": "Anti-flood",
    "btn_privacy_policy": "Privacy Policy",
    "btn_training": "AI Training",
    "btn_database": "Database",
    "btn_user_info": "User Info",
    "btn_reports": "Reports",
    "btn_chats": "Manage Chats",
    "btn_add_local_ai": "Local AI",

    # Providers
    "providers_list": "AI Providers list:",
    "provider_info": "Provider: {name}\nSlug: {slug}\nURL: {url}\nStatus: {status}\nDefault: {default}",
    "btn_add_provider": "Add Provider",
    "btn_set_default": "Set as Default",
    "btn_toggle_status": "On/Off",
    "btn_delete": "Delete",
    "enter_provider_slug": "Enter provider slug (Latin letters):",
    "enter_provider_name": "Enter provider display name:",
    "enter_provider_url": "Enter provider base_url:",
    "provider_added": "Provider added.",
    "provider_deleted": "Provider deleted.",
    "provider_is_default": "Cannot delete default provider.",
    "provider_set_default": "Provider set as default.",

    # Keys
    "keys_list": "API keys for provider {provider}:",
    "key_info": "Key: {masked}\nStatus: {status}\nRequests: {requests}/{limit}\nLast error: {error}",
    "btn_add_key": "Add Key",
    "btn_activate": "Activate",
    "btn_deactivate": "Deactivate",
    "enter_api_key": "Enter API key:",
    "key_added": "Key added.",
    "key_deleted": "Key deleted.",
    "key_empty": "Key cannot be empty.",
    "key_activated": "Key activated.",
    "key_deactivated": "Key deactivated.",

    # Models
    "models_list": "AI models for provider {provider}:",
    "model_info": "Model: {name}\nDisplay: {display}\nStatus: {status}\nDefault: {default}\nErrors: {errors}\nLast used: {last_used}",
    "btn_add_model": "Add Model",
    "enter_model_name": "Enter model name (as in API):",
    "enter_model_display": "Enter model display name:",
    "model_added": "Model added.",
    "model_deleted": "Model deleted.",
    "model_is_last": "Cannot delete last model.",
    "model_set_default": "Model set as default.",
    "model_activated": "Model activated.",
    "model_deactivated": "Model deactivated.",

    # Local AI
    "local_ai_wizard": "Local AI Setup Wizard",
    "enter_local_base_url": "Enter base_url (e.g.: http://localhost:11434/v1):",
    "enter_local_model_name": "Enter model name:",
    "enter_local_provider_name": "Enter provider name:",
    "enter_local_api_key": 'Enter API key (or "-" if not required):',
    "local_ai_added": "Local AI added:\nProvider: {provider}\nModel: {model}",

    # Training
    "training_list": "Training messages (page {page}/{total}):",
    "training_info": "Message #{id}\nPriority: {priority}\nStatus: {status}\n\n{content}",
    "btn_add_training": "Add Message",
    "btn_edit_text": "Edit Text",
    "btn_edit_priority": "Change Priority",
    "btn_toggle_active": "On/Off",
    "enter_training_text": "Enter training message text:",
    "enter_training_priority": "Enter priority (1-10):\n1-3: high\n4-7: medium\n8-10: low",
    "training_added": "Message added.",
    "training_updated": "Message updated.",
    "training_deleted": "Message deleted.",
    "training_activated": "Message activated.",
    "training_deactivated": "Message deactivated.",
    "priority_invalid": "Priority must be a number from 1 to 10.",

    # User info
    "enter_user_search": "Enter user ID or @username:",
    "user_not_found": "User not found.",
    "similar_users": "Similar users:",
    "user_info": """User:
ID: {id}
Username: @{username}
Name: {name}
Language: {language}
Role: {role}
Messages: {messages}
Sessions: {sessions}
Banned: {banned}
Topic: {topic}
Registered: {created}""",
    "btn_ban": "Ban",
    "btn_unban": "Unban",
    "btn_grant_admin": "Grant Admin",
    "btn_revoke_admin": "Revoke Admin",
    "user_banned": "User banned.",
    "user_unbanned": "User unbanned.",
    "admin_granted": "Admin rights granted.",
    "admin_revoked": "Admin rights revoked.",

    # Antiflood
    "antiflood_settings": "Anti-flood settings:\nThreshold: {threshold} messages\nWindow: {window} seconds\nBan: {duration} seconds",
    "enter_threshold": "Enter threshold (message count):",
    "enter_window": "Enter time window (seconds):",
    "enter_duration": "Enter ban duration (seconds):",
    "antiflood_updated": "Anti-flood settings updated.",
    "invalid_number": "Enter a valid number.",
    "btn_edit_threshold": "Edit Threshold",
    "btn_edit_window": "Edit Window",
    "btn_edit_duration": "Edit Ban Duration",

    # Privacy policy
    "current_privacy_url": "Current privacy policy URL:\n{url}",
    "enter_privacy_url": "Enter new URL:",
    "privacy_url_updated": "Privacy policy URL updated.",
    "btn_edit_url": "Edit URL",

    # Database
    "database_menu": "Database Management",
    "btn_export_db": "Export DB",
    "btn_download_backup": "Download Backup",
    "db_exported": "Database exported.",
    "db_export_error": "Database export error.",

    # Reports
    "select_period": "Select report period:",
    "btn_today": "Today",
    "btn_7_days": "7 Days",
    "btn_30_days": "30 Days",
    "report": """Report for {period}:

Total users: {total_users}
New in period: {new_users}
Total messages: {total_messages}
User messages: {user_messages}
Human replies: {human_replies}
AI replies: {ai_replies}
AI share: {ai_percent}%

Top 10 questions:
{top_questions}""",

    # Chats
    "chats_list": "Managed chats (page {page}/{total}):",
    "chat_info": "Chat: {title}\nID: {id}\nType: {type}\nActive: {active}\nPrimary: {primary}",
    "btn_set_primary": "Set as Primary",
    "btn_leave_chat": "Leave Chat",
    "chat_set_primary": "Chat set as primary.",
    "chat_left": "Bot left the chat.",
    "no_chats": "No managed chats.",

    # Support group
    "topic_created": "Topic created for user {name} ({id})",
    "user_message_header": "Message from user:",
    "ai_response_header": "AI response:",
    "operator_alert": "User {name} ({id}) requested an operator!",
    "btn_ai_reply": "AI Reply",
    "btn_resend_ai": "Enable AI",
    "btn_ban_user": "Ban User",

    # Group commands
    "group_info": """Chat info:
Chat ID: {chat_id}
Type: {type}
Title: {title}
Thread ID: {thread_id}
Message ID: {message_id}
Reply to: {reply_to}
Called by: {user}""",
}
