from agents.recommendation.retriever import ProductRetriever

retriever = ProductRetriever()

results = retriever.retrieve_candidates(price_min=1000, price_max=50000, category=None)

print("Found:", len(results))

if results:
    print("Sample product:")
    print(results[0]["product"]["title"])
