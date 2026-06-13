from groq import Groq
import os
from dotenv import load_dotenv
import json

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "llama-3.3-70b-versatile"


def _language_instruction(language: str) -> str:
    if language == "ar":
        return (
            "Write every user-facing JSON value in Arabic. "
            "Keep product names, model names, brand names, and technical specs in English when appropriate. "
            "Use Arabic sentiment labels only: إيجابي / محايد / سلبي. "
            "Do not translate the JSON keys."
        )

    return "Write every user-facing JSON value in English."


def analyze_reviews(product_name, transcripts, language: str = "en"):

    combined = " ".join(transcripts[:2])[:6000]

    prompt = f"""
You are an expert product review analyst.
{_language_instruction(language)}

Product:
{product_name}

Review data:
----------------
{combined}
----------------

Return ONLY valid JSON.

FORMAT:

{{
  "summary": "2-3 lines overall verdict",
  "sentiment_score": "positive / neutral / negative",
  "pros": ["...", "...", "..."],
  "cons": ["...", "..."],
  "value_for_money": "short statement",
  "insights": ["...", "..."],
  "best_for": ["...", "..."]
}}

RULES:
- No markdown
- No extra text
- Keep it concise
- Match the requested response language for summary, sentiment_score, pros, cons, value_for_money, insights, and best_for
"""

    response = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.3
    )

    raw = response.choices[0].message.content

    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        cleaned = raw[start:end]

        return json.loads(cleaned)
    except Exception:
        return {
            "summary": "تعذر تحليل المراجعات" if language == "ar" else "Could not analyze reviews",
            "sentiment_score": "غير معروف" if language == "ar" else "unknown",
            "pros": [],
            "cons": [],
            "value_for_money": "",
            "insights": [],
            "best_for": [],
        }
