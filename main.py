from Data_base import db
from agents.profile.agent import run_profile_agent
from Data_base.profile_repo import get_profile, save_profile
from agents.profile.schemas import UserProfile
from graph.collector_graph import collector_graph
from agents.recommendation.agent import RecommendationAgent
from agents.recommendation.chat_handler import RecommendationChatHandler
from Data_base.feedback_repo import save_feedback
from Data_base.product_cache import has_enough_products
from agents.recommendation.agent import detect_product_type


def chat_with_profile_agent():
    user_id = input("Enter user id: ")
    history = []
    mode = "discovery"
    rec_handler = RecommendationChatHandler(user_id)
    last_recommendations = []

    # reset profile every run
    db.user_profiles.delete_one({"user_id": user_id})

    current_profile = None

    print("\nProfile Agent Started.")
    print("Type 'exit' to stop.")
    print("Type 'reset' to start a new product search.\n")

    user_input = input("You: ")

    while user_input.lower() != "exit":
        # Reset command
        if user_input.lower() == "reset":
            current_profile = None
            history = []
            last_recommendations = []
            mode = "discovery"
            print("\nProfile reset. Starting new product search.")
            user_input = input("You: ")
            continue

        # Run agent
        if mode == "discovery":
            output, raw = run_profile_agent(user_input, history, current_profile)

        elif mode == "recommendation":
            # -----------------------------
            # Review sentiment command
            # -----------------------------
            if user_input.lower().startswith("review"):
                parts = user_input.lower().split()

                numbers = [int(p) for p in parts if p.isdigit()]

                if len(numbers) == 1:
                    i = numbers[0]

                    if 1 <= i <= len(last_recommendations):
                        product = last_recommendations[i - 1]

                        review_text = rec_handler.get_product_reviews(product)

                        print("\n" + review_text)

                        user_input = input("You: ")
                        continue

            # check comparison command
            if user_input.lower().startswith("compare"):
                parts = user_input.lower().split()

                numbers = [int(p) for p in parts if p.isdigit()]

                if len(numbers) == 2:
                    i, j = numbers

                    if 1 <= i <= len(last_recommendations) and 1 <= j <= len(
                        last_recommendations
                    ):
                        p1 = last_recommendations[i - 1]
                        p2 = last_recommendations[j - 1]

                        comparison = rec_handler.compare_products(p1, p2)

                        print("\n" + comparison)

                        user_input = input("You: ")
                        continue

            result = rec_handler.handle(
                user_input, current_profile.model_dump(), last_recommendations
            )

            if result["type"] == "recommendation_update":
                last_recommendations = result["data"]

                if not last_recommendations:
                    print("No recommendations found.")
                else:
                    print("\n=== Updated Recommendations ===")
                    for i, rec in enumerate(last_recommendations, 1):
                        print(f"\nRank {i}")
                        print("Title:", rec["title"])
                        print("Price:", rec["price"])
                        print("Score:", round(rec.get("final_score", 0), 4))

            elif result["type"] == "message":
                print("\n" + result["data"])

            elif result["type"] == "new_search":
                print("\nStarting new search...")
                mode = "discovery"
                current_profile = None
                history = []

            print("\nYou can continue refining or type 'reset' to start over.")
            user_input = input("You: ")
            continue

        # Update profile in memory
        current_profile = output.profile

        # Save user message
        history.append({"role": "user", "content": user_input})

        if not output.is_complete:
            question = output.next_question
            print(f"Agent: {question}")

            history.append({"role": "assistant", "content": question})
            user_input = input("You: ")

        else:
            # Save profile to Mongo
            save_profile(user_id, current_profile.model_dump())
            print("\nProfile saved to database.")

            print("\n=== Profile Complete ===")
            print(current_profile)
            print("\nSearch Queries:")
            for q in current_profile.search_queries:
                print("-", q)

            # ==============================
            # STEP 4: Trigger Collector (SMART CACHE VERSION)
            # ==============================

            profile_dict = current_profile.model_dump()

            # detect product type
            product_type = detect_product_type(profile_dict)

            price_min = profile_dict.get("budget_min")
            price_max = profile_dict.get("budget_max")

            # check cache
            cache_ok = has_enough_products(
                product_type=product_type,
                price_min=price_min,
                price_max=price_max,
            )

            if cache_ok:
                print("\nUsing cached products from database. Skipping scraping.")

            else:
                profile_doc = db.user_profiles.find_one({"user_id": user_id})
                status = (
                    profile_doc.get("collection_status", "idle")
                    if profile_doc
                    else "idle"
                )

                if status == "running":
                    print("\nCollector is already running for this user.")

                else:
                    state = {"user_id": user_id, "queries": []}

                    print("\nStarting Collector...")

                    collector_graph.invoke(state)

                    print("Collector finished.")
            # ==============================
            # STEP 6: Run Recommendation Agent
            # ==============================

            print("\nGenerating recommendations...")

            rec_agent = RecommendationAgent(user_id)

            profile_dict = current_profile.model_dump()

            recommendations = rec_agent.recommend(profile_dict)
            last_recommendations = recommendations

            if not recommendations:
                print("No recommendations found based on your profile.")
            else:
                print("\n=== Top Recommendations ===")
                for i, rec in enumerate(recommendations, 1):
                    print(f"\nRank {i}")
                    print("Title:", rec["title"])
                    print("Price:", rec["price"])
                    print("Score:", round(rec["final_score"], 4))

                print("\nWhich recommendation do you prefer? (1 / 2 / 3 / none)")
                choice = input("Choice: ").strip()

                if choice in ["1", "2", "3"]:
                    idx = int(choice) - 1
                    selected = recommendations[idx]

                    save_feedback(user_id, selected["link"], liked=True)

                    print(
                        "Feedback saved. We'll prioritize similar products next time."
                    )

                elif choice.lower() == "none":
                    for r in recommendations:
                        save_feedback(user_id, r["link"], liked=False)

                    print("Got it. We'll avoid similar products next time.")

                mode = "recommendation"

            print("\nYou can type 'reset' to search for another product.")
            user_input = input("You: ")


if __name__ == "__main__":
    chat_with_profile_agent()
