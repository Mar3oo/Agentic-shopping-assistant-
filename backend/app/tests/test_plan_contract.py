import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from agents.comparison.agent import ComparisonAgent
from agents.reviews.agent import ReviewAgent
from backend.app.main import rate_limit_exception_handler
from backend.app.routes.session import router as session_router
from backend.app.services.cache_service import build_cache_key
from backend.app.services.rate_limit_service import RateLimitExceeded, enforce_rate_limit
from backend.app.services.recommendation_service import chat_recommendation


class SessionRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(session_router)
        self.client = TestClient(self.app)

    @patch("backend.app.routes.session.list_messages_for_session")
    @patch("backend.app.routes.session.load_session")
    def test_messages_endpoint_passes_limit(self, mock_load_session, mock_list_messages):
        mock_load_session.return_value = {"session_id": "session_1", "status": "active"}
        mock_list_messages.return_value = []

        response = self.client.get(
            "/sessions/session_1/messages",
            params={"user_id": "user_1", "limit": 7},
        )

        self.assertEqual(response.status_code, 200)
        mock_list_messages.assert_called_once_with("user_1", "session_1", limit=7)


class RateLimitTests(unittest.TestCase):
    def test_rate_limit_exception_payload_matches_plan(self):
        app = FastAPI()
        app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)

        @app.get("/limited")
        def limited():
            enforce_rate_limit("user_1", "test_scope", limit=1, window_seconds=60)
            enforce_rate_limit("user_1", "test_scope", limit=1, window_seconds=60)
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/limited")

        self.assertEqual(response.status_code, 429)
        body = response.json()
        self.assertEqual(body["message"], "Rate limit exceeded")
        self.assertEqual(body["limit"], 1)
        self.assertIn("retry_after_seconds", body)
        self.assertNotIn("detail", body)


class CacheServiceTests(unittest.TestCase):
    def test_cache_key_normalization_ignores_case_and_spacing(self):
        key_a = build_cache_key("search", {"message": "  Gaming   Laptop ", "top_k": 5})
        key_b = build_cache_key("search", {"message": "gaming laptop", "top_k": 5})
        self.assertEqual(key_a, key_b)


class AgentStateTests(unittest.TestCase):
    def test_comparison_state_round_trip_includes_serialized_fields(self):
        agent = ComparisonAgent()
        agent.products = ["iphone 15", "galaxy s24"]
        agent.comparison_active = True
        agent.search_queries = ["iphone 15 vs galaxy s24 comparison"]
        agent.source_urls = ["https://example.com/compare"]
        agent.raw_contents = ["cleaned page text"]
        agent.comparison_result = {"summary": "test"}

        restored = ComparisonAgent.from_state(agent.to_state())

        self.assertEqual(restored.products, agent.products)
        self.assertEqual(restored.search_queries, agent.search_queries)
        self.assertEqual(restored.source_urls, agent.source_urls)
        self.assertEqual(restored.comparison_result, agent.comparison_result)

    def test_review_state_round_trip_includes_query_and_sources(self):
        agent = ReviewAgent()
        agent.product = "iphone 15"
        agent.query = "iphone 15 honest review"
        agent.sources = [{"url": "https://youtube.com/watch?v=1"}]
        agent.reviews_data = {"summary": "test"}

        restored = ReviewAgent.from_state(agent.to_state())

        self.assertEqual(restored.product, agent.product)
        self.assertEqual(restored.query, agent.query)
        self.assertEqual(restored.sources, agent.sources)
        self.assertEqual(restored.reviews_data, agent.reviews_data)

    def test_comparison_parser_requires_two_products_for_new_task(self):
        agent = ComparisonAgent()
        self.assertFalse(agent._is_new_comparison("compare battery life"))
        self.assertTrue(agent._is_new_comparison("iphone 15 vs galaxy s24"))

    def test_review_new_task_detection_avoids_followup_questions(self):
        agent = ReviewAgent()
        self.assertFalse(agent._is_new_review("what are the bad reviews?"))
        self.assertTrue(agent._is_new_review("iphone 15 reviews"))


class RecommendationFlowTests(unittest.TestCase):
    @patch("backend.app.services.recommendation_service._initialize_recommendation_session")
    @patch("backend.app.services.recommendation_service.append_user_message")
    @patch("backend.app.services.recommendation_service.load_session")
    @patch("backend.app.services.recommendation_service.enforce_rate_limit")
    def test_empty_recommendation_session_initializes_from_chat(
        self,
        _mock_rate_limit,
        mock_load_session,
        mock_append_user_message,
        mock_initialize,
    ):
        mock_load_session.return_value = {
            "session_id": "session_1",
            "agent_type": "recommendation",
            "status": "active",
            "agent_state": {},
        }
        mock_initialize.return_value = {
            "status": "success",
            "type": "recommendations",
            "session_id": "session_1",
            "data": {"products": []},
        }

        response = chat_recommendation("user_1", "session_1", "gaming laptop under 1500")

        self.assertEqual(response["type"], "recommendations")
        mock_append_user_message.assert_called_once_with(
            "user_1",
            "session_1",
            "recommendation",
            "gaming laptop under 1500",
        )
        mock_initialize.assert_called_once_with(
            "user_1",
            "session_1",
            "gaming laptop under 1500",
        )

    @patch("backend.app.services.recommendation_service._open_reset_recommendation_session")
    @patch("backend.app.services.recommendation_service.close_session_for_user")
    @patch("backend.app.services.recommendation_service.RecommendationChatHandler")
    @patch("backend.app.services.recommendation_service.recent_history")
    @patch("backend.app.services.recommendation_service.load_session")
    @patch("backend.app.services.recommendation_service.enforce_rate_limit")
    def test_new_search_opens_new_session(
        self,
        _mock_rate_limit,
        mock_load_session,
        mock_recent_history,
        mock_handler_cls,
        mock_close_session,
        mock_open_reset,
    ):
        mock_load_session.return_value = {
            "session_id": "session_old",
            "agent_type": "recommendation",
            "status": "active",
            "agent_state": {
                "raw_profile_snapshot": {"category": "laptop"},
                "adapted_profile": {"category": "laptop"},
                "last_recommendations": [{"link": "https://example.com/p1"}],
            },
        }
        mock_recent_history.return_value = []
        mock_handler_cls.return_value.handle.return_value = {
            "type": "new_search",
            "data": {"message": "Starting a new search. What are you looking for?"},
        }
        mock_open_reset.return_value = "session_new"

        response = chat_recommendation("user_1", "session_old", "new search")

        self.assertEqual(response["type"], "reset")
        self.assertEqual(response["session_id"], "session_new")
        mock_close_session.assert_called_once_with("user_1", "session_old")
        mock_open_reset.assert_called_once_with("user_1", "new search")


if __name__ == "__main__":
    unittest.main()
