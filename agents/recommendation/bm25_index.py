from rank_bm25 import BM25Okapi
from Data_base.db import get_collection


class BM25Index:
    def __init__(self):
        self.collection = get_collection()
        self.documents = []
        self.products = []
        self.cache = {}
        self.bm25 = None
        self.current_type = None

    def build(self, product_type=None):
        
        if product_type in self.cache:
            cached = self.cache[product_type]
            self.bm25 = cached["bm25"]
            self.documents = cached["documents"]
            self.products = cached["products"]
            return
    
        # prevent rebuilding same index
        if self.bm25 and self.current_type == product_type:
            return

        self.current_type = product_type
        
        query = {"product.embedding": {"$exists": True}}

        if product_type:
            query["product.product_type"] = product_type

        cursor = self.collection.find(query)

        self.documents = []
        self.products = []

        for doc in cursor:
            product = doc["product"]

            text = f"{product.get('title', '')} {product.get('details_text', '')}"
            tokens = text.lower().split()

            self.documents.append(tokens)
            self.products.append(product)

        if self.documents:
            self.bm25 = BM25Okapi(self.documents)
            self.cache[product_type] = {
                "bm25": self.bm25,
                "documents": self.documents,
                "products": self.products,
            }

    def search(self, query_text, top_k=20):
        if not self.bm25:
            return []

        tokens = query_text.lower().split()
        scores = self.bm25.get_scores(tokens)

        ranked = sorted(zip(self.products, scores), key=lambda x: x[1], reverse=True)

        return [p for p, _ in ranked[:top_k]]
