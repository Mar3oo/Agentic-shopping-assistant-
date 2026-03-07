import numpy as np

from agents.recommendation.agent import RecommendationAgent
from agents.recommendation import agent as agent_module


class FakeModel:
    def encode(self, texts):
        return np.array([[0.3, 0.4, 0.5]])


class FakeRetriever:
    def retrieve_candidates(self, **kwargs):
        return [
            {
                "product": {
                    "title": "A",
                    "price": 1200,
                    "link": "link-a",
                    "embedding": [0.3, 0.4, 0.5],
                    "seller_score": 4,
                    "category": "laptop",
                }
            }
        ]


class FakeBM25:
    def __init__(self):
        self.build_calls = []

    def build(self, product_type=None):
        self.build_calls.append(product_type)

    def search(self, query_text, top_k=50):
        return [
            {
                "title": "A duplicate",
                "price": 1200,
                "link": "link-a",
                "embedding": [0.3, 0.4, 0.5],
                "seller_score": 4,
                "category": "laptop",
            },
            {
                "title": "B",
                "price": 1800,
                "link": "link-b",
                "embedding": [0.2, 0.2, 0.2],
                "seller_score": 3,
                "category": "laptop",
            },
        ]


class FakeScorer:
    def __init__(self, user_id):
        self.user_id = user_id
        self.last_candidate_count = 0

    def rank_products(self, candidates, user_embedding, **kwargs):
        self.last_candidate_count = len(candidates)
        return [
            {"title": "A", "link": "link-a", "final_score": 0.91},
            {"title": "B", "link": "link-b", "final_score": 0.77},
        ]


class FakeReranker:
    def rerank(self, query_text, ranked, top_k=3):
        return ranked[:top_k]


def test_recommendation_pipeline_runs_profile_to_final_ranking(monkeypatch, fake_profiles):
    # Arrange
    monkeypatch.setattr(agent_module, "get_embedding_model", lambda: FakeModel())
    monkeypatch.setattr(agent_module, "ProductRetriever", lambda: FakeRetriever())
    fake_scorer = FakeScorer("user_001")
    monkeypatch.setattr(agent_module, "ProductScorer", lambda user_id: fake_scorer)
    monkeypatch.setattr(agent_module, "BM25Index", lambda: FakeBM25())
    monkeypatch.setattr(agent_module, "LLMReranker", lambda: FakeReranker())
    monkeypatch.setattr(agent_module, "classify_product_type", lambda _: "laptop")

    agent = RecommendationAgent(user_id="user_001")

    # Act
    results = agent.recommend(fake_profiles[0], top_k=3)

    # Assert
    assert len(results) == 2
    assert results[0]["link"] == "link-a"
    assert fake_scorer.last_candidate_count == 2
