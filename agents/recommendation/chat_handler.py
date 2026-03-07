"""
Recommendation Mode Chat Handler.
Executes actions based on LLM intent classification.
"""

import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from groq import Groq

from agents.recommendation.intent_router import RecommendationIntentRouter
from agents.recommendation.agent import RecommendationAgent

from agents.reviews.youtube_service import search_youtube, get_transcripts_for_videos
from agents.reviews.sentiment_analyzer import analyze_reviews

load_dotenv()


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
        """
        Returns:
        {
            "type": "...",
            "data": ...
        }
        """

        intent_data = self.router.route(user_message, current_recommendations)

        intent = intent_data.get("intent")

        # -----------------------------
        # 1️⃣ Budget refinement
        # -----------------------------
        if intent == "refine_budget":
            new_min = intent_data.get("budget_min")
            new_max = intent_data.get("budget_max")

            if new_min is not None:
                current_profile["budget_min"] = new_min
            if new_max is not None:
                current_profile["budget_max"] = new_max

            new_recs = self.rec_agent.recommend(current_profile)

            return {"type": "recommendation_update", "data": new_recs}

        # -----------------------------
        # 2️⃣ Brand refinement
        # -----------------------------
        if intent == "refine_brand":
            brand = intent_data.get("brand")

            if brand:
                filtered = [
                    r
                    for r in current_recommendations
                    if brand.lower() in r["title"].lower()
                ]

                if filtered:
                    return {"type": "recommendation_update", "data": filtered[:3]}

            return {
                "type": "message",
                "data": "No products found for that brand in current results.",
            }

        # -----------------------------
        # 3️⃣ Explanation request
        # -----------------------------
        if intent == "ask_explanation":
            explanation = self._generate_explanation(
                current_profile, current_recommendations
            )
            return {"type": "message", "data": explanation}

        # -----------------------------
        # 4️⃣ General product question
        # -----------------------------
        if intent == "general_question":
            answer = self._answer_general_question(
                user_message, current_recommendations
            )
            return {"type": "message", "data": answer}

        # -----------------------------
        # 5️⃣ New search requested
        # -----------------------------
        if intent == "new_search":
            return {"type": "new_search", "data": None}

        # -----------------------------
        # 6️⃣ Review sentiment analysis
        # -----------------------------

        if intent == "review_sentiment":
            product = current_recommendations[0]

            videos = search_youtube(product["title"] + " review")

            video_ids = [v["video_id"] for v in videos]

            transcripts = get_transcripts_for_videos(video_ids)

            sentiment = analyze_reviews(product["title"], transcripts)

            return {"type": "message", "data": sentiment}

        # Fallback
        return {
            "type": "message",
            "data": "I'm not sure how to help with that. Could you clarify?",
        }

    # ------------------------------------
    # LLM explanation generator
    # ------------------------------------
    def _generate_explanation(
        self,
        profile: Dict[str, Any],
        recommendations: List[Dict[str, Any]],
    ) -> str:

        prompt = f"""
User profile:
{profile}

Recommendations:
{recommendations}

Explain clearly and concisely why these products match the user's needs.
"""

        response = self.llm.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )

        return response.choices[0].message.content.strip()

    # ------------------------------------
    # General Q&A handler
    # ------------------------------------
    def _answer_general_question(
        self,
        user_message: str,
        recommendations: List[Dict[str, Any]],
    ) -> str:

        prompt = f"""
Current recommended products:
{recommendations}

User question:
{user_message}

Answer clearly using product context.
"""

        response = self.llm.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )

        return response.choices[0].message.content.strip()

    def get_product_reviews(self, product):

        product_name = product.get("title")

        videos = search_youtube(product_name + " review")

        if not videos:
            return "No review videos found."

        video_ids = [v["video_id"] for v in videos]

        transcripts = get_transcripts_for_videos(video_ids)

        if not transcripts:
            return "No transcripts available for analysis."

        sentiment = analyze_reviews(product_name, transcripts)

        video_links = "\n".join([f"- {v['title']} ({v['link']})" for v in videos[:3]])

        return f"""
    YouTube Community Review Analysis

    Product: {product_name}

    {sentiment}

    Top review videos:
    {video_links}
    """

    def compare_products(self, p1, p2):

        prompt = f"""
    Compare these two products and help the user decide.

    Product 1:
    Title: {p1.get("title")}
    Price: {p1.get("price")}
    Details: {p1.get("details_text")}

    Product 2:
    Title: {p2.get("title")}
    Price: {p2.get("price")}
    Details: {p2.get("details_text")}

    Explain:

    1. Performance
    2. Build quality
    3. Battery life (if relevant)
    4. Value for money
    5. Which user each product is better for

    Give a clear final recommendation.
    """

        response = self.llm.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
        )

        return response.choices[0].message.content.strip()
