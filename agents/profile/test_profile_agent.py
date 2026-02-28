from agents.profile.agent import run_profile_agent
from Data_base.profile_repo import get_profile, save_profile
from agents.profile.schemas import UserProfile


def chat_with_profile_agent():
    user_id = "user_001"
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

            print("\nYou can type 'reset' to search for another product.")
            user_input = input("You: ")


if __name__ == "__main__":
    chat_with_profile_agent()
