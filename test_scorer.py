import numpy as np
from agents.recommendation.retriever import ProductRetriever
from agents.recommendation.scorer import ProductScorer
from agents.recommendation.embedding_model import get_embedding_model

# Fake user query
user_text = "Gaming laptop for programming and AI with good GPU"

model = get_embedding_model()
user_embedding = model.encode([user_text])[0]

retriever = ProductRetriever()
products = retriever.retrieve_candidates(
    price_min=1000,
    price_max=50000,
)

scorer = ProductScorer()

top = scorer.rank_products(
    products,
    user_embedding,
    user_price_min=1000,
    user_price_max=50000,
    top_k=3,
)

for i, p in enumerate(top, 1):
    print(f"\nRank {i}")
    print("Title:", p["title"])
    print("Score:", round(p["final_score"], 4))
