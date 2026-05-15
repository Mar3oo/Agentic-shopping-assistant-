from groq import Groq
import os
from dotenv import load_dotenv
import json

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "llama-3.3-70b-versatile"


def analyze_reviews(product_name, transcripts):

    combined = " ".join(transcripts[:2])[:6000]

    prompt = f"""
You are an expert product review analyst.

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
            "summary": "Could not analyze reviews",
            "sentiment_score": "unknown",
            "pros": [],
            "cons": [],
            "value_for_money": "",
            "insights": [],
            "best_for": [],
        }
