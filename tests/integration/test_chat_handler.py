from types import SimpleNamespace

from agents.recommendation import chat_handler as chat_module


class _FakeGroq:
    def __init__(self, *args, **kwargs):
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **kw: SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content="llm response"))]
                )
            )
        )


def _build_handler(monkeypatch, intent_data, recommendation_result=None):
    class FakeRouter:
        def __init__(self, api_key=None):
            self.api_key = api_key

        def route(self, user_message, current_recommendations):
            return intent_data

    class FakeRecAgent:
        def __init__(self, user_id):
            self.user_id = user_id
            self.calls = []

        def recommend(self, profile):
            self.calls.append(dict(profile))
            if recommendation_result is None:
                return [{"title": "Recommended", "price": 1000, "link": "r1"}]
            return recommendation_result

    monkeypatch.setattr(chat_module, "RecommendationIntentRouter", FakeRouter)
    monkeypatch.setattr(chat_module, "RecommendationAgent", FakeRecAgent)
    monkeypatch.setattr(chat_module, "Groq", _FakeGroq)

    return chat_module.RecommendationChatHandler(user_id="user_001")


def test_chat_handler_refine_budget_updates_profile_and_returns_new_recommendations(
    monkeypatch,
):
    # Arrange
    handler = _build_handler(
        monkeypatch,
        {"intent": "refine_budget", "budget_min": 1000, "budget_max": 2000},
        recommendation_result=[{"title": "A", "price": 1500, "link": "a"}],
    )
    profile = {"budget_min": 500, "budget_max": 3000}

    # Act
    response = handler.handle("keep it under 2000", profile, [])

    # Assert
    assert profile["budget_min"] == 1000
    assert profile["budget_max"] == 2000
    assert response == {
        "type": "recommendation_update",
        "data": [{"title": "A", "price": 1500, "link": "a"}],
    }
    assert len(handler.rec_agent.calls) == 1


def test_chat_handler_refine_brand_filters_case_insensitive(monkeypatch):
    # Arrange
    handler = _build_handler(monkeypatch, {"intent": "refine_brand", "brand": "lenovo"})
    recommendations = [
        {"title": "Lenovo Legion", "price": 1200, "link": "a"},
        {"title": "ASUS TUF", "price": 1300, "link": "b"},
        {"title": "LENOVO IdeaPad", "price": 1100, "link": "c"},
    ]

    # Act
    response = handler.handle("show lenovo only", {}, recommendations)

    # Assert
    assert response["type"] == "recommendation_update"
    assert len(response["data"]) == 2
    assert all("lenovo" in p["title"].lower() for p in response["data"])


def test_chat_handler_explanation_request_calls_explainer(monkeypatch):
    # Arrange
    handler = _build_handler(monkeypatch, {"intent": "ask_explanation"})
    monkeypatch.setattr(handler, "_generate_explanation", lambda p, r: "Because of budget and use case")

    # Act
    response = handler.handle("why these?", {"budget_min": 1000}, [{"title": "A"}])

    # Assert
    assert response == {"type": "message", "data": "Because of budget and use case"}


def test_chat_handler_returns_fallback_for_unknown_intent(monkeypatch):
    # Arrange
    handler = _build_handler(monkeypatch, {"intent": "something_else"})

    # Act
    response = handler.handle("???", {}, [])

    # Assert
    assert response["type"] == "message"
    assert "Could you clarify" in response["data"]
