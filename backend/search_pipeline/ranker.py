"""Ranking stage for the standalone product search pipeline."""

from __future__ import annotations

import re


def _log(message: str) -> None:
    print(f"[search_pipeline.ranker] {message}")


class ProductRanker:
    """Rank products with query relevance first and price as a tie-breaker."""

    def rank(self, query: str, products: list[dict], top_k: int = 5) -> list[dict]:
        query_tokens = self._tokenize(query)
        ranked_products = []

        for product in products:
            relevance_score = self._score_product(query=query, query_tokens=query_tokens, product=product)
            ranked_products.append({**product, "relevance_score": round(relevance_score, 6)})

        ranked_products.sort(key=self._sort_key)

        top_products = ranked_products[: max(1, top_k)]
        for index, product in enumerate(top_products, start=1):
            product["rank"] = index

        _log(f"Ranked {len(products)} products and returned top {len(top_products)}.")
        return top_products

    def _score_product(self, query: str, query_tokens: set[str], product: dict) -> float:
        title = product.get("title") or ""
        details_text = product.get("details_text") or ""

        title_tokens = self._tokenize(title)
        detail_tokens = self._tokenize(details_text)
        if not query_tokens:
            lexical_score = 0.0
        else:
            title_overlap = len(query_tokens & title_tokens) / len(query_tokens)
            detail_overlap = len(query_tokens & detail_tokens) / len(query_tokens)
            exact_phrase_bonus = 0.15 if query.strip().casefold() in f"{title} {details_text}".casefold() else 0.0
            lexical_score = min(1.0, (title_overlap * 0.85) + (detail_overlap * 0.15) + exact_phrase_bonus)

        position = product.get("search_position")
        position_bonus = 0.0
        if isinstance(position, int) and position > 0:
            position_bonus = min(0.12, 0.12 / position)

        return min(1.0, lexical_score + position_bonus)

    @staticmethod
    def _sort_key(product: dict) -> tuple:
        price = product.get("price")
        position = product.get("search_position")
        return (
            -float(product.get("relevance_score", 0.0)),
            1 if price is None else 0,
            float("inf") if price is None else float(price),
            float("inf") if position is None else int(position),
            (product.get("title") or "").casefold(),
        )

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return set(re.findall(r"[a-z0-9]+", (text or "").casefold()))
