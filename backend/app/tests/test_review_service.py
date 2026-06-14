import unittest
from unittest.mock import patch

from backend.app.services import review_service


class ReviewServiceTests(unittest.TestCase):
    @patch("backend.app.services.review_service.append_assistant_message")
    @patch("backend.app.services.review_service.persist_session_state")
    @patch("backend.app.services.review_service.append_user_message")
    @patch("backend.app.services.review_service.open_session")
    @patch("backend.app.services.review_service.enforce_rate_limit")
    @patch("backend.app.services.review_service.store_cached_response")
    @patch("backend.app.services.review_service.load_cached_response")
    @patch("backend.app.services.review_service.ReviewAgent")
    def test_review_cache_fingerprint_includes_language(
        self,
        mock_agent_cls,
        mock_load_cached,
        mock_store_cached,
        _mock_rate_limit,
        mock_open_session,
        _mock_append_user,
        _mock_persist_state,
        _mock_append_assistant,
    ):
        fingerprint = {"message": "review iPhone 17", "language": "ar"}
        mock_open_session.return_value = {"session_id": "session_1"}
        mock_load_cached.return_value = None
        agent = mock_agent_cls.return_value
        agent.start_review.return_value = {"summary": "مراجعة عربية"}
        agent.to_state.return_value = {"product": "iPhone 17", "language": "ar"}

        response = review_service.start_review(
            user_id="user_1",
            message="review iPhone 17",
            language="ar",
        )

        self.assertEqual(response["message"], "هذه مراجعات المنتج")
        mock_load_cached.assert_called_once_with("review", fingerprint)
        mock_store_cached.assert_called_once_with(
            "review",
            fingerprint,
            {
                "result": {"summary": "مراجعة عربية"},
                "agent_state": {"product": "iPhone 17", "language": "ar"},
            },
        )


if __name__ == "__main__":
    unittest.main()
