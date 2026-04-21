import logging

from agents.profile.agent import run_profile_agent
from agents.recommendation.agent import RecommendationAgent
from agents.recommendation.chat_handler import RecommendationChatHandler
from agents.recommendation.profile_adapter import adapt_profile
from Data_base.profile_repo import save_profile, get_profile

logger = logging.getLogger(__name__)


def print_recommendations(recs):
    if not recs:
        print("\n❌ No products found.\n")
        return

    print("\n💡 Recommended Products:\n")

    for i, r in enumerate(recs, 1):
        print(f"{i}. {r.get('title')}")
        print(f"   💰 Price: {r.get('price')}")
        print(f"   🔗 Link: {r.get('link')}")
        print()


def main():
    print("\n🛒 AI Shopping Assistant")
    print("Type 'exit' to quit")
    print("Type 'reset' to start a new search\n")

    user_id = input("Enter user id: ").strip()

    rec_agent = RecommendationAgent(user_id)
    chat_handler = RecommendationChatHandler(user_id)

    # -----------------------------
    # Load existing profile
    # -----------------------------
    saved_profile = get_profile(user_id)

    current_profile = None
    current_profile_data = None
    current_recommendations = []
    history = []

    if saved_profile:
        print("\n📦 Loaded previous profile.")

        current_profile = saved_profile
        current_profile_data = adapt_profile(saved_profile)

        current_recommendations = rec_agent.recommend(current_profile_data)
        print_recommendations(current_recommendations)

    print("\nStart chatting...\n")

    while True:
        user_input = input("👤 You: ").strip()

        if user_input.lower() == "exit":
            print("👋 Goodbye!")
            break

        if user_input.lower() == "reset":
            print("\n🔄 Starting new search...\n")

            current_profile = None
            current_profile_data = None
            current_recommendations = []
            history = []

            continue

        # -----------------------------
        # FIRST MESSAGE → Profile Agent
        # -----------------------------
        if current_profile is None:
            parsed, raw = run_profile_agent(
                user_input, history=history, current_profile=None
            )

            current_profile = parsed.profile

            # Save profile
            save_profile(user_id, current_profile.model_dump())

            current_profile_data = adapt_profile(current_profile.model_dump())

            print("\n🤖 Got it! Finding best products...\n")

            current_recommendations = rec_agent.recommend(current_profile_data)

            print_recommendations(current_recommendations)

            history.append({"role": "user", "content": user_input})

            continue

        # -----------------------------
        # FOLLOW-UP → Chat Handler
        # -----------------------------
        response = chat_handler.handle(
            user_message=user_input,
            current_profile=current_profile_data,
            current_recommendations=current_recommendations,
        )

        response_type = response.get("type")

        if response_type == "recommendation_update":
            current_recommendations = response["data"]
            print_recommendations(current_recommendations)

        elif response_type == "message":
            print(f"\n🤖 {response['data']}\n")

        elif response_type == "new_search":
            print("\n🔄 Starting new search...\n")

            current_profile = None
            current_profile_data = None
            current_recommendations = []
            history = []

        else:
            print("\n⚠️ Unexpected response.\n")

        history.append({"role": "user", "content": user_input})


if __name__ == "__main__":
    main()
