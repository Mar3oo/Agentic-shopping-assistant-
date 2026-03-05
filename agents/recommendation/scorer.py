"""
Hybrid scoring engine:
Combines semantic similarity + structured signals.
"""

from typing import List, Dict, Any
import numpy as np
from Data_base.feedback_repo import get_user_feedback


class ProductScorer:
    """
    Scores products using:
    - Semantic similarity (primary)
    - Price proximity
    - Seller score
    """

    def __init__(
        self,
        semantic_weight: float = 0.7,
        price_weight: float = 0.2,
        seller_weight: float = 0.1,
    ):
        self.semantic_weight = semantic_weight
        self.price_weight = price_weight
        self.seller_weight = seller_weight

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Cosine similarity for normalized vectors.
        Since embeddings are normalized,
        dot product = cosine similarity.
        """
        return float(np.dot(a, b))

    def _price_score(
        self,
        product_price: float,
        user_min: float | None,
        user_max: float | None,
    ) -> float:
        """
        Score how close price is to middle of user's range.
        Returns value between 0 and 1.
        """

        if product_price is None:
            return 0.0

        if user_min is None and user_max is None:
            return 0.5  # neutral

        # Define bounds safely
        lower = user_min if user_min is not None else product_price
        upper = user_max if user_max is not None else product_price

        if lower == upper:
            return 1.0

        mid = (lower + upper) / 2
        distance = abs(product_price - mid)

        max_distance = (upper - lower) / 2
        if max_distance == 0:
            return 1.0

        score = 1 - (distance / max_distance)

        return max(0.0, min(1.0, score))

    def _seller_score(self, seller_score: float | None) -> float:
        """
        Normalize seller score into 0-1.
        If missing → treat as 0.
        Assumes seller_score roughly between 0-5.
        """

        if seller_score is None:
            return 0.0

        return max(0.0, min(1.0, seller_score / 5))

    def rank_products(
        self,
        products: List[Dict[str, Any]],
        user_embedding: np.ndarray,
        user_price_min: float | None = None,
        user_price_max: float | None = None,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Rank products and return top_k.
        """

        scored = []
        feedback = get_user_feedback("user_005")
        liked_links = {f["product_link"] for f in feedback if f["liked"]}

        for item in products:
            product = item["product"]

            embedding = np.array(product["embedding"])
            semantic_sim = self._cosine_similarity(user_embedding, embedding)

            price_score = self._price_score(
                product.get("price"),
                user_price_min,
                user_price_max,
            )

            seller_score = self._seller_score(product.get("seller_score"))

            feedback_boost = 0

            if product.get("link") in liked_links:
                feedback_boost = 0.1

            final_score = (
                semantic_sim * self.semantic_weight
                + price_score * self.price_weight
                + seller_score * self.seller_weight
                + feedback_boost
            )

            scored.append(
                {
                    "title": product.get("title"),
                    "price": product.get("price"),
                    "link": product.get("link"),
                    "category": product.get("category"),
                    "semantic_score": semantic_sim,
                    "price_score": price_score,
                    "seller_score": seller_score,
                    "final_score": final_score,
                }
            )

        scored.sort(key=lambda x: x["final_score"], reverse=True)

        return scored[:top_k]
