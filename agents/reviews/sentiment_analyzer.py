from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "llama-3.3-70b-versatile"


def analyze_reviews(product_name, transcripts):

    combined = " ".join(transcripts[:3])[:8000]

    prompt = f"""
Analyze community sentiment about this product based on YouTube review transcripts.

Product: {product_name}

Transcript excerpts:
{combined}

Return:

1. overall sentiment score (0-100)
2. main pros
3. main cons
4. short summary
"""

    response = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.3
    )

    return response.choices[0].message.content
