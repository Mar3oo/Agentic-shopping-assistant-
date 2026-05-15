from backend.agents.profile.agent import run_profile_agent
from backend.agents.recommendation.agent import RecommendationAgent
from backend.agents.recommendation.chat_handler import RecommendationChatHandler
from backend.agents.recommendation.profile_adapter import adapt_profile

from backend.database.profile_repo import get_profile, save_profile
from backend.app.services.rate_limit_service import enforce_rate_limit
from backend.app.services.session_service import (
    append_assistant_message,
    append_user_message,
    close_session_for_user,
    load_session,
    open_session,
    persist_session_state,
    recent_history,
)


def _t(language: str, en: str, ar: str) -> str:
    return ar if language == "ar" else en


def _suggestions(language: str) -> list[dict]:
    return [
        {
            "type": "compare",
            "trigger": "after_recommendations",
            "message": _t(
                language,
                "Want help comparing these products?",
                "هل تريد المساعدة في مقارنة هذه المنتجات؟",
            ),
        },
        {
            "type": "review",
            "trigger": "after_recommendations",
            "message": _t(
                language,
                "Want to check real user reviews?",
                "هل تريد الاطلاع على مراجعات المستخدمين الحقيقية؟",
            ),
        },
    ]


def _selected_links(products: list[dict]) -> list[str]:
    return [
        product["link"]
        for product in products
        if isinstance(product, dict) and product.get("link")
    ]


def _recommendation_state(
    raw_profile: dict,
    adapted_profile: dict,
    products: list[dict],
    language: str,
) -> dict:
    return {
        "raw_profile_snapshot": raw_profile,
        "adapted_profile": adapted_profile,
        "last_recommendations": products,
        "selected_links": _selected_links(products),
        "mode": "recommendation",
        "language": language,
    }


def _initialize_recommendation_session(
    user_id: str,
    session_id: str,
    message: str,
    language: str = "en",
) -> dict:
    parsed, _ = run_profile_agent(
        message,
        language=language,
    )
    raw_profile = parsed.profile.model_dump()
    save_profile(user_id, raw_profile)

    adapted_profile = adapt_profile(raw_profile)
    products = RecommendationAgent(user_id).recommend(adapted_profile)

    persist_session_state(
        user_id,
        session_id,
        _recommendation_state(raw_profile, adapted_profile, products, language),
        last_response_type="recommendation_update",
        status="active",
        last_error=None,
    )
    append_assistant_message(
        user_id,
        session_id,
        "recommendation",
        _t(
            language,
            "Here are some recommendations",
            "هذه بعض التوصيات المناسبة لك",
        ),
        payload={"products": products},
    )

    return {
        "status": "success",
        "type": "recommendations",
        "message": _t(
            language,
            "Here are some products for you",
            "هذه بعض المنتجات المناسبة لك",
        ),
        "session_id": session_id,
        "data": {"products": products, "suggestions": _suggestions(language)},
    }


def _open_reset_recommendation_session(
    user_id: str,
    message: str,
    language: str = "en",
) -> str:
    session = open_session(user_id=user_id, agent_type="recommendation", title=message)
    session_id = session["session_id"]
    prompt = _t(
        language,
        "Starting a new search. What are you looking for?",
        "بدأنا عملية بحث جديدة، ما المنتج الذي تبحث عنه؟",
    )
    append_user_message(user_id, session_id, "recommendation", message)
    persist_session_state(
        user_id,
        session_id,
        {},
        last_response_type="recommendation_prompt",
        status="active",
        last_error=None,
    )
    append_assistant_message(
        user_id,
        session_id,
        "recommendation",
        prompt,
        payload={"type": "new_search", "data": {"message": prompt}},
        metadata={"reset": True},
    )
    return session_id


def start_recommendation(
    user_id: str,
    message: str,
    language: str = "en",
) -> dict:
    enforce_rate_limit(user_id, "recommendation_start", limit=10, window_seconds=60)

    session = open_session(user_id=user_id, agent_type="recommendation", title=message)
    session_id = session["session_id"]
    append_user_message(user_id, session_id, "recommendation", message)
    try:
        return _initialize_recommendation_session(
            user_id, session_id, message, language
        )
    except Exception as exc:
        persist_session_state(
            user_id,
            session_id,
            {},
            status="error",
            last_error=str(exc),
        )
        append_assistant_message(
            user_id,
            session_id,
            "recommendation",
            "Recommendation request failed",
            payload={"error": str(exc)},
        )
        return {
            "status": "error",
            "type": "recommendations",
            "message": str(exc),
            "session_id": session_id,
            "data": {},
        }


def chat_recommendation(
    user_id: str,
    session_id: str,
    message: str,
    language: str = "en",
) -> dict:
    enforce_rate_limit(user_id, "recommendation_chat", limit=20, window_seconds=60)

    session = load_session(
        user_id,
        session_id,
        agent_type="recommendation",
        require_active=True,
    )
    if not session:
        return {
            "status": "error",
            "type": "recommendations",
            "message": "No active session. Start with /recommendation/start",
            "data": {},
        }

    agent_state = session.get("agent_state", {})
    session_language = agent_state.get("language", language)
    session_has_context = any(
        [
            agent_state.get("raw_profile_snapshot"),
            agent_state.get("adapted_profile"),
            agent_state.get("last_recommendations"),
        ]
    )

    if not session_has_context:
        append_user_message(user_id, session_id, "recommendation", message)
        try:
            if language == "en":
                return _initialize_recommendation_session(user_id, session_id, message)
            return _initialize_recommendation_session(
                user_id,
                session_id,
                message,
                language,
            )
        except Exception as exc:
            persist_session_state(
                user_id,
                session_id,
                {},
                status="error",
                last_error=str(exc),
            )
            append_assistant_message(
                user_id,
                session_id,
                "recommendation",
                "Recommendation request failed",
                payload={"error": str(exc)},
            )
            return {
                "status": "error",
                "type": "recommendations",
                "message": str(exc),
                "session_id": session_id,
                "data": {},
            }

    raw_profile = agent_state.get("raw_profile_snapshot") or get_profile(user_id)
    adapted_profile = agent_state.get("adapted_profile") or adapt_profile(
        raw_profile or {}
    )
    current_recommendations = agent_state.get("last_recommendations") or []

    if not current_recommendations:
        current_recommendations = RecommendationAgent(user_id).recommend(
            adapted_profile
        )

    try:
        response = RecommendationChatHandler(user_id).handle(
            user_message=message,
            current_profile=adapted_profile,
            current_recommendations=current_recommendations,
            language=session_language,
            conversation_history=recent_history(user_id, session_id, limit=12),
        )
    except Exception as exc:
        persist_session_state(
            user_id,
            session_id,
            agent_state,
            status="error",
            last_error=str(exc),
        )
        append_user_message(user_id, session_id, "recommendation", message)
        append_assistant_message(
            user_id,
            session_id,
            "recommendation",
            "Recommendation chat failed",
            payload={"error": str(exc)},
        )
        return {
            "status": "error",
            "type": "message",
            "message": str(exc),
            "session_id": session_id,
            "data": {},
        }

    if response.get("type") == "new_search":
        close_session_for_user(user_id, session_id)
        if session_language == "en":
            new_session_id = _open_reset_recommendation_session(user_id, message)
        else:
            new_session_id = _open_reset_recommendation_session(
                user_id,
                message,
                session_language,
            )
        return {
            "status": "success",
            "type": "reset",
            "message": _t(
                session_language,
                "Starting a new search",
                "بدأنا عملية بحث جديدة",
            ),
            "session_id": new_session_id,
            "data": {},
        }

    append_user_message(user_id, session_id, "recommendation", message)

    next_profile = response.get("profile", adapted_profile)
    next_raw_profile = raw_profile or {}
    next_recommendations = current_recommendations

    if response.get("type") == "recommendation_update":
        next_recommendations = response["data"]

    if not next_raw_profile and next_profile:
        next_raw_profile = next_profile

    persist_session_state(
        user_id,
        session_id,
        _recommendation_state(
            next_raw_profile,
            next_profile,
            next_recommendations,
            session_language,
        ),
        last_response_type=response.get("type"),
        status="active",
        last_error=None,
    )

    assistant_text = response.get("data")
    if isinstance(assistant_text, list):
        assistant_text = _t(
            session_language,
            "Updated recommendations",
            "تم تحديث التوصيات",
        )
    elif isinstance(assistant_text, dict):
        assistant_text = assistant_text.get("message", "Recommendation response")
    append_assistant_message(
        user_id,
        session_id,
        "recommendation",
        assistant_text or "Recommendation response",
        payload=response,
    )

    if response["type"] == "recommendation_update":
        return {
            "status": "success",
            "type": "recommendations",
            "message": _t(
                session_language,
                "Updated recommendations",
                "تم تحديث التوصيات",
            ),
            "session_id": session_id,
            "data": {
                "products": response["data"],
                "suggestions": _suggestions(session_language),
            },
        }

    if response["type"] == "message":
        return {
            "status": "success",
            "type": "message",
            "message": response["data"],
            "session_id": session_id,
            "data": {},
        }

    return {
        "status": "error",
        "type": "message",
        "message": "Something went wrong",
        "session_id": session_id,
        "data": {},
    }
