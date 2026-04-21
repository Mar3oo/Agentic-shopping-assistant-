from groq import Groq
import os
from dotenv import load_dotenv

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

            Return TWO sections:

            === QUICK SUMMARY ===
            - Overall verdict (1–2 lines)
            - Sentiment score
            - Top 3 pros
            - Top 2 cons
            - Value for money (1 line)

            === DETAILED ANALYSIS ===
            1) PROS (full)
            2) CONS (full)
            3) KEY INSIGHTS
            4) WHO IS THIS FOR

            Rules:
            - Do NOT repeat information between sections
            - Keep quick summary very concise
            - Use ONLY the provided data
            """

    response = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.3
    )

    return response.choices[0].message.content
