import faiss
import numpy as np
from Data_base.db import get_collection


class ProductVectorIndex:
    def __init__(self):

        self.collection = get_collection()
        self.index = None
        self.product_links = []
        self.product_type = None

    def build(self, product_type=None):

        # do not rebuild if already built for same type
        if self.index is not None and self.product_type == product_type:
            return

        query = {"product.embedding": {"$exists": True}}

        if product_type:
            query["product.product_type"] = product_type

        cursor = self.collection.find(query)

        embeddings = []
        self.product_links = []

        for doc in cursor:
            product = doc["product"]

            embeddings.append(product["embedding"])
            self.product_links.append(product["link"])

        if not embeddings:
            return

        embeddings = np.array(embeddings).astype("float32")

        dim = embeddings.shape[1]

        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)

        self.product_type = product_type

        print(f"[FAISS] Index built with {len(self.product_links)} products")

    def search(self, query_embedding, top_k=50):

        if self.index is None:
            return []

        query_vector = np.array([query_embedding]).astype("float32")

        scores, indices = self.index.search(query_vector, top_k)

        results = []

        for i in indices[0]:
            if i < len(self.product_links):
                results.append(self.product_links[i])

        return results
