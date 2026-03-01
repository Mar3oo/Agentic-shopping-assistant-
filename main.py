from Data_base import db
from agents.profile.agent import run_profile_agent
from Data_base.profile_repo import get_profile, save_profile
from agents.profile.schemas import UserProfile
from graph.collector_graph import collector_graph
import threading


def chat_with_profile_agent():
    user_id = "user_005"
    history = []

    # Load existing profile
    stored_profile = get_profile(user_id)

    if stored_profile:
        current_profile = UserProfile(**stored_profile)
        print("Loaded existing profile from database.")
    else:
        current_profile = None
        print("No existing profile found. Starting new session.")

    print("\nProfile Agent Started.")
    print("Type 'exit' to stop.")
    print("Type 'reset' to start a new product search.\n")

    user_input = input("You: ")

    while user_input.lower() != "exit":
        # Reset command
        if user_input.lower() == "reset":
            current_profile = None
            history = []
            print("\nProfile reset. Starting new product search.")
            user_input = input("You: ")
            continue

        # Run agent
        output, raw = run_profile_agent(user_input, history, current_profile)

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
            # STEP 4: Trigger Collector
            # ==============================
            if output.is_complete:
                # ------------------------------
                # Step 8: Safety checks
                # ------------------------------

                # 1) Check collection status
                profile_doc = db.user_profiles.find_one({"user_id": user_id})
                status = profile_doc.get("collection_status") if profile_doc else None

                if status == "running":
                    print("\nCollector is already running for this user.")

                else:
                    # 2) Check if products already exist
                    existing_products = db.products_raw.count_documents(
                        {"user_id": user_id}
                    )

                    if existing_products > 0:
                        print(
                            f"\nCollector skipped. {existing_products} products already exist for this user."
                        )

                    else:
                        print("\nStarting Collector...")

                        state = {"user_id": user_id, "queries": []}

                        def run_collector():
                            collector_graph.invoke(state)

                        thread = threading.Thread(target=run_collector, daemon=True)
                        thread.start()

                        print("Collector started in background.")

            print("\nYou can type 'reset' to search for another product.")
            user_input = input("You: ")


if __name__ == "__main__":
    chat_with_profile_agent()
