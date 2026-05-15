import logging
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MODEL = "llama-3.3-70b-versatile"


class LLMReranker:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def rerank(self, user_query, products, top_k=4):
        """
        Use LLM to rerank top candidates.
        """

        if not products:
            return []

        if len(products) <= top_k:
            return products

        try:
            # -------------------------
            # Build product text (safe length)
            # -------------------------
            product_blocks = []

            for i, p in enumerate(products):
                details = (p.get("details_text") or "")[:200]

                price = p.get("price")

                block = f"""
            Product {i + 1}
            Title: {p.get("title")}
            Price: {price} EGP

            Key Info:
            {details}
            """
                product_blocks.append(block)

            product_text = "\n".join(product_blocks)
            # -------------------------
            # Prompt (clean + strict)
            # -------------------------
            prompt = f"""
You are a professional shopping assistant.

User request:
{user_query}

Below are product candidates.

{product_text}

Your task:
- Select the BEST {top_k} products
- Balance:
  - price vs performance
  - real-world usability
  - value for money

IMPORTANT:
- Do NOT just pick the most powerful
- Do NOT just pick the cheapest
- Prefer balanced and reasonable options

Return ONLY product numbers like:
1,4,7
"""

            # -------------------------
            # LLM call
            # -------------------------
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )

            text = response.choices[0].message.content.strip()

            # -------------------------
            # Parse output safely
            # -------------------------
            indices = []

            for x in text.replace(" ", "").split(","):
                if x.isdigit():
                    idx = int(x) - 1
                    if 0 <= idx < len(products):
                        indices.append(idx)

            # fallback if parsing fails
            if not indices:
                logger.warning("[LLM] Failed to parse response, using default ranking")
                return products[:top_k]

            selected = [products[i] for i in indices]

            logger.info(f"[LLM] Reranked {len(selected)} products")

            return selected[:top_k]

        except Exception as e:
            logger.error(f"[LLM] Rerank failed: {e}")

            # fallback → return top_k from original ranking
            return products[:top_k]
