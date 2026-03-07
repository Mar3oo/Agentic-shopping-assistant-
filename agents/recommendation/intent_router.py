"""
LLM Intent Router for Recommendation Mode.
Uses Groq to classify user intent into structured JSON.
"""

import json
from typing import Dict, Any
from groq import Groq
from agents.recommendation.prompts import system_prompt


class RecommendationIntentRouter:
    """
    Uses LLM to detect user intent during recommendation conversation.
    """

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.client = Groq(api_key=api_key)
        self.model = model

    def route(
        self,
        user_message: str,
        current_recommendations: list,
    ) -> Dict[str, Any]:
        """
        Returns structured intent:
        {
            "intent": "...",
            "budget_min": float | null,
            "budget_max": float | null,
            "brand": str | null
        }
        """

        SYSTEM_PROMPT = system_prompt.strip()

        recommendations_text = "\n".join(
            [f"- {r['title']} ({r['price']})" for r in current_recommendations]
        )

        user_prompt = f"""
Current recommendations:
{recommendations_text}

User message:
{user_message}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )

        content = response.choices[0].message.content.strip()

        # try extracting JSON from text
        start = content.find("{")
        end = content.rfind("}") + 1

        if start != -1 and end != -1:
            content = content[start:end]

        try:
            return json.loads(content)

        except json.JSONDecodeError:
            return {
                "intent": "general_question",
                "budget_min": None,
                "budget_max": None,
                "brand": None,
            }
