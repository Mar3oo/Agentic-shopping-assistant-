"""
Hybrid retriever:
1) Hard filter using Mongo (price + optional category)
2) Return candidate products with embeddings
"""

from typing import List, Dict, Any, Optional
from Data_base.db import get_collection
from agents.recommendation.vector_index import ProductVectorIndex


class ProductRetriever:
    """
    Handles product retrieval from MongoDB
    before semantic ranking.
    """

    def __init__(self):
        self.collection = get_collection()
        self.vector_index = ProductVectorIndex()

    def retrieve_candidates(
        self,
        product_type: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        user_embedding=None,
        limit: int = 300,
    ) -> List[Dict[str, Any]]:

        query = {"product.embedding": {"$exists": True}}

        if product_type:
            query["product.product_type"] = product_type

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
        # FAISS vector search
        # ---------------------------
        if user_embedding is not None:
            self.vector_index.build(product_type)

            links = self.vector_index.search(user_embedding, top_k=100)

            if links:
                query["product.link"] = {"$in": links}

        cursor = self.collection.find(query, projection).limit(limit)

        return list(cursor)
