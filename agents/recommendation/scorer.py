from typing import List, Dict, Any
import numpy as np


class ProductScorer:
    """
    Clean scoring engine:
    - Semantic similarity
    - Price alignment
    - Adaptive budget penalty
    - Priority-aware weighting
    """

    def __init__(self, user_id: str):
        self.user_id = user_id

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b))

    def _price_score(
        self,
        product_price: float,
        user_min: float | None,
        user_max: float | None,
    ) -> float:

        if product_price is None:
            return 0.0

        if user_max is None or user_max <= 0:
            return 0.5

        # 🔥 prefer prices closer to upper budget (better quality)
        ratio = product_price / user_max

        if ratio <= 1:
            # within budget → higher is better
            return 0.5 + 0.5 * ratio  # range: 0.5 → 1.0

        else:
            # above budget → decrease score
            return max(0.0, 1 - (ratio - 1))

    def _budget_penalty(
        self,
        price: float,
        budget_max: float | None,
        priorities: Dict[str, float] | None,
    ) -> float:
        """
        Penalize products above budget with adaptive tolerance.
        """

        if not budget_max or not price:
            return 0.0

        performance_priority = (priorities or {}).get("performance", 0)
        price_priority = (priorities or {}).get("price", 0)

        # 🔥 Dynamic tolerance
        base_tolerance = 0.15  # 15%

        if performance_priority > 0.7:
            base_tolerance += 0.15  # allow more expensive if performance matters

        if price_priority > 0.7:
            base_tolerance -= 0.05  # stricter if price matters

        max_allowed = budget_max * (1 + base_tolerance)

        if price <= budget_max:
            return 0.0

        elif price <= max_allowed:
            # mild penalty
            overflow_ratio = (price - budget_max) / (max_allowed - budget_max)
            return -0.2 * overflow_ratio

        else:
            # strong penalty
            return -0.8

    def rank_products(
        self,
        products: List[Dict[str, Any]],
        user_embedding: np.ndarray,
        user_price_min: float | None = None,
        user_price_max: float | None = None,
        priorities: Dict[str, float] | None = None,
        top_k: int = 50,
    ) -> List[Dict[str, Any]]:

        scored = []

        for item in products:
            product = item["product"]

            embedding = np.array(product["embedding"])
            semantic_sim = self._cosine_similarity(user_embedding, embedding)

            price = product.get("price")

            price_score = self._price_score(
                price,
                user_price_min,
                user_price_max,
            )

            # -------------------------
            # 🔥 Adaptive weights
            # -------------------------
            semantic_w = 0.6
            price_w = 0.4

            if priorities:
                perf = priorities.get("performance", 0)
                price_p = priorities.get("price", 0)

                if perf > 0.7:
                    semantic_w = 0.75
                    price_w = 0.25

                elif price_p > 0.7:
                    semantic_w = 0.4
                    price_w = 0.6

            # -------------------------
            # 🔥 Budget penalty
            # -------------------------
            penalty = self._budget_penalty(
                price,
                user_price_max,
                priorities,
            )

            # -------------------------
            # Final score
            # -------------------------
            final_score = semantic_sim * semantic_w + price_score * price_w + penalty

            scored.append(
                {
                    "title": product.get("title"),
                    "price": price,
                    "link": product.get("link"),
                    "category": product.get("category"),
                    "semantic_score": semantic_sim,
                    "price_score": price_score,
                    "final_score": final_score,
                }
            )

        scored.sort(key=lambda x: x["final_score"], reverse=True)

        return scored[:top_k]
