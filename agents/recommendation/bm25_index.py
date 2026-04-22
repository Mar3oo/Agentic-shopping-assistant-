import logging
from rank_bm25 import BM25Okapi
from Data_Base.db import get_collection

logger = logging.getLogger(__name__)


class BM25Index:
    """
    BM25 keyword-based retrieval index.
    Works alongside FAISS for hybrid search.
    """

    def __init__(self):
        self.collection = get_collection()
        self.documents = []
        self.products = []
        self.cache = {}
        self.bm25 = None
        self.current_type = None

    def build(self, product_type=None):
        """
        Build BM25 index from product text.
        Uses caching to avoid rebuilding.
        """

        # Use cache if available
        if product_type in self.cache:
            cached = self.cache[product_type]
            self.bm25 = cached["bm25"]
            self.documents = cached["documents"]
            self.products = cached["products"]
            logger.info(f"[BM25] Loaded from cache for type={product_type}")
            return

        # Prevent rebuild if already built
        if self.bm25 is not None and self.current_type == product_type:
            logger.info(f"[BM25] Reusing existing index for type={product_type}")
            return

        logger.info(f"[BM25] Building index for type={product_type}")

        self.current_type = product_type

        query = {"product.embedding": {"$exists": True}}

        if product_type:
            query["product.product_type"] = product_type

        # limit for safety (important for scaling)
        cursor = self.collection.find(query).limit(5000)

        self.documents = []
        self.products = []

        for doc in cursor:
            product = doc["product"]

            title = product.get("title") or ""
            details = product.get("details_text") or ""
            category = product.get("category") or ""

            text = f"{title} {details} {category}".lower()

            tokens = text.split()

            if not tokens:
                continue

            self.documents.append(tokens)
            self.products.append(product)

        if not self.documents:
            logger.warning("[BM25] No documents found, index not built")
            self.bm25 = None
            return

        self.bm25 = BM25Okapi(self.documents)

        # Cache result
        self.cache[product_type] = {
            "bm25": self.bm25,
            "documents": self.documents,
            "products": self.products,
        }

        logger.info(f"[BM25] Index built with {len(self.products)} products")

    def search(self, query_text, top_k=20):
        """
        Search products using keyword matching.

        Args:
            query_text: user query string
            top_k: number of results

        Returns:
            List of product dicts
        """

        if not self.bm25:
            logger.warning("[BM25] Search called before index built")
            return []

        if not query_text or not query_text.strip():
            logger.warning("[BM25] Empty query")
            return []

        tokens = query_text.lower().split()

        scores = self.bm25.get_scores(tokens)

        ranked = sorted(zip(self.products, scores), key=lambda x: x[1], reverse=True)

        results = [p for p, _ in ranked[:top_k]]

        logger.info(f"[BM25] Returned {len(results)} results")

        return results
