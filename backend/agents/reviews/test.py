from agent import ReviewAgent

agent = ReviewAgent()

print(agent.handle_message("reviews for iphone 13"))
print("=" * 50)
print(agent.handle_message("is it good for its cost?"))
