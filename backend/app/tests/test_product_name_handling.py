import unittest
from unittest.mock import patch

from agents.comparison.agent import ComparisonAgent
from agents.reviews.agent import ReviewAgent


class ReviewProductNameTests(unittest.TestCase):
    @patch("agents.reviews.agent.analyze_reviews")
    @patch("agents.reviews.agent.get_transcripts_for_videos")
    @patch("agents.reviews.agent.search_youtube")
    @patch("agents.reviews.agent.extract_clean_product_name")
    def test_review_agent_uses_clean_name_for_youtube_query(
        self,
        mock_extract_clean_name,
        mock_search_youtube,
        mock_get_transcripts,
        mock_analyze_reviews,
    ):
        mock_extract_clean_name.return_value = "HP EliteBook 845 G8"
        mock_search_youtube.return_value = [
            {
                "title": "Review video",
                "video_id": "video_1",
                "link": "https://youtube.com/watch?v=video_1",
            }
        ]
        mock_get_transcripts.return_value = ["Great laptop review transcript"]
        mock_analyze_reviews.return_value = {"summary": "Solid business laptop"}

        agent = ReviewAgent()
        result = agent.start_review(
            'reviews for HP EliteBook 845 G8 | AMD Ryzen 5 Pro | 14" inch | RAM 16GB | Hardisk 256GB SSD Silver',
        )

        self.assertEqual(agent.product, "HP EliteBook 845 G8")
        self.assertEqual(agent.query, "HP EliteBook 845 G8 honest review")
        mock_search_youtube.assert_called_once_with("HP EliteBook 845 G8 honest review")
        mock_analyze_reviews.assert_called_once_with(
            "HP EliteBook 845 G8",
            ["Great laptop review transcript"],
        )
        self.assertEqual(result["summary"], "Solid business laptop")


class ComparisonProductNameTests(unittest.TestCase):
    @patch.object(ComparisonAgent, "run_comparison_pipeline", return_value={"summary": "Comparison ready"})
    @patch("agents.comparison.agent.extract_clean_product_mappings")
    def test_comparison_agent_keeps_only_two_clean_products(
        self,
        mock_extract_mappings,
        _mock_run_pipeline,
    ):
        mock_extract_mappings.return_value = [
            {
                "product_full": "Apple iPhone 15 Pro Max 256GB Blue Titanium",
                "product_clean": "Apple iPhone 15 Pro Max",
            },
            {
                "product_full": "Samsung Galaxy S24 128GB Onyx Black",
                "product_clean": "Samsung Galaxy S24",
            },
            {
                "product_full": "Google Pixel 8 128GB Hazel",
                "product_clean": "Google Pixel 8",
            },
        ]

        agent = ComparisonAgent()
        result = agent.start_comparison(
            "compare Apple iPhone 15 Pro Max 256GB Blue Titanium and Samsung Galaxy S24 128GB Onyx Black and Google Pixel 8 128GB Hazel",
        )

        self.assertEqual(result["summary"], "Comparison ready")
        self.assertEqual(
            agent.products,
            ["Apple iPhone 15 Pro Max", "Samsung Galaxy S24"],
        )
        self.assertEqual(
            agent.product_pairs,
            [
                {
                    "product_clean": "Apple iPhone 15 Pro Max",
                    "product_full": "Apple iPhone 15 Pro Max 256GB Blue Titanium",
                },
                {
                    "product_clean": "Samsung Galaxy S24",
                    "product_full": "Samsung Galaxy S24 128GB Onyx Black",
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
