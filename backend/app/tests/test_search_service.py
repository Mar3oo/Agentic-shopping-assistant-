import time
import unittest
from unittest.mock import patch

from backend.app.services import search_service


class SearchServiceTests(unittest.TestCase):
    def setUp(self):
        search_service._SEARCH_CACHE.clear()

    @patch("backend.app.services.search_service.insert_search_history")
    @patch("backend.app.services.search_service.upsert_search_session")
    @patch("backend.app.services.search_service.ensure_user")
    @patch("backend.app.services.search_service.enforce_rate_limit")
    def test_cache_hit_skips_pipeline_and_persists_session_history(
        self,
        mock_rate_limit,
        mock_ensure_user,
        mock_upsert_session,
        mock_insert_history,
    ):
        cached_products = [{"title": "Gaming Laptop"}]
        search_service._SEARCH_CACHE["gaming laptop under 1500"] = {
            "data": cached_products,
            "timestamp": time.time(),
        }

        with patch.object(search_service.pipeline, "run") as mock_pipeline_run:
            response = search_service.run_search(
                user_id="user_1",
                message="  Gaming   Laptop Under 1500  ",
            )

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"]["products"], cached_products)
        mock_rate_limit.assert_called_once_with("user_1", "search", limit=20, window_seconds=60)
        mock_ensure_user.assert_called_once_with("user_1")
        mock_pipeline_run.assert_not_called()
        mock_upsert_session.assert_called_once_with(
            user_id="user_1",
            query="Gaming   Laptop Under 1500",
            results=cached_products,
        )
        mock_insert_history.assert_called_once_with(
            user_id="user_1",
            query="Gaming   Laptop Under 1500",
            results_count=1,
        )

    @patch("backend.app.services.search_service.insert_search_history")
    @patch("backend.app.services.search_service.upsert_search_session")
    @patch("backend.app.services.search_service.ensure_user")
    @patch("backend.app.services.search_service.enforce_rate_limit")
    def test_cache_miss_runs_pipeline_and_populates_cache(
        self,
        mock_rate_limit,
        mock_ensure_user,
        mock_upsert_session,
        mock_insert_history,
    ):
        products = [{"title": "Budget Laptop"}, {"title": "Creator Laptop"}]

        with patch.object(search_service.pipeline, "run", return_value=products) as mock_pipeline_run:
            response = search_service.run_search(
                user_id="user_2",
                message="budget laptop",
            )

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"]["products"], products)
        mock_rate_limit.assert_called_once_with("user_2", "search", limit=20, window_seconds=60)
        mock_ensure_user.assert_called_once_with("user_2")
        mock_pipeline_run.assert_called_once_with(
            query="budget laptop",
            search_limit=10,
            top_k=5,
        )
        self.assertIn("budget laptop", search_service._SEARCH_CACHE)
        mock_upsert_session.assert_called_once_with(
            user_id="user_2",
            query="budget laptop",
            results=products,
        )
        mock_insert_history.assert_called_once_with(
            user_id="user_2",
            query="budget laptop",
            results_count=2,
        )

    @patch("backend.app.services.search_service.insert_search_history")
    @patch("backend.app.services.search_service.upsert_search_session")
    @patch("backend.app.services.search_service.ensure_user")
    @patch("backend.app.services.search_service.enforce_rate_limit")
    def test_expired_cache_entry_triggers_pipeline(
        self,
        mock_rate_limit,
        mock_ensure_user,
        mock_upsert_session,
        mock_insert_history,
    ):
        search_service._SEARCH_CACHE["gaming monitor"] = {
            "data": [{"title": "Old Monitor"}],
            "timestamp": time.time() - (search_service._SEARCH_CACHE_TTL_SECONDS + 1),
        }
        products = [{"title": "Fresh Monitor"}]

        with patch.object(search_service.pipeline, "run", return_value=products) as mock_pipeline_run:
            response = search_service.run_search(
                user_id="user_3",
                message="gaming monitor",
            )

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"]["products"], products)
        mock_rate_limit.assert_called_once_with("user_3", "search", limit=20, window_seconds=60)
        mock_ensure_user.assert_called_once_with("user_3")
        mock_pipeline_run.assert_called_once_with(
            query="gaming monitor",
            search_limit=10,
            top_k=5,
        )
        mock_upsert_session.assert_called_once_with(
            user_id="user_3",
            query="gaming monitor",
            results=products,
        )
        mock_insert_history.assert_called_once_with(
            user_id="user_3",
            query="gaming monitor",
            results_count=1,
        )


if __name__ == "__main__":
    unittest.main()
