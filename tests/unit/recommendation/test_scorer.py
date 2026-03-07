import numpy as np
import pytest

from agents.recommendation import scorer as scorer_module


def test_cosine_similarity_uses_dot_product_for_normalized_vectors():
    # Arrange
    scorer = scorer_module.ProductScorer(user_id="u1")
    a = np.array([1.0, 0.0, 0.0])
    b = np.array([0.8, 0.2, 0.0])

    # Act
    similarity = scorer._cosine_similarity(a, b)

    # Assert
    assert similarity == pytest.approx(0.8)


def test_price_score_handles_budget_boundaries():
    # Arrange
    scorer = scorer_module.ProductScorer(user_id="u1")

    # Act
    neutral = scorer._price_score(1000, None, None)
    center = scorer._price_score(1500, 1000, 2000)
    outside = scorer._price_score(3000, 1000, 2000)
    exact_same_bounds = scorer._price_score(1500, 1500, 1500)

    # Assert
    assert neutral == pytest.approx(0.5)
    assert center == pytest.approx(1.0)
    assert outside == pytest.approx(0.0)
    assert exact_same_bounds == pytest.approx(1.0)


def test_seller_score_normalization_clamps_values():
    # Arrange
    scorer = scorer_module.ProductScorer(user_id="u1")

    # Act
    missing = scorer._seller_score(None)
    low = scorer._seller_score(-3)
    middle = scorer._seller_score(2.5)
    high = scorer._seller_score(10)

    # Assert
    assert missing == pytest.approx(0.0)
    assert low == pytest.approx(0.0)
    assert middle == pytest.approx(0.5)
    assert high == pytest.approx(1.0)


def test_rank_products_boosts_liked_products_and_sorts_descending(monkeypatch):
    # Arrange
    monkeypatch.setattr(
        scorer_module,
        "get_user_feedback",
        lambda user_id: [{"product_link": "p2", "liked": True}],
    )

    scorer = scorer_module.ProductScorer(user_id="u1")
    user_embedding = np.array([1.0, 0.0, 0.0])

    products = [
        {
            "product": {
                "title": "Product 1",
                "price": 1500,
                "link": "p1",
                "category": "laptop",
                "seller_score": 5,
                "embedding": [0.95, 0.0, 0.0],
            }
        },
        {
            "product": {
                "title": "Product 2",
                "price": 1500,
                "link": "p2",
                "category": "laptop",
                "seller_score": 5,
                "embedding": [0.90, 0.0, 0.0],
            }
        },
    ]

    # Act
    ranked = scorer.rank_products(products, user_embedding, 1000, 2000, top_k=2)

    # Assert
    assert ranked[0]["link"] == "p2"
    assert ranked[0]["final_score"] >= ranked[1]["final_score"]


def test_rank_products_raises_on_corrupted_product_record(monkeypatch):
    # Arrange
    monkeypatch.setattr(scorer_module, "get_user_feedback", lambda user_id: [])
    scorer = scorer_module.ProductScorer(user_id="u1")
    user_embedding = np.array([1.0, 0.0, 0.0])
    products = [{"product": {"title": "Broken", "price": 1000, "link": "bad"}}]

    # Act / Assert
    with pytest.raises(KeyError, match="embedding"):
        scorer.rank_products(products, user_embedding)
