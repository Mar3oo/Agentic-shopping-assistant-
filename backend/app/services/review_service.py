from agents.reviews.agent import ReviewAgent

review_sessions = {}


def start_review(user_id: str, message: str):
    agent = ReviewAgent()

    result = agent.handle_message(message)

    review_sessions[user_id] = agent

    return {
        "status": "success",
        "type": "review",
        "message": "Here are the reviews",
        "data": result,
    }


def chat_review(user_id: str, message: str):
    agent = review_sessions.get(user_id)

    if not agent:
        return {
            "status": "error",
            "type": "review",
            "message": "Start review first",
            "data": {},
        }

    result = agent.handle_message(message)

    return {
        "status": "success",
        "type": "review",
        "message": "Updated review",
        "data": result,
    }
