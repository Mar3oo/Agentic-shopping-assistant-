from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

MODEL = "llama-3.3-70b-versatile"


def _get_client() -> Groq | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)


def _parse_json_payload(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end <= start:
        return None

    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        return None


def _fallback_mapping(title: str) -> dict[str, str]:
    cleaned = " ".join((title or "").strip().split())
    return {
        "product_full": cleaned,
        "product_clean": cleaned,
    }


def extract_clean_product_mappings(titles: list[str]) -> list[dict[str, str]]:
    normalized_titles = [
        " ".join((title or "").strip().split())
        for title in titles
        if str(title or "").strip()
    ]
    if not normalized_titles:
        return []

    client = _get_client()
    if client is None:
        return [_fallback_mapping(title) for title in normalized_titles]

    prompt = f"""
You clean noisy shopping product titles into concise product names.

Your job:
1. Extract a clean product name from each messy title.
2. Remove RAM, storage, colors, screen size, minor specs, merchant info, and marketing text.
3. Keep the brand, model name, and important generation or version number.
4. Do not invent missing information.
5. Return names that work well for YouTube review search and product comparison.

Examples:
- "HP EliteBook 845 G8 | AMD Ryzen 5 Pro | 14 inch | RAM 16GB | Hardisk 256GB SSD Silver"
  -> "HP EliteBook 845 G8"
- "Dell Latitude 5410 14 inch FHD Business Laptop Intel Core i5 16GB RAM 512GB SSD"
  -> "Dell Latitude 5410"
- "Apple iPhone 15 Pro Max 256GB Blue Titanium"
  -> "Apple iPhone 15 Pro Max"

Return ONLY valid JSON with this format:
{{
  "products": [
    {{
      "product_full": "original input title",
      "product_clean": "clean product name"
    }}
  ]
}}

Titles:
{json.dumps(normalized_titles, ensure_ascii=False, indent=2)}
""".strip()

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You normalize messy product titles into clean product names. "
                        "Return JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        raw = response.choices[0].message.content.strip()
        payload = _parse_json_payload(raw)
        products = payload.get("products") if isinstance(payload, dict) else None
        if not isinstance(products, list):
            return [_fallback_mapping(title) for title in normalized_titles]

        mappings: list[dict[str, str]] = []
        for index, original_title in enumerate(normalized_titles):
            item = products[index] if index < len(products) and isinstance(products[index], dict) else {}
            full_title = str(item.get("product_full") or original_title).strip() or original_title
            clean_name = str(item.get("product_clean") or full_title).strip() or full_title
            mappings.append(
                {
                    "product_full": full_title,
                    "product_clean": clean_name,
                }
            )
        return mappings
    except Exception:
        return [_fallback_mapping(title) for title in normalized_titles]


def extract_clean_product_name(title: str) -> str:
    mappings = extract_clean_product_mappings([title])
    if not mappings:
        return " ".join((title or "").strip().split())
    return mappings[0]["product_clean"]
