"""
Recommendation Mode Chat Handler.
Handles refinement vs new search cleanly.
"""

import os
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv
from groq import Groq

from agents.recommendation.intent_router import RecommendationIntentRouter
from agents.recommendation.agent import RecommendationAgent

load_dotenv()

logger = logging.getLogger(__name__)


def adjust_budget_from_preferences(profile, recommendations, preferences):
    if "price" not in preferences:
        return profile

    strength = preferences["price"]

    if not recommendations:
        return profile

    prices = [p["price"] for p in recommendations if p.get("price")]

    if not prices:
        return profile

    avg_price = sum(prices) / len(prices)

    # smarter adjustment
    new_max = avg_price * (1 - 0.3 * strength)

    profile["budget_max"] = new_max

    return profile


class RecommendationChatHandler:
    def __init__(self, user_id: str):
        self.router = RecommendationIntentRouter(api_key=os.getenv("GROQ_API_KEY"))
        self.rec_agent = RecommendationAgent(user_id)
        self.llm = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"

    def handle(
        self,
        user_message: str,
        current_profile: Dict[str, Any],
        current_recommendations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        intent_data = self.router.route(user_message, current_recommendations)
        intent = intent_data.get("intent")

        logger.info(f"[ChatHandler] Intent: {intent}")

        # -----------------------------
        # 🔴 0️⃣ NEW SEARCH (RESET)
        # -----------------------------
        if intent == "new_search":
            logger.info("[ChatHandler] Resetting session for new search")

            return {
                "type": "new_search",
                "data": {"message": "Starting a new search. What are you looking for?"},
            }

        # -----------------------------
        # 🟢 1️⃣ Budget refinement
        # -----------------------------
        if intent == "refine_budget":
            new_min = intent_data.get("budget_min")
            new_max = intent_data.get("budget_max")

            if new_min is not None:
                current_profile["budget_min"] = new_min
            if new_max is not None:
                current_profile["budget_max"] = new_max

            return {
                "type": "recommendation_update",
                "data": self.rec_agent.recommend(current_profile),
            }

        # -----------------------------
        # 🟡 2️⃣ Preference refinement
        # -----------------------------
        if intent == "refine_preferences":
            priorities = current_profile.get("priorities", {}) or {}
            new_prefs = intent_data.get("preferences", {})

            # -------------------------
            # Update priorities
            # -------------------------
            if new_prefs:
                for k, v in new_prefs.items():
                    priorities[k] = min(max(v, 0), 1)

            current_profile["priorities"] = priorities

            # -------------------------
            # 🔥 SMART budget adjustment
            # -------------------------
            current_profile = adjust_budget_from_preferences(
                current_profile, current_recommendations, new_prefs
            )

            # -------------------------
            # Re-run recommendation
            # -------------------------
            new_recs = self.rec_agent.recommend(current_profile)

            return {
                "type": "recommendation_update",
                "data": new_recs,
            }

        # -------------------------
        # Handle "in between" / balanced requests
        # -------------------------
        user_text = user_message.lower()

        if any(
            word in user_text
            for word in ["between", "balanced", "middle", "in between"]
        ):
            prices = [p["price"] for p in current_recommendations if p.get("price")]

            if prices:
                min_p = min(prices)
                max_p = max(prices)

                #  create mid-range window
                new_min = min_p + (max_p - min_p) * 0.3
                new_max = min_p + (max_p - min_p) * 0.7

                current_profile["budget_min"] = new_min
                current_profile["budget_max"] = new_max
        # -----------------------------
        # 🔵 3️⃣ Brand refinement
        # -----------------------------
        if intent == "refine_brand":
            brand = intent_data.get("brand")

            if brand:
                filtered = [
                    r
                    for r in current_recommendations
                    if brand.lower() in (r.get("title") or "").lower()
                ]

                if filtered:
                    return {
                        "type": "recommendation_update",
                        "data": filtered[:3],
                    }

            return {
                "type": "message",
                "data": "No products found for that brand in current results.",
            }

        # -----------------------------
        # 🟣 4️⃣ Explanation
        # -----------------------------
        if intent == "ask_explanation":
            return {
                "type": "message",
                "data": self._generate_explanation(
                    current_profile, current_recommendations
                ),
            }

        # -----------------------------
        # ⚪ 5️⃣ General question
        # -----------------------------
        if intent == "general_question":
            return {
                "type": "message",
                "data": self._answer_general_question(
                    user_message, current_recommendations
                ),
            }

        # -----------------------------
        # Fallback
        # -----------------------------
        return {
            "type": "message",
            "data": "Could you clarify what you'd like to change?",
        }

    # ------------------------------------
    # Explanation
    # ------------------------------------
    def _generate_explanation(self, profile, recommendations):

        try:
            prompt = f"""
User profile:
{profile}

Top products:
{recommendations[:3]}

Explain briefly why these match the user.
"""

            response = self.llm.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
            )

            return response.choices[0].message.content.strip()

        except Exception:
            return "These products were selected based on your preferences."

    # ------------------------------------
    # General Q&A
    # ------------------------------------
    def _answer_general_question(self, user_message, recommendations):

        try:
            prompt = f"""
Products:
{recommendations[:5]}

User question:
{user_message}

Answer clearly.
"""

            response = self.llm.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
            )

            return response.choices[0].message.content.strip()

        except Exception:
            return "I can help compare these products if you'd like."
