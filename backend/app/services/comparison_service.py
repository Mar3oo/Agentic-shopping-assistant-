from agents.comparison.agent import ComparisonAgent

# simple session store
comparison_sessions = {}


def start_comparison(user_id: str, message: str):
    agent = ComparisonAgent()

    response = agent.handle_message(message)

    # store agent session
    comparison_sessions[user_id] = agent

    return {
        "status": "success",
        "type": "comparison",
        "message": "Here is your comparison",
        "data": response,
    }


def chat_comparison(user_id: str, message: str):
    agent = comparison_sessions.get(user_id)

    if not agent:
        return {
            "status": "error",
            "type": "comparison",
            "message": "Start comparison first",
            "data": {},
        }

    response = agent.handle_message(message)

    return {
        "status": "success",
        "type": "comparison",
        "message": "Updated comparison",
        "data": response,
    }
