"""Reports handlers."""
import logging
from datetime import datetime, timedelta
from collections import Counter
import re

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, ChatHistory
from database.models.chat import MessageRole
from bot.states import AdminStates
from bot.keyboards import AdminKeyboards
from bot.locales import get_text

logger = logging.getLogger(__name__)
router = Router(name="admin_reports")


@router.callback_query(F.data == "admin:reports")
async def show_reports_menu(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Show reports period selection."""
    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    await state.set_state(AdminStates.reports_menu)
    await callback.answer()

    try:
        await callback.message.edit_text(
            get_text("select_period", lang),
            reply_markup=AdminKeyboards.reports_menu(lang)
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("select_period", lang),
            reply_markup=AdminKeyboards.reports_menu(lang)
        )


@router.callback_query(F.data.startswith("report:"))
async def generate_report(
    callback: CallbackQuery,
    state: FSMContext,
    bot_session: AsyncSession
):
    """Generate report for selected period."""
    period = callback.data.split(":")[1]

    result = await bot_session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language if user else "ru"

    now = datetime.utcnow()

    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_name = get_text("btn_today", lang)
    elif period == "7days":
        start_date = now - timedelta(days=7)
        period_name = get_text("btn_7_days", lang)
    else:  # 30days
        start_date = now - timedelta(days=30)
        period_name = get_text("btn_30_days", lang)

    # Total users
    total_users_result = await bot_session.execute(
        select(func.count(User.id))
    )
    total_users = total_users_result.scalar() or 0

    # New users in period
    new_users_result = await bot_session.execute(
        select(func.count(User.id)).where(User.created_at >= start_date)
    )
    new_users = new_users_result.scalar() or 0

    # Total messages in period
    total_messages_result = await bot_session.execute(
        select(func.count(ChatHistory.id)).where(ChatHistory.created_at >= start_date)
    )
    total_messages = total_messages_result.scalar() or 0

    # User messages
    user_messages_result = await bot_session.execute(
        select(func.count(ChatHistory.id)).where(
            ChatHistory.created_at >= start_date,
            ChatHistory.role == MessageRole.USER.value
        )
    )
    user_messages = user_messages_result.scalar() or 0

    # Human replies (support)
    human_replies_result = await bot_session.execute(
        select(func.count(ChatHistory.id)).where(
            ChatHistory.created_at >= start_date,
            ChatHistory.role == MessageRole.SUPPORT.value
        )
    )
    human_replies = human_replies_result.scalar() or 0

    # AI replies
    ai_replies_result = await bot_session.execute(
        select(func.count(ChatHistory.id)).where(
            ChatHistory.created_at >= start_date,
            ChatHistory.role == MessageRole.ASSISTANT.value,
            ChatHistory.is_ai_handled == True
        )
    )
    ai_replies = ai_replies_result.scalar() or 0

    # Calculate AI percentage
    total_replies = human_replies + ai_replies
    ai_percent = round((ai_replies / total_replies * 100) if total_replies > 0 else 0, 1)

    # Top 10 questions
    top_questions = await _get_top_questions(bot_session, start_date)

    text = get_text(
        "report", lang,
        period=period_name,
        total_users=total_users,
        new_users=new_users,
        total_messages=total_messages,
        user_messages=user_messages,
        human_replies=human_replies,
        ai_replies=ai_replies,
        ai_percent=ai_percent,
        top_questions=top_questions
    )

    await callback.answer()
    try:
        await callback.message.edit_text(
            text,
            reply_markup=AdminKeyboards.back_button(lang, "admin:reports")
        )
    except TelegramBadRequest:
        await callback.message.answer(
            text,
            reply_markup=AdminKeyboards.back_button(lang, "admin:reports")
        )


async def _get_top_questions(
    bot_session: AsyncSession,
    start_date: datetime
) -> str:
    """Get top 10 non-template questions."""
    # Get user messages that have AI responses (not errors or special actions)
    result = await bot_session.execute(
        select(ChatHistory).where(
            ChatHistory.created_at >= start_date,
            ChatHistory.role == MessageRole.USER.value
        ).order_by(ChatHistory.created_at.desc()).limit(1000)
    )
    messages = list(result.scalars().all())

    if not messages:
        return "(no data)"

    # Filter and normalize questions
    questions = []
    for msg in messages:
        content = msg.content.strip()

        # Skip very short messages
        if len(content) < 10:
            continue

        # Skip messages that look like greetings or off-topic
        if re.match(r'^(hi|hello|hey|привет|здравствуй|салом|сәлем)', content.lower()):
            continue

        # Normalize: lowercase, remove extra spaces
        normalized = ' '.join(content.lower().split())

        # Truncate for grouping
        if len(normalized) > 100:
            normalized = normalized[:100]

        questions.append(normalized)

    # Count and get top 10
    counter = Counter(questions)
    top_10 = counter.most_common(10)

    if not top_10:
        return "(no data)"

    lines = []
    for i, (question, count) in enumerate(top_10, 1):
        # Truncate for display
        display = question[:60] + "..." if len(question) > 60 else question
        lines.append(f"`{i}. {display}` ({count})")

    return "\n".join(lines)
