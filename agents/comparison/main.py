from agents.comparison.agent import ComparisonAgent


def run_chat():
    agent = ComparisonAgent()

    print("=== Comparison Agent ===")
    print("Type 'exit' to quit")
    print("Type 'new_comparison' to start over\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        response = agent.handle_message(user_input)
        print(f"\nAgent: {response}\n")


if __name__ == "__main__":
    run_chat()
