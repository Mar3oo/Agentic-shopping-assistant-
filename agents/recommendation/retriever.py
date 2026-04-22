from typing import List, Dict, Any, Optional
import logging

from Data_Base.db import get_collection
from agents.recommendation.vector_index import ProductVectorIndex

logger = logging.getLogger(__name__)


class ProductRetriever:
    """
    Hybrid retriever:
    1) Hard filter using Mongo (price + type)
    2) Optional FAISS narrowing
    """

    def __init__(self):
        self.collection = get_collection()
        self.vector_index = ProductVectorIndex()
        self.cache = {}

    def retrieve_candidates(
        self,
        product_type: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        user_embedding=None,
        limit: int = 300,
        vector_k: int = 100,  # 🔥 NEW
    ) -> List[Dict[str, Any]]:

        query = {"product.embedding": {"$exists": True}}

        if product_type:
            query["product.product_type"] = {"$eq": product_type}

        if price_min is not None or price_max is not None:
            query["product.price"] = {}

            if price_min is not None:
                query["product.price"]["$gte"] = price_min

            if price_max is not None:
                query["product.price"]["$lte"] = price_max

        projection = {
            "_id": 0,
            "product.title": 1,
            "product.price": 1,
            "product.link": 1,
            "product.details_text": 1,
            "product.seller_score": 1,
            "product.category": 1,
            "product.embedding": 1,
            "product.product_type": 1,
        }

        # ---------------------------
        # FAISS vector narrowing
        # ---------------------------
        if user_embedding is not None:
            self.vector_index.build(product_type)

            links = self.vector_index.search(user_embedding, top_k=vector_k)

            if links:
                query["product.link"] = {"$in": links}
            else:
                logger.warning(
                    "[Retriever] FAISS returned no results, skipping vector filter"
                )

        # ---------------------------
        # Cache (only non-embedding queries)
        # ---------------------------
        cache_key = (
            product_type,
            int(price_min) if price_min else None,
            int(price_max) if price_max else None,
        )

        if user_embedding is None and cache_key in self.cache:
            logger.info("[Retriever] Returning cached results")
            return self.cache[cache_key]

        # ---------------------------
        # Mongo query
        # ---------------------------
        cursor = self.collection.find(query, projection).limit(limit)

        results = list(cursor)

        if user_embedding is None:
            self.cache[cache_key] = results

        logger.info(f"[Retriever] Retrieved {len(results)} candidates")

        return results
