import numpy as np
import pytest

from agents.recommendation import agent as agent_module


class FakeModel:
    def __init__(self):
        self.encoded_texts = []

    def encode(self, texts):
        self.encoded_texts.extend(texts)
        return np.array([[0.1, 0.2, 0.3]])


class FakeRetriever:
    def __init__(self):
        self.calls = []
        self.results = []

    def retrieve_candidates(self, **kwargs):
        self.calls.append(kwargs)
        return self.results


class FakeScorer:
    def __init__(self, user_id):
        self.user_id = user_id
        self.calls = []
        self.result = []

    def rank_products(self, candidates, user_embedding, **kwargs):
        self.calls.append((candidates, user_embedding, kwargs))
        return self.result


class FakeBM25:
    def __init__(self):
        self.build_calls = []
        self.search_calls = []
        self.results = []

    def build(self, product_type):
        self.build_calls.append(product_type)

    def search(self, query_text, top_k=20):
        self.search_calls.append((query_text, top_k))
        return self.results


class FakeReranker:
    def __init__(self):
        self.calls = []
        self.result = []

    def rerank(self, query_text, ranked, top_k=3):
        self.calls.append((query_text, ranked, top_k))
        return self.result


def _build_agent(monkeypatch, adapted_profile):
    fake_model = FakeModel()
    fake_retriever = FakeRetriever()
    fake_scorer = FakeScorer("u1")
    fake_bm25 = FakeBM25()
    fake_reranker = FakeReranker()

    monkeypatch.setattr(agent_module, "get_embedding_model", lambda: fake_model)
    monkeypatch.setattr(agent_module, "ProductRetriever", lambda: fake_retriever)
    monkeypatch.setattr(agent_module, "ProductScorer", lambda user_id: fake_scorer)
    monkeypatch.setattr(agent_module, "BM25Index", lambda: fake_bm25)
    monkeypatch.setattr(agent_module, "LLMReranker", lambda: fake_reranker)
    monkeypatch.setattr(agent_module, "adapt_profile", lambda profile: adapted_profile)
    monkeypatch.setattr(agent_module, "classify_product_type", lambda _: "laptop")

    agent = agent_module.RecommendationAgent("u1")
    return agent, fake_model, fake_retriever, fake_scorer, fake_bm25, fake_reranker


def test_recommendation_pipeline_profile_to_final_results(monkeypatch):
    # Arrange
    adapted = {
        "category": "laptop",
        "use_case": "gaming",
        "budget_min": 1000,
        "budget_max": 2000,
        "preferences": {"ram": "16GB"},
        "search_queries": ["gaming laptop"],
    }
    (
        agent,
        _model,
        fake_retriever,
        fake_scorer,
        fake_bm25,
        fake_reranker,
    ) = _build_agent(monkeypatch, adapted)

    semantic = {
        "product": {
            "title": "A",
            "price": 1500,
            "link": "x",
            "embedding": [0.1, 0.2, 0.3],
            "seller_score": 4,
            "category": "laptop",
        }
    }
    bm25 = {
        "title": "B",
        "price": 1400,
        "link": "y",
        "embedding": [0.1, 0.2, 0.3],
        "seller_score": 3,
        "category": "laptop",
    }

    fake_retriever.results = [semantic]
    fake_bm25.results = [bm25]
    fake_scorer.result = [{"title": "A", "link": "x", "final_score": 0.8}]
    fake_reranker.result = [{"title": "A", "link": "x", "final_score": 0.8}]

    # Act
    results = agent.recommend({"budget": "1000-2000"})

    # Assert
    assert results == [{"title": "A", "link": "x", "final_score": 0.8}]
    assert fake_bm25.build_calls == ["laptop"]
    assert fake_retriever.calls[0]["price_min"] == 1000
    assert fake_retriever.calls[0]["price_max"] == 2000
    assert fake_reranker.calls[0][0] == "gaming laptop"


def test_recommendation_raises_for_empty_profile(monkeypatch):
    # Arrange
    agent, *_ = _build_agent(monkeypatch, adapted_profile={})

    # Act / Assert
    with pytest.raises(ValueError, match="too empty"):
        agent.recommend({})


def test_recommendation_returns_empty_when_no_candidates(monkeypatch):
    # Arrange
    adapted = {
        "category": "laptop",
        "use_case": "work",
        "budget_min": None,
        "budget_max": None,
        "preferences": {},
        "search_queries": ["office laptop"],
    }
    (
        agent,
        _model,
        fake_retriever,
        fake_scorer,
        fake_bm25,
        fake_reranker,
    ) = _build_agent(monkeypatch, adapted)
    fake_retriever.results = []
    fake_bm25.results = []

    fake_scorer.rank_products = lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("rank_products should not be called")
    )
    fake_reranker.rerank = lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("rerank should not be called")
    )

    # Act
    results = agent.recommend({"budget": "3000-5000"})

    # Assert
    assert results == []
