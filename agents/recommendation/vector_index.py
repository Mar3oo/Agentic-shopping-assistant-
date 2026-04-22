import logging

import faiss
import numpy as np
from Data_Base.db import get_collection

logger = logging.getLogger(__name__)


class ProductVectorIndex:
    """
    FAISS-based vector index for semantic product search.
    Builds once per product_type and reuses in memory.
    """

    def __init__(self):
        self.collection = get_collection()
        self.index = None
        self.product_links = []
        self.product_type = None

    def build(self, product_type=None, force_rebuild=False):
        """
        Build FAISS index from stored product embeddings.

        Args:
            product_type: filter products by type
            force_rebuild: force rebuilding index even if already built
        """

        # Skip rebuild if already built for same type
        if (
            not force_rebuild
            and self.index is not None
            and self.product_type == product_type
        ):
            logger.info("[FAISS] Reusing existing index")
            return

        logger.info(f"[FAISS] Building index for type={product_type}")

        query = {"product.embedding": {"$exists": True}}

        if product_type:
            query["product.product_type"] = product_type

        # Limit to avoid memory explosion (safe default)
        cursor = self.collection.find(query).limit(5000)

        embeddings = []
        self.product_links = []

        for doc in cursor:
            product = doc["product"]

            embedding = product.get("embedding")
            link = product.get("link")

            if embedding is None or link is None:
                continue

            embeddings.append(embedding)
            self.product_links.append(link)

        if len(embeddings) == 0:
            logger.warning("[FAISS] No embeddings found, index not built")
            self.index = None
            return

        embeddings = np.array(embeddings).astype("float32")

        dim = embeddings.shape[1]

        self.index = faiss.IndexFlatIP(dim)  # cosine similarity (normalized vectors)
        self.index.add(embeddings)

        self.product_type = product_type

        logger.info(f"[FAISS] Index built with {len(self.product_links)} products")

    def search(self, query_embedding, top_k=50):
        """
        Search for similar products using FAISS.

        Args:
            query_embedding: user embedding vector
            top_k: number of results

        Returns:
            List of product links
        """

        if self.index is None:
            logger.warning("[FAISS] Search called before index built")
            return []

        query_vector = np.array([query_embedding]).astype("float32")

        scores, indices = self.index.search(query_vector, top_k)

        results = []

        for i in indices[0]:
            if 0 <= i < len(self.product_links):
                results.append(self.product_links[i])

        logger.info(f"[FAISS] Returned {len(results)} results")

        return results
