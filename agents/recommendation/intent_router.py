import json
import logging
from typing import Dict, Any
from groq import Groq
from agents.recommendation.prompts import system_prompt

logger = logging.getLogger(__name__)


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
            "brand": str | null,
            "preferences": {...}
        }
        """

        SYSTEM_PROMPT = system_prompt.strip()

        # -------------------------
        # Limit recommendations to avoid long prompts
        # -------------------------
        limited_recs = current_recommendations[:5]

        recommendations_text = "\n".join(
            [f"- {r.get('title')} ({r.get('price')})" for r in limited_recs]
        )

        user_prompt = f"""
Current recommendations:
{recommendations_text}

User message:
{user_message}

Return ONLY a valid JSON object.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
            )

            content = response.choices[0].message.content.strip()

            # -------------------------
            # Extract JSON safely
            # -------------------------
            start = content.find("{")
            end = content.rfind("}") + 1

            if start != -1 and end != -1:
                content = content[start:end]

            parsed = json.loads(content)

            # -------------------------
            # Ensure required keys exist
            # -------------------------
            return {
                "intent": parsed.get("intent", "general_question"),
                "budget_min": parsed.get("budget_min"),
                "budget_max": parsed.get("budget_max"),
                "brand": parsed.get("brand"),
                "preferences": parsed.get("preferences", {}),
            }

        except Exception as e:
            logger.error(f"[IntentRouter] Failed: {e}")

            return {
                "intent": "general_question",
                "budget_min": None,
                "budget_max": None,
                "brand": None,
                "preferences": {},
            }
