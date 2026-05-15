"""Search stage for the standalone product search pipeline."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

import requests


DEFAULT_SERPER_BASE_URL = "https://google.serper.dev"


def _log(message: str) -> None:
    print(f"[search_pipeline.search] {message}")


class SerperSearchClient:
    """Small Serper.dev client that returns normalized search results."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEFAULT_SERPER_BASE_URL,
        timeout: int = 20,
    ) -> None:
        self.api_key = api_key or os.getenv("SERPER_API_KEY")
        if not self.api_key:
            raise ValueError("SERPER_API_KEY is required to use SerperSearchClient.")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def search(
        self,
        query: str,
        num_results: int = 10,
        gl: str | None = None,
        hl: str | None = None,
    ) -> list[dict]:
        """Search Serper shopping results first, then fall back to organic search."""
        cleaned_query = (query or "").strip()
        if not cleaned_query:
            raise ValueError("query must not be blank.")

        requested_results = max(1, int(num_results))
        payload = {"q": cleaned_query, "num": requested_results}
        if gl:
            payload["gl"] = gl
        if hl:
            payload["hl"] = hl

        _log(f"Searching shopping results for query: {cleaned_query!r}")
        shopping_payload = self._post("/shopping", payload)
        shopping_results = self._normalize_shopping_results(
            shopping_payload.get("shopping", []),
        )
        if shopping_results:
            limited_results = shopping_results[:requested_results]
            _log(
                f"Found {len(shopping_results)} shopping results. "
                f"Returning top {len(limited_results)}.",
            )
            return limited_results

        _log("No usable shopping results. Falling back to organic search.")
        organic_payload = self._post("/search", payload)
        organic_results = self._normalize_organic_results(
            organic_payload.get("organic", []),
        )
        limited_results = organic_results[:requested_results]
        _log(
            f"Found {len(organic_results)} organic results. "
            f"Returning top {len(limited_results)}.",
        )
        return limited_results

    def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            body = exc.response.text[:300] if exc.response is not None else ""
            status_code = exc.response.status_code if exc.response is not None else "unknown"
            raise RuntimeError(
                f"Serper request failed with status {status_code}: {body}",
            ) from exc
        except requests.RequestException as exc:
            raise RuntimeError(f"Serper request failed: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError("Serper returned invalid JSON.") from exc

        if not isinstance(data, dict):
            raise RuntimeError("Serper returned an unexpected response shape.")
        return data

    def _normalize_shopping_results(self, results: Any) -> list[dict]:
        normalized: list[dict] = []
        if not isinstance(results, list):
            return normalized

        for index, item in enumerate(results, start=1):
            if not isinstance(item, dict):
                continue

            title = self._clean_text(item.get("title"))
            link = self._clean_text(item.get("link")) or self._clean_text(item.get("productLink"))
            if not title or not link:
                continue

            price_text = self._stringify_price(item.get("priceText"), item.get("price"))
            snippet_parts = self._build_shopping_details(item)
            normalized.append(
                {
                    "title": title,
                    "link": link,
                    "price_text": price_text,
                    "details_text": " | ".join(part for part in snippet_parts if part) or None,
                    "source": self._clean_text(item.get("source"))
                    or self._source_from_link(link),
                    "search_position": self._to_int(item.get("position")) or index,
                },
            )

        return normalized

    def _build_shopping_details(self, item: dict[str, Any]) -> list[str]:
        details = []

        snippet = self._clean_text(item.get("snippet"))
        if snippet:
            details.append(snippet)

        delivery = self._clean_text(item.get("delivery"))
        if delivery:
            details.append(f"Delivery: {delivery}")

        rating = item.get("rating")
        rating_count = item.get("ratingCount")
        if rating is not None:
            rating_text = f"Rating: {rating}"
            if rating_count is not None:
                rating_text += f" ({rating_count} reviews)"
            details.append(rating_text)

        source = self._clean_text(item.get("source"))
        if source:
            details.append(f"Merchant: {source}")

        return details

    def _normalize_organic_results(self, results: Any) -> list[dict]:
        normalized: list[dict] = []
        if not isinstance(results, list):
            return normalized

        for index, item in enumerate(results, start=1):
            if not isinstance(item, dict):
                continue

            title = self._clean_text(item.get("title"))
            link = self._clean_text(item.get("link"))
            if not title or not link:
                continue

            normalized.append(
                {
                    "title": title,
                    "link": link,
                    "price_text": self._stringify_price(item.get("priceText"), item.get("price")),
                    "details_text": self._clean_text(item.get("snippet"))
                    or self._clean_text(item.get("description")),
                    "source": self._clean_text(item.get("source"))
                    or self._source_from_link(link),
                    "search_position": self._to_int(item.get("position")) or index,
                },
            )

        return normalized

    @staticmethod
    def _clean_text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _to_int(value: Any) -> int | None:
        try:
            if value is None or value == "":
                return None
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _stringify_price(*values: Any) -> str | None:
        for value in values:
            if value is None:
                continue
            if isinstance(value, (int, float)):
                return str(value)
            text = str(value).strip()
            if text:
                return text
        return None

    @staticmethod
    def _source_from_link(link: str) -> str | None:
        netloc = urlparse(link).netloc.lower()
        if not netloc:
            return None
        return netloc.removeprefix("www.")
