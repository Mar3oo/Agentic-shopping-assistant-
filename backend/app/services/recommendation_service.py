from agents.profile.agent import run_profile_agent
from agents.recommendation.agent import RecommendationAgent
from agents.recommendation.profile_adapter import adapt_profile
from agents.recommendation.chat_handler import RecommendationChatHandler

from Data_base.profile_repo import save_profile
from Data_base.profile_repo import get_profile

# simple in-memory session store
user_sessions = {}


def start_recommendation(user_id: str, message: str):
    # 1) Generate profile from user input
    parsed, _ = run_profile_agent(message)

    profile = parsed.profile.model_dump()

    # 2) Save profile
    save_profile(user_id, profile)

    # 3) Adapt profile for recommendation system
    adapted_profile = adapt_profile(profile)

    # 4) Get recommendations
    agent = RecommendationAgent(user_id)
    products = agent.recommend(adapted_profile)

    # STORE SESSION
    user_sessions[user_id] = {"profile": adapted_profile, "recommendations": products}

    return {
        "status": "success",
        "type": "recommendations",
        "message": "Here are some products for you",
        "data": {
            "products": products,
            "suggestions": [
                {
                    "type": "compare",
                    "trigger": "after_recommendations",
                    "message": "Want help comparing these products?",
                },
                {
                    "type": "review",
                    "trigger": "after_recommendations",
                    "message": "Want to check real user reviews?",
                },
            ],
        },
    }


def chat_recommendation(user_id: str, message: str):
    # 1) Load saved profile
    saved_profile = get_profile(user_id)

    if not saved_profile:
        return {
            "type": "error",
            "message": "No active session. Start with /recommendation/start",
        }

    # 2) Adapt profile
    adapted_profile = adapt_profile(saved_profile)

    # 3) Get current recommendations
    rec_agent = RecommendationAgent(user_id)
    current_recommendations = rec_agent.recommend(adapted_profile)

    # 4) Chat handler
    chat_handler = RecommendationChatHandler(user_id)

    response = chat_handler.handle(
        user_message=message,
        current_profile=adapted_profile,
        current_recommendations=current_recommendations,
    )

    # update recommendations if changed
    if response.get("type") == "recommendation_update":
        user_sessions[user_id]["recommendations"] = response["data"]

    # NORMALIZE OUTPUT
    if response["type"] == "recommendation_update":
        return {
            "status": "success",
            "type": "recommendations",
            "message": "Updated recommendations",
            "data": {
                "products": response["data"],
                "suggestions": [
                    {
                        "type": "compare",
                        "trigger": "after_recommendations",
                        "message": "Want help comparing these products?",
                    },
                    {
                        "type": "review",
                        "trigger": "after_recommendations",
                        "message": "Want to check real user reviews?",
                    },
                ],
            },
        }

    elif response["type"] == "message":
        return {
            "status": "success",
            "type": "message",
            "message": response["data"],
            "data": {},
        }

    elif response["type"] == "new_search":
        return {
            "status": "success",
            "type": "reset",
            "message": "Starting a new search",
            "data": {},
        }

    return {
        "status": "error",
        "type": "message",
        "message": "Something went wrong",
        "data": {},
    }
