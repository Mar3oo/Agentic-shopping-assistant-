from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

MODEL = "llama-3.3-70b-versatile"


class LLMReranker:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def rerank(self, user_query, products, top_k=3):

        if len(products) <= top_k:
            return products

        product_text = ""

        for i, p in enumerate(products):
            product_text += f"""
Product {i + 1}
Title: {p.get("title")}
Price: {p.get("price")}
Details: {p.get("details_text")}
"""

        prompt = f"""
User request:
{user_query}

Below are product candidates.

{product_text}

Select the {top_k} products that best match the user's request.

Return ONLY the product numbers like this example:
1,4,7
"""

        response = self.client.chat.completions.create(
            model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0
        )

        text = response.choices[0].message.content.strip()

        indices = []

        for x in text.replace(" ", "").split(","):
            if x.isdigit():
                indices.append(int(x) - 1)

        selected = []

        for i in indices:
            if 0 <= i < len(products):
                selected.append(products[i])

        return selected[:top_k]
