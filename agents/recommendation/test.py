from agents.recommendation.agent import RecommendationAgent
from agents.recommendation.chat_handler import RecommendationChatHandler


def run_test():
    user_id = "test_user"

    # -----------------------------
    # 1️⃣ Initial user request (simulate profile output)
    # -----------------------------
    profile = {
        "product_category": "laptop",
        "product_intent": "programming",
        "budget": "under 25000",
        "priorities": {"performance": 0.8},
        "must_have_features": ["SSD"],
        "preferences": {"RAM": "16GB"},
        "search_queries": ["programming laptop"],
        "original_query": "I want a laptop for programming under 25k",
    }

    rec_agent = RecommendationAgent(user_id)

    print("\n=== Initial Recommendation ===")
    recommendations = rec_agent.recommend(profile)

    for i, r in enumerate(recommendations, 1):
        print(f"{i}. {r['title']} | {r['price']}")

    # -----------------------------
    # 2️⃣ Simulate user refinement
    # -----------------------------
    chat = RecommendationChatHandler(user_id)

    user_message = "make it cheaper"

    print("\n=== User says:", user_message, "===")

    response = chat.handle(
        user_message=user_message,
        current_profile=profile,
        current_recommendations=recommendations,
    )

    print("\n=== After Refinement ===")

    if response["type"] == "recommendation_update":
        new_recs = response["data"]

        for i, r in enumerate(new_recs, 1):
            print(f"{i}. {r['title']} | {r['price']}")

    else:
        print(response)


if __name__ == "__main__":
    run_test()
