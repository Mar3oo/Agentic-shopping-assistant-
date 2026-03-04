from agents.recommendation.agent import RecommendationAgent

# Simulate stored profile
profile = {
    "category": "Laptop",
    "budget_min": 10000,
    "budget_max": 50000,
    "use_case": "Programming and AI development",
    "preferences": "Good GPU, long battery life",
    "search_queries": ["gaming laptop", "RTX laptop for coding"],
}

agent = RecommendationAgent()

recommendations = agent.recommend(profile)

if not recommendations:
    print("No recommendations found.")
else:
    for i, rec in enumerate(recommendations, 1):
        print(f"\nRank {i}")
        print("Title:", rec["title"])
        print("Price:", rec["price"])
        print("Final Score:", round(rec["final_score"], 4))
