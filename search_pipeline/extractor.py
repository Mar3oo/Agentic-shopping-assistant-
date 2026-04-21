"""LLM extraction stage for the standalone product search pipeline."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import requests


DEFAULT_GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"


def _log(message: str) -> None:
    print(f"[search_pipeline.extractor] {message}")


class ExtractionError(RuntimeError):
    """Raised when LLM extraction fails and the pipeline should fall back."""


class GroqProductExtractor:
    """Extract structured products from search results using Groq."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_GROQ_MODEL,
        api_url: str = DEFAULT_GROQ_API_URL,
        timeout: int = 45,
    ) -> None:
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self.api_url = api_url
        self.timeout = timeout

    def extract(
        self,
        query: str,
        search_results: list[dict],
        max_products: int = 10,
    ) -> list[dict]:
        """Return extracted product dictionaries or raise ExtractionError."""
        if not search_results:
            return []

        if not self.api_key:
            raise ExtractionError("GROQ_API_KEY is required for product extraction.")

        prompt = self._build_prompt(query=query, search_results=search_results, max_products=max_products)
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You extract shopping products from search results. "
                        "Reply with JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            body = exc.response.text[:300] if exc.response is not None else ""
            status_code = exc.response.status_code if exc.response is not None else "unknown"
            raise ExtractionError(
                f"Groq request failed with status {status_code}: {body}",
            ) from exc
        except requests.RequestException as exc:
            raise ExtractionError(f"Groq request failed: {exc}") from exc

        try:
            response_data = response.json()
        except ValueError as exc:
            raise ExtractionError("Groq returned invalid JSON.") from exc

        content = self._extract_message_content(response_data)
        parsed_payload = self._parse_json_payload(content)
        products = self._coerce_product_list(parsed_payload)
        normalized = [self._normalize_product(item) for item in products if isinstance(item, dict)]
        normalized = [item for item in normalized if item]

        if not normalized:
            raise ExtractionError("Groq returned no usable products.")

        _log(f"Extracted {len(normalized)} product candidates from Groq.")
        return normalized[:max_products]

    def _build_prompt(self, query: str, search_results: list[dict], max_products: int) -> str:
        compact_results = json.dumps(search_results[:max_products], ensure_ascii=False, indent=2)
        return f"""
User query:
{query}

Search results:
{compact_results}

Return either:
1. a JSON object with a "products" array, or
2. a bare JSON array.

Each product should use this schema as closely as possible:
{{
  "title": "string",
  "price": "string or number or null",
  "currency": "string or null",
  "price_text": "string or null",
  "link": "string",
  "source": "string or null",
  "details_text": "string or null",
  "search_position": 1
}}

Rules:
- Use only the provided search results.
- Include at most {max_products} products.
- Do not invent links or prices.
- If a field is missing, return null.
- Return JSON only with no explanation.
""".strip()

    @staticmethod
    def _extract_message_content(response_data: dict[str, Any]) -> str:
        choices = response_data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ExtractionError("Groq response is missing choices.")

        message = choices[0].get("message")
        if not isinstance(message, dict):
            raise ExtractionError("Groq response is missing message content.")

        content = message.get("content")
        if isinstance(content, list):
            text_parts = []
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "text":
                    continue
                text_value = block.get("text")
                if isinstance(text_value, str) and text_value.strip():
                    text_parts.append(text_value.strip())
            content = "\n".join(text_parts)

        if not isinstance(content, str) or not content.strip():
            raise ExtractionError("Groq response content is empty.")
        return content.strip()

    def _parse_json_payload(self, text: str) -> Any:
        parsers = (
            self._parse_direct_json,
            self._parse_fenced_json,
            self._parse_balanced_json,
        )

        for parser in parsers:
            parsed = parser(text)
            if parsed is not None:
                return parsed

        raise ExtractionError("Could not parse JSON from Groq response.")

    @staticmethod
    def _parse_direct_json(text: str) -> Any:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _parse_fenced_json(text: str) -> Any:
        matches = re.findall(r"```(?:json)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue
        return None

    @staticmethod
    def _parse_balanced_json(text: str) -> Any:
        for start_index, character in enumerate(text):
            if character not in "[{":
                continue

            stack: list[str] = ["}" if character == "{" else "]"]
            in_string = False
            escape = False

            for current_index in range(start_index + 1, len(text)):
                current_char = text[current_index]

                if in_string:
                    if escape:
                        escape = False
                    elif current_char == "\\":
                        escape = True
                    elif current_char == '"':
                        in_string = False
                    continue

                if current_char == '"':
                    in_string = True
                    continue

                if current_char in "[{":
                    stack.append("}" if current_char == "{" else "]")
                    continue

                if current_char in "}]":
                    if not stack or current_char != stack[-1]:
                        break
                    stack.pop()
                    if not stack:
                        candidate = text[start_index : current_index + 1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            break

        return None

    @staticmethod
    def _coerce_product_list(payload: Any) -> list[dict]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]

        if isinstance(payload, dict):
            for key in ("products", "items", "results"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]

        raise ExtractionError("Parsed Groq JSON did not contain a product list.")

    @staticmethod
    def _normalize_product(item: dict[str, Any]) -> dict | None:
        title = GroqProductExtractor._pick_text(item, "title", "name", "product_name")
        link = GroqProductExtractor._pick_text(item, "link", "url", "product_url")
        if not title or not link:
            return None

        raw_price = item.get("price")
        price_text = GroqProductExtractor._pick_text(
            item,
            "price_text",
            "priceText",
            "price_string",
            "priceLabel",
        )
        if price_text is None and raw_price is not None:
            price_text = str(raw_price)

        return {
            "title": title,
            "price": raw_price if isinstance(raw_price, (int, float, str)) else None,
            "currency": GroqProductExtractor._pick_text(
                item,
                "currency",
                "currency_code",
                "price_currency",
            ),
            "price_text": price_text,
            "link": link,
            "source": GroqProductExtractor._pick_text(
                item,
                "source",
                "merchant",
                "seller",
                "store",
                "site",
            ),
            "details_text": GroqProductExtractor._pick_text(
                item,
                "details_text",
                "details",
                "description",
                "snippet",
                "summary",
            ),
            "search_position": GroqProductExtractor._pick_int(
                item,
                "search_position",
                "position",
                "rank",
            ),
        }

    @staticmethod
    def _pick_text(item: dict[str, Any], *keys: str) -> str | None:
        for key in keys:
            value = item.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        return None

    @staticmethod
    def _pick_int(item: dict[str, Any], *keys: str) -> int | None:
        for key in keys:
            value = item.get(key)
            try:
                if value is not None and value != "":
                    return int(value)
            except (TypeError, ValueError):
                continue
        return None
