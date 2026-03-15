"""AI service for handling OpenAI-compatible API calls."""
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass

from openai import AsyncOpenAI
from openai import APIError, RateLimitError, APIConnectionError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    AIProvider, AIKey, AIModel,
    ChatSession, ChatHistory, TrainingMessage,
    PendingRequest
)
from database.models.chat import MessageRole, RequestStatus
from bot.services.training import TrainingService

logger = logging.getLogger(__name__)

# Keywords that trigger operator request
OPERATOR_KEYWORDS = [
    "оператор", "человек", "живой", "менеджер", "поддержка", "помощь",
    "operator", "human", "person", "manager", "support", "help me",
    "operator", "inson", "yordam", "qo'llab",
    "оператор", "адам", "менеджер", "комек"
]


@dataclass
class AIResponse:
    """AI response with metadata."""
    content: str
    action: Optional[str] = None  # call_people, ignore_offtopic
    model_used: Optional[str] = None
    provider_used: Optional[str] = None
    error: Optional[str] = None


class AIService:
    """Service for AI interactions with failover support."""

    def __init__(self, shared_session: AsyncSession, bot_session: AsyncSession):
        self.shared_session = shared_session
        self.bot_session = bot_session
        self.training_service = TrainingService(bot_session)

    async def get_response(
        self,
        user_id: int,
        message: str,
        session_id: int,
        lang: str = "ru"
    ) -> AIResponse:
        """
        Get AI response with full failover chain.

        1. Try default provider -> available key -> available model
        2. On failure, try other models of same provider
        3. On failure, try other keys/providers
        4. If all fail, return error
        """
        # Check for operator keywords first
        if self._check_operator_keywords(message):
            return AIResponse(
                content="",
                action="call_people"
            )

        # Build conversation context
        context = await self._build_context(user_id, session_id, message, lang)

        # Get available providers (default first)
        providers = await self._get_available_providers()

        if not providers:
            logger.error("No AI providers available")
            return AIResponse(
                content="",
                error="No AI providers configured"
            )

        last_error = None

        for provider in providers:
            # Get available keys for provider
            keys = await self._get_available_keys(provider.id)

            for key in keys:
                # Get available models for provider
                models = await self._get_available_models(provider.id)

                for model in models:
                    try:
                        response = await self._call_api(
                            provider, key, model, context
                        )

                        # Update model last_used
                        await self._update_model_usage(model.id)

                        # Parse response for special actions
                        action = self._parse_action(response)

                        return AIResponse(
                            content=response,
                            action=action,
                            model_used=model.model_name,
                            provider_used=provider.display_name
                        )

                    except RateLimitError as e:
                        logger.warning(f"Rate limit on key {key.id}: {e}")
                        await self._set_key_cooldown(key.id)
                        last_error = str(e)
                        continue

                    except APIError as e:
                        logger.error(f"API error with model {model.model_name}: {e}")
                        await self._log_model_error(model.id, str(e))

                        # Check if model should be deactivated
                        if "model not found" in str(e).lower() or "invalid model" in str(e).lower():
                            await self._deactivate_model(model.id)

                        last_error = str(e)
                        continue

                    except APIConnectionError as e:
                        logger.error(f"Connection error to {provider.base_url}: {e}")
                        last_error = str(e)
                        continue

                    except Exception as e:
                        logger.error(f"Unexpected error: {e}", exc_info=True)
                        last_error = str(e)
                        continue

        return AIResponse(
            content="",
            error=last_error or "All AI providers failed"
        )

    async def _build_context(
        self,
        user_id: int,
        session_id: int,
        current_message: str,
        lang: str
    ) -> List[Dict[str, str]]:
        """Build conversation context with training messages and history."""
        messages = []

        # Get training/system messages
        training_messages = await self.training_service.get_active_messages()

        for tm in training_messages:
            messages.append({
                "role": "system",
                "content": tm.content
            })

        # Add language instruction
        lang_instruction = {
            "ru": "Отвечай на русском языке.",
            "en": "Respond in English.",
            "uz": "O'zbek tilida javob bering.",
            "kz": "Қазақ тілінде жауап беріңіз."
        }.get(lang, "Respond in the user's language.")

        messages.append({
            "role": "system",
            "content": lang_instruction
        })

        # Add action instructions
        messages.append({
            "role": "system",
            "content": """Special actions (return ONLY these exact phrases when needed):
- If user asks for human operator/support: return exactly "[ACTION:CALL_PEOPLE]"
- If user's message is completely off-topic (not related to our service): return exactly "[ACTION:IGNORE_OFFTOPIC]"
Otherwise, provide a helpful response."""
        })

        # Get chat history (limit to prevent context overflow)
        result = await self.bot_session.execute(
            select(ChatHistory)
            .where(ChatHistory.session_id == session_id)
            .order_by(ChatHistory.created_at.desc())
            .limit(20)
        )
        history = result.scalars().all()

        # Check if we need context compression
        session_result = await self.bot_session.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()

        if session and session.context_summary:
            messages.append({
                "role": "system",
                "content": f"Previous conversation summary: {session.context_summary}"
            })

        # Add history in chronological order
        for msg in reversed(history):
            role = "user" if msg.role == MessageRole.USER.value else "assistant"
            messages.append({
                "role": role,
                "content": msg.content
            })

        # Add current message
        messages.append({
            "role": "user",
            "content": current_message
        })

        return messages

    async def _call_api(
        self,
        provider: AIProvider,
        key: AIKey,
        model: AIModel,
        messages: List[Dict[str, str]]
    ) -> str:
        """Call the AI API."""
        api_key = key.api_key if key.api_key != "-" else "dummy"

        client = AsyncOpenAI(
            api_key=api_key,
            base_url=provider.base_url,
            timeout=60.0
        )

        response = await client.chat.completions.create(
            model=model.model_name,
            messages=messages,
            max_tokens=2000,
            temperature=0.7,
        )

        # Increment request count
        await self._increment_key_requests(key.id)

        return response.choices[0].message.content or ""

    def _check_operator_keywords(self, message: str) -> bool:
        """Check if message contains operator request keywords."""
        message_lower = message.lower()
        return any(kw in message_lower for kw in OPERATOR_KEYWORDS)

    def _parse_action(self, response: str) -> Optional[str]:
        """Parse special action from AI response."""
        if "[ACTION:CALL_PEOPLE]" in response:
            return "call_people"
        if "[ACTION:IGNORE_OFFTOPIC]" in response:
            return "ignore_offtopic"
        return None

    async def _get_available_providers(self) -> List[AIProvider]:
        """Get available providers, default first."""
        result = await self.shared_session.execute(
            select(AIProvider)
            .where(AIProvider.is_active == True)
            .order_by(AIProvider.is_default.desc())
        )
        return list(result.scalars().all())

    async def _get_available_keys(self, provider_id: int) -> List[AIKey]:
        """Get available API keys for provider."""
        now = datetime.utcnow()
        result = await self.shared_session.execute(
            select(AIKey)
            .where(
                AIKey.provider_id == provider_id,
                AIKey.is_active == True,
                (AIKey.cooldown_until == None) | (AIKey.cooldown_until < now)
            )
        )
        return list(result.scalars().all())

    async def _get_available_models(self, provider_id: int) -> List[AIModel]:
        """Get available models for provider, default first."""
        result = await self.shared_session.execute(
            select(AIModel)
            .where(
                AIModel.provider_id == provider_id,
                AIModel.is_active == True
            )
            .order_by(AIModel.is_default.desc())
        )
        return list(result.scalars().all())

    async def _set_key_cooldown(self, key_id: int, minutes: int = 5) -> None:
        """Set cooldown on API key after rate limit."""
        await self.shared_session.execute(
            update(AIKey)
            .where(AIKey.id == key_id)
            .values(cooldown_until=datetime.utcnow() + timedelta(minutes=minutes))
        )

    async def _increment_key_requests(self, key_id: int) -> None:
        """Increment request counter on key."""
        result = await self.shared_session.execute(
            select(AIKey).where(AIKey.id == key_id)
        )
        key = result.scalar_one_or_none()
        if key:
            key.requests_made += 1

    async def _update_model_usage(self, model_id: int) -> None:
        """Update model last used timestamp."""
        await self.shared_session.execute(
            update(AIModel)
            .where(AIModel.id == model_id)
            .values(last_used_at=datetime.utcnow())
        )

    async def _log_model_error(self, model_id: int, error: str) -> None:
        """Log error for model."""
        result = await self.shared_session.execute(
            select(AIModel).where(AIModel.id == model_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.error_count += 1
            model.last_error = error
            model.last_error_at = datetime.utcnow()

    async def _deactivate_model(self, model_id: int) -> None:
        """Deactivate model due to error."""
        await self.shared_session.execute(
            update(AIModel)
            .where(AIModel.id == model_id)
            .values(is_active=False)
        )
        logger.warning(f"Model {model_id} deactivated due to API error")

    async def compress_context(self, session_id: int) -> None:
        """Compress old conversation history into summary."""
        # Get old messages (keep last 10, compress rest)
        result = await self.bot_session.execute(
            select(ChatHistory)
            .where(ChatHistory.session_id == session_id)
            .order_by(ChatHistory.created_at.asc())
        )
        all_messages = list(result.scalars().all())

        if len(all_messages) <= 20:
            return  # Not enough messages to compress

        to_compress = all_messages[:-10]

        # Build text to summarize
        text_parts = []
        for msg in to_compress:
            role = "User" if msg.role == MessageRole.USER.value else "Assistant"
            text_parts.append(f"{role}: {msg.content}")

        text_to_summarize = "\n".join(text_parts)

        # Get AI to summarize
        providers = await self._get_available_providers()
        if not providers:
            return

        provider = providers[0]
        keys = await self._get_available_keys(provider.id)
        if not keys:
            return

        key = keys[0]
        models = await self._get_available_models(provider.id)
        if not models:
            return

        model = models[0]

        try:
            summary = await self._call_api(
                provider, key, model,
                [
                    {"role": "system", "content": "Summarize this conversation briefly, keeping key points:"},
                    {"role": "user", "content": text_to_summarize}
                ]
            )

            # Update session with summary
            session_result = await self.bot_session.execute(
                select(ChatSession).where(ChatSession.id == session_id)
            )
            session = session_result.scalar_one_or_none()
            if session:
                session.context_summary = summary

            # Delete old messages
            for msg in to_compress:
                await self.bot_session.delete(msg)

            logger.info(f"Compressed {len(to_compress)} messages for session {session_id}")

        except Exception as e:
            logger.error(f"Failed to compress context: {e}")
