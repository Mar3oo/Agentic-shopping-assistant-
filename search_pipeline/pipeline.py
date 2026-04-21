"""Orchestration layer for the standalone product search pipeline."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from search_pipeline.cleaner import clean_products
    from search_pipeline.extractor import ExtractionError, GroqProductExtractor
    from search_pipeline.ranker import ProductRanker
    from search_pipeline.search import SerperSearchClient
except ImportError:  # pragma: no cover - enables direct script execution
    from cleaner import clean_products
    from extractor import ExtractionError, GroqProductExtractor
    from ranker import ProductRanker
    from search import SerperSearchClient


def _log(message: str) -> None:
    print(f"[search_pipeline.pipeline] {message}")


class SearchPipeline:
    """Full search -> extract -> clean -> rank pipeline."""

    def __init__(
        self,
        search_client: SerperSearchClient | None = None,
        extractor: GroqProductExtractor | None = None,
        ranker: ProductRanker | None = None,
    ) -> None:
        self.search_client = search_client or SerperSearchClient()
        self.extractor = extractor or GroqProductExtractor()
        self.ranker = ranker or ProductRanker()

    def run(
        self,
        query: str,
        search_limit: int = 10,
        top_k: int = 5,
        gl: str | None = None,
        hl: str | None = None,
    ) -> list[dict]:
        cleaned_query = (query or "").strip()
        if not cleaned_query:
            raise ValueError("query must not be blank.")

        search_results = self.search_client.search(
            query=cleaned_query,
            num_results=search_limit,
            gl=gl,
            hl=hl,
        )
        if not search_results:
            _log("Search returned no results.")
            return []

        extracted_products: list[dict] = []
        try:
            extracted_products = self.extractor.extract(
                query=cleaned_query,
                search_results=search_results,
                max_products=search_limit,
            )
        except ExtractionError as exc:
            _log(f"Extractor failed. Using direct search fallback. Reason: {exc}")

        if not extracted_products:
            extracted_products = self._build_fallback_products(search_results)

        cleaned_products = clean_products(extracted_products)
        if not cleaned_products:
            _log("No products remained after cleaning.")
            return []

        return self.ranker.rank(query=cleaned_query, products=cleaned_products, top_k=top_k)

    @staticmethod
    def _build_fallback_products(search_results: list[dict]) -> list[dict]:
        _log("Building fallback products directly from normalized search results.")
        fallback_products = []
        for item in search_results:
            fallback_products.append(
                {
                    "title": item.get("title"),
                    "price": item.get("price"),
                    "currency": item.get("currency"),
                    "price_text": item.get("price_text"),
                    "link": item.get("link"),
                    "source": item.get("source"),
                    "details_text": item.get("details_text"),
                    "search_position": item.get("search_position"),
                },
            )
        return fallback_products


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the standalone search pipeline.")
    parser.add_argument("query", nargs="+", help="User search query.")
    parser.add_argument("--search-limit", type=int, default=10, help="Number of Serper results to fetch.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of ranked products to return.")
    parser.add_argument("--gl", default=None, help="Optional country code for Serper.")
    parser.add_argument("--hl", default=None, help="Optional language code for Serper.")
    return parser.parse_args(argv)


def _load_env_file(path: str | os.PathLike[str] = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        key, value = line.split("=", 1)
        cleaned_value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), cleaned_value)


def main(argv: list[str] | None = None) -> int:
    _load_env_file()
    args = _parse_args(argv or sys.argv[1:])
    query = " ".join(args.query).strip()

    try:
        pipeline = SearchPipeline()
        products = pipeline.run(
            query=query,
            search_limit=args.search_limit,
            top_k=args.top_k,
            gl=args.gl,
            hl=args.hl,
        )
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(products, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
