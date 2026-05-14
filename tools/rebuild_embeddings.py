"""
Rebuild all product embeddings using the current embedding model.
Useful after changing embedding models.
"""

from Data_Base.db import get_collection
from agents.recommendation.embedding_model import get_embedding_model


def build_semantic_text(product: dict) -> str:
    parts = []

    if product.get("title"):
        parts.append(f"Title: {product['title']}")

    if product.get("category"):
        parts.append(f"Category: {product['category']}")

    if product.get("details_text"):
        parts.append(f"Details: {product['details_text']}")

    return "\n".join(parts)


def rebuild_embeddings(batch_size: int = 32):
    collection = get_collection()
    model = get_embedding_model()

    cursor = collection.find(
        {"product.link": {"$exists": True}},
        {
            "_id": 1,
            "product": 1,
        },
    )

    documents = list(cursor)

    total = len(documents)

    print(f"Found {total} products")

    updated = 0

    for start in range(0, total, batch_size):
        batch = documents[start : start + batch_size]

        texts = []
        ids = []

        for doc in batch:
            product = doc.get("product", {})

            semantic_text = build_semantic_text(product)

            if semantic_text.strip():
                texts.append(semantic_text)
                ids.append(doc["_id"])

        if not texts:
            continue

        embeddings = model.encode_documents(texts)

        for doc_id, embedding in zip(ids, embeddings):
            collection.update_one(
                {"_id": doc_id},
                {"$set": {"product.embedding": embedding.tolist()}},
            )

            updated += 1

        print(f"Updated {updated}/{total}")

    print("Embedding rebuild complete")


if __name__ == "__main__":
    rebuild_embeddings()
