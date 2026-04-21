"""
Recommendation Agent:
Profile → Embedding → Retrieval → Ranking → Rerank
"""

from typing import Dict, Any, List, final

from agents import profile
from agents.recommendation.embedding_model import get_embedding_model
from agents.recommendation.retriever import ProductRetriever
from agents.recommendation.scorer import ProductScorer
from agents.recommendation.bm25_index import BM25Index
from agents.recommendation.llm_reranker import LLMReranker
from agents.recommendation.profile_adapter import adapt_profile
from tools.product_classifier import classify_product_type


# -----------------------------
# Product type detection
# -----------------------------
def detect_product_type(profile: Dict[str, Any]) -> str:
    normalized = adapt_profile(profile)

    parts = []

    if normalized.get("category"):
        parts.append(str(normalized["category"]))

    if normalized.get("use_case"):
        parts.append(str(normalized["use_case"]))

    if normalized.get("search_queries"):
        parts.append(" ".join(normalized["search_queries"]))

    detection_text = " ".join(parts).strip()

    return classify_product_type(detection_text, normalized.get("category"))


# -----------------------------
# Recommendation Agent
# -----------------------------
class RecommendationAgent:
    def __init__(self, user_id: str):
        self.model = get_embedding_model()
        self.retriever = ProductRetriever()
        self.scorer = ProductScorer(user_id)
        self.bm25 = BM25Index()
        self.reranker = LLMReranker()

    # -----------------------------
    # Build semantic text (for embedding)
    # -----------------------------
    def _build_user_semantic_text(self, profile: Dict[str, Any]) -> str:

        parts = []

        if profile.get("category"):
            parts.append(f"{profile['category']}")

        if profile.get("use_case"):
            parts.append(f"{profile['use_case']}")

        if profile.get("preferences"):
            parts.extend([str(v) for v in profile["preferences"].values()])

        if profile.get("must_have_features"):
            parts.extend(profile["must_have_features"])

        if profile.get("search_queries"):
            parts.extend(profile["search_queries"])

        if profile.get("original_query"):
            parts.append(profile["original_query"])

        return " ".join(parts)

    # -----------------------------
    # Build BM25 query (keywords)
    # -----------------------------
    def _build_bm25_query(self, profile: Dict[str, Any]) -> str:

        parts = []

        if profile.get("category"):
            parts.append(profile["category"])

        if profile.get("use_case"):
            parts.append(profile["use_case"])

        if profile.get("must_have_features"):
            parts.extend(profile["must_have_features"])

        if profile.get("preferences"):
            parts.extend(profile["preferences"].values())

        # Priority → keywords
        priorities = profile.get("priorities", {})

        if priorities.get("performance", 0) > 0.7:
            parts.append("powerful")

        if priorities.get("price", 0) > 0.7:
            parts.append("cheap")

        if priorities.get("battery", 0) > 0.7:
            parts.append("battery")

        if priorities.get("camera", 0) > 0.7:
            parts.append("camera")

        if profile.get("search_queries"):
            parts.extend(profile["search_queries"])

        return " ".join(parts)

    def _apply_diversity(self, products, top_k):
        """
        Diversity based ONLY on title similarity.
        Domain-agnostic and robust.
        """

        diverse = []
        used_signatures = []

        for p in products:
            title = (p.get("title") or "").lower()
            tokens = title.split()

            # signature = first meaningful words
            signature = " ".join(
                tokens[:4]
            )  # the bigger the number the looser the diversity (e.g. 2 would be very strict, 5 would be more relaxed)

            # check similarity
            is_duplicate = False
            for sig in used_signatures:
                if signature in sig or sig in signature:
                    is_duplicate = True
                    break

            if not is_duplicate:
                diverse.append(p)
                used_signatures.append(signature)

            # fallback to fill results
            elif len(diverse) < top_k:
                diverse.append(p)

            if len(diverse) >= top_k:
                break

        return diverse

    # -----------------------------
    # Main pipeline
    # -----------------------------
    def recommend(
        self,
        profile: Dict[str, Any],
        top_k: int = 4,
    ) -> List[Dict[str, Any]]:

        # -----------------------------
        # 0) Normalize profile
        # -----------------------------
        profile = adapt_profile(profile)

        # print("[DEBUG] budget_min:", profile.get("budget_min"))
        # print("[DEBUG] budget_max:", profile.get("budget_max"))

        # -----------------------------
        # 1) Build semantic text
        # -----------------------------
        user_text = self._build_user_semantic_text(profile)

        if not user_text.strip():
            raise ValueError("Profile is too empty for recommendation.")

        # -----------------------------
        # 2) Embedding
        # -----------------------------
        user_embedding = self.model.encode([user_text])[0]

        # -----------------------------
        # 3) Product type
        # -----------------------------
        product_type = detect_product_type(profile)

        # -----------------------------
        # 4) BM25 Retrieval (WIDE)
        # -----------------------------
        query_text = self._build_bm25_query(profile)

        self.bm25.build(product_type)

        bm25_k = 40  # wider pool if you want better recall for the LLM reranker
        bm25_results = self.bm25.search(query_text, top_k=bm25_k)

        # print("\n[DEBUG] BM25 candidates (first 10):")
        # for p in bm25_results[:10]:
        #     print(f"- {p.get('price')} | {p.get('title')[:30]}")

        # -----------------------------
        # 5) Build candidates
        # -----------------------------
        candidates = [{"product": p} for p in bm25_results]

        # Deduplicate
        unique = {}
        for item in candidates:
            product = item["product"]
            unique[product["link"]] = item

        candidates = list(unique.values())

        if not candidates:
            return []

        # -----------------------------
        # 6) Must-have filtering (SOFT)
        # -----------------------------
        must_have = profile.get("must_have_features") or []

        if must_have:
            filtered = []

            for item in candidates:
                text = (item["product"].get("details_text") or "").lower()

                if all(f.lower() in text for f in must_have):
                    filtered.append(item)

            # only apply if safe (avoid collapse)
            if len(filtered) >= 5:
                candidates = filtered

        # -----------------------------
        # 7) Ranking (Scorer)
        # -----------------------------
        ranked = self.scorer.rank_products(
            candidates,
            user_embedding,
            user_price_min=profile.get("budget_min"),
            user_price_max=profile.get("budget_max"),
            priorities=profile.get("priorities"),
            top_k=25,  # give LLM more options
        )

        if not ranked:
            return []

        # -----------------------------
        # 8) LLM Reranking (SMART)
        # -----------------------------
        expanded = self.reranker.rerank(
            user_text, ranked, top_k=top_k * 4
        )  # keep more for final budget clipping

        # -----------------------------
        # 9) FINAL Budget Clipping
        # -----------------------------
        budget_max = profile.get("budget_max")

        if budget_max:
            tolerance = 0.15  # 15% flexibility
            max_allowed = budget_max * (1 + tolerance)

            filtered = [
                p
                for p in expanded
                if p.get("price") is not None and p["price"] <= max_allowed
            ]

            if filtered:
                final = filtered
            else:
                final = expanded
        else:
            final = expanded

        # -----------------------------
        # 10) Final Top-K and apply diversity
        # -----------------------------
        final = self._apply_diversity(final, top_k)
        return final
