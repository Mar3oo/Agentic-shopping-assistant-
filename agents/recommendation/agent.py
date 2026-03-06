"""
Recommendation Agent:
Connects profile → embedding → retrieval → ranking
"""

from typing import Dict, Any, List, Optional
from agents.recommendation.embedding_model import get_embedding_model
from agents.recommendation.retriever import ProductRetriever
from agents.recommendation.scorer import ProductScorer
from agents.recommendation.bm25_index import BM25Index
from agents.recommendation.llm_reranker import LLMReranker
from tools.product_classifier import classify_product_type


class RecommendationAgent:
    """
    Main recommendation pipeline.
    """

    def __init__(self):
        self.model = get_embedding_model()
        self.retriever = ProductRetriever()
        self.scorer = ProductScorer()
        self.bm25 = BM25Index()
        self.reranker = LLMReranker()

    def _build_user_semantic_text(self, profile: Dict[str, Any]) -> str:
        """
        Convert structured profile into semantic query text.
        Best practice: structured → natural language format.
        """

        parts = []

        if profile.get("category"):
            parts.append(f"Category: {profile['category']}")

        if profile.get("budget_min") or profile.get("budget_max"):
            parts.append(
                f"Budget: {profile.get('budget_min')} - {profile.get('budget_max')}"
            )

        if profile.get("preferences"):
            parts.append(f"Preferences: {profile['preferences']}")

        if profile.get("use_case"):
            parts.append(f"Use case: {profile['use_case']}")

        if profile.get("search_queries"):
            joined = ", ".join(profile["search_queries"])
            parts.append(f"Search intent: {joined}")

        return "\n".join(parts)

    def recommend(
        self,
        profile: Dict[str, Any],
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Full recommendation pipeline.
        """

        # 1️⃣ Build semantic user text
        user_text = self._build_user_semantic_text(profile)

        if not user_text.strip():
            raise ValueError("User profile is too empty for recommendation.")

        # 2️⃣ Generate user embedding
        user_embedding = self.model.encode([user_text])[0]

        product_type = classify_product_type(profile)

        # 3️⃣ Retrieve candidate products
        query_text = " ".join(profile.get("search_queries", []))

        # build BM25 index
        self.bm25.build(product_type)

        bm25_results = self.bm25.search(query_text, top_k=50)

        semantic_candidates = self.retriever.retrieve_candidates(
            product_type=product_type,
            price_min=profile.get("budget_min"),
            price_max=profile.get("budget_max"),
            user_embedding=user_embedding,
        )

        # merge both candidate lists
        candidates = semantic_candidates + [{"product": p} for p in bm25_results]
        unique = {}
        for item in candidates:
            p = item["product"]
            unique[p["link"]] = item

        candidates = list(unique.values())

        if not candidates:
            return []

        # 4️⃣ Rank
        ranked = self.scorer.rank_products(
            candidates,
            user_embedding,
            user_price_min=profile.get("budget_min"),
            user_price_max=profile.get("budget_max"),
            top_k=10,
        )

        # 5️⃣ Rerank with LLM
        query_text = " ".join(profile.get("search_queries", []))

        final = self.reranker.rerank(query_text, ranked, top_k=3)

        return final
