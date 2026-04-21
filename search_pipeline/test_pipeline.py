"""Runnable smoke script for the standalone search pipeline."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from search_pipeline.cleaner import clean_products
    import search_pipeline.cleaner as cleaner_module
    from search_pipeline.extractor import ExtractionError
    from search_pipeline.pipeline import SearchPipeline
    from search_pipeline.ranker import ProductRanker
    from search_pipeline.search import SerperSearchClient
except ImportError:  # pragma: no cover - enables direct script execution
    from cleaner import clean_products
    import cleaner as cleaner_module
    from extractor import ExtractionError
    from pipeline import SearchPipeline
    from ranker import ProductRanker
    from search import SerperSearchClient


def _log(message: str) -> None:
    print(f"[search_pipeline.test_pipeline] {message}")


class FakeSearchClient:
    def __init__(self, mode: str = "default") -> None:
        self.mode = mode

    def search(self, query: str, num_results: int = 10, gl: str | None = None, hl: str | None = None) -> list[dict]:
        if self.mode == "empty":
            return []

        return [
            {
                "title": "Lenovo Legion Pro 5 Gaming Laptop",
                "link": "https://shop.example.com/products/legion-pro-5?ref=search",
                "price_text": "$1,299.99",
                "details_text": "16GB RAM, RTX graphics, fast refresh display",
                "source": "shop.example.com",
                "search_position": 1,
            },
            {
                "title": "Lenovo Legion Pro 5 Gaming Laptop",
                "link": "https://shop.example.com/products/legion-pro-5?campaign=duplicate",
                "price_text": "$1,299.99",
                "details_text": "Duplicate search result with same product",
                "source": "shop.example.com",
                "search_position": 2,
            },
            {
                "title": "ASUS TUF Gaming Laptop A15",
                "link": "https://store.example.com/asus-tuf-a15#reviews",
                "price_text": "EGP 50,000",
                "details_text": "Ryzen gaming laptop with solid thermals",
                "source": "store.example.com",
                "search_position": 3,
            },
        ][:num_results]


class FakeExtractor:
    def __init__(self, mode: str = "messy") -> None:
        self.mode = mode

    def extract(self, query: str, search_results: list[dict], max_products: int = 10) -> list[dict]:
        if self.mode == "invalid":
            raise ExtractionError("Simulated invalid JSON from Groq.")

        return [
            {
                "title": " Lenovo Legion Pro 5 Gaming Laptop ",
                "price": "$1,299.99",
                "currency": "",
                "price_text": None,
                "link": "https://shop.example.com/products/legion-pro-5?ref=llm",
                "source": "Example Shop",
                "details_text": " 16GB RAM, RTX graphics, gaming display ",
                "search_position": "1",
            },
            {
                "title": "Lenovo Legion Pro 5 Gaming Laptop",
                "price_text": "$1,299.99",
                "link": "https://shop.example.com/products/legion-pro-5?campaign=duplicate",
                "details_text": "duplicate title and product",
                "source": "Example Shop",
                "search_position": 2,
            },
            {
                "title": "ASUS TUF Gaming Laptop A15",
                "price_text": "EGP 50,000",
                "link": "https://store.example.com/asus-tuf-a15#specs",
                "source": "Example Store",
                "details_text": "Ryzen gaming laptop for 1080p play",
                "search_position": 3,
            },
            {
                "title": "",
                "price_text": "$999",
                "link": "https://bad.example.com/missing-title",
            },
            {
                "title": "No Link Product",
                "price_text": "$999",
                "link": "",
            },
        ][:max_products]


def _assert_canonical_shape(products: list[dict]) -> None:
    required_fields = {
        "rank",
        "title",
        "price",
        "currency",
        "price_text",
        "link",
        "source",
        "details_text",
        "search_position",
        "relevance_score",
    }
    for product in products:
        missing = required_fields - set(product)
        assert not missing, f"Missing canonical fields: {missing}"


def _run_smoke_test() -> None:
    _log("Running default smoke test with messy extracted products.")
    pipeline = SearchPipeline(
        search_client=FakeSearchClient(),
        extractor=FakeExtractor(mode="messy"),
        ranker=ProductRanker(),
    )
    results = pipeline.run(query="best gaming laptop", search_limit=5, top_k=5)
    _assert_canonical_shape(results)
    assert len(results) == 2, f"Expected deduped products, got {len(results)}"
    titles = {result["title"] for result in results}
    assert titles == {
        "Lenovo Legion Pro 5 Gaming Laptop",
        "ASUS TUF Gaming Laptop A15",
    }
    prices = {result["title"]: result["price"] for result in results}
    assert prices["Lenovo Legion Pro 5 Gaming Laptop"] == 1299.99
    assert prices["ASUS TUF Gaming Laptop A15"] == 50000.0
    assert all(result["source"] == "example" for result in results)
    _log("Smoke test passed.")
    print(json.dumps(results, indent=2, ensure_ascii=False))


def _run_fallback_test() -> None:
    _log("Running fallback test with simulated extraction failure.")
    pipeline = SearchPipeline(
        search_client=FakeSearchClient(),
        extractor=FakeExtractor(mode="invalid"),
        ranker=ProductRanker(),
    )
    results = pipeline.run(query="best gaming laptop", search_limit=5, top_k=5)
    _assert_canonical_shape(results)
    assert results, "Fallback should still return products."
    assert results[0]["link"].startswith("https://")
    _log("Fallback test passed.")


def _run_empty_search_test() -> None:
    _log("Running empty search test.")
    pipeline = SearchPipeline(
        search_client=FakeSearchClient(mode="empty"),
        extractor=FakeExtractor(),
        ranker=ProductRanker(),
    )
    results = pipeline.run(query="anything", search_limit=5, top_k=5)
    assert results == [], f"Expected empty result list, got {results}"
    _log("Empty search test passed.")


def _run_blank_query_test() -> None:
    _log("Running blank query validation test.")
    pipeline = SearchPipeline(
        search_client=FakeSearchClient(),
        extractor=FakeExtractor(),
        ranker=ProductRanker(),
    )
    try:
        pipeline.run(query="   ")
    except ValueError:
        _log("Blank query test passed.")
        return
    raise AssertionError("Blank query should raise ValueError.")


def _run_google_link_preservation_test() -> None:
    _log("Running Google Shopping link preservation test.")
    google_like = [
        {
            "title": "Product One",
            "price_text": "$999",
            "link": "https://www.google.com/search?ibp=oshop&prds=pid:111&q=test&utm_source=ad",
            "source": "Merchant A",
            "details_text": "First result",
            "search_position": 1,
        },
        {
            "title": "Product Two",
            "price_text": "$1099",
            "link": "https://www.google.com/search?ibp=oshop&prds=pid:222&q=test&utm_source=ad",
            "source": "Merchant B",
            "details_text": "Second result",
            "search_position": 2,
        },
    ]
    cleaned = clean_products(google_like)
    ranked = ProductRanker().rank(query="test product", products=cleaned, top_k=5)
    assert len(ranked) == 2, "Distinct Google Shopping links should remain distinct after cleaning."
    assert ranked[0]["link"] != ranked[1]["link"]
    _log("Google Shopping link preservation test passed.")


class FakeSerperClient(SerperSearchClient):
    def __init__(self) -> None:
        super().__init__(api_key="test-key")

    def _post(self, endpoint: str, payload: dict) -> dict:
        if endpoint == "/shopping":
            return {
                "shopping": [
                    {
                        "title": f"Product {index}",
                        "source": f"Store {index}",
                        "link": f"https://www.google.com/search?ibp=oshop&prds=pid:{index}&q=test",
                        "price": f"${index}.00",
                        "rating": 4.5,
                        "ratingCount": 10 * index,
                        "position": index,
                    }
                    for index in range(1, 6)
                ],
            }
        return {"organic": []}


def _run_search_limit_test() -> None:
    _log("Running Serper search-limit test.")
    client = FakeSerperClient()
    results = client.search(query="test query", num_results=2)
    assert len(results) == 2, f"Expected search client to honor num_results, got {len(results)}"
    assert results[0]["search_position"] == 1
    assert results[1]["search_position"] == 2
    _log("Serper search-limit test passed.")


def _run_grounded_cleaner_test() -> None:
    _log("Running grounded cleaner resolution test.")

    class _FakeResponse:
        def __init__(self, url: str, text: str = "", status_code: int = 200) -> None:
            self.url = url
            self.text = text
            self.status_code = status_code

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise RuntimeError(f"HTTP {self.status_code}")

    original_get = cleaner_module.requests.get

    def _fake_get(url: str, **kwargs):
        if "google.com/search" in url:
            html = (
                '<a href="/url?q=https://www.amazon.com/dp/B0TEST1234%3Fref_%3Dabc'
                '&amp;sa=U&amp;ved=xyz">Visit site</a>'
            )
            return _FakeResponse(url=url, text=html)
        if "amazon.com/dp/B0TEST1234" in url:
            return _FakeResponse(url="https://www.amazon.com/dp/B0TEST1234?ref_=abc")
        raise AssertionError(f"Unexpected URL requested during test: {url}")

    cleaner_module.requests.get = _fake_get
    try:
        cleaned = clean_products(
            products=[
                {
                    "title": "Laptop Placeholder",
                    "price_text": "$9999.00",
                    "link": "https://www.google.com/search?ibp=oshop&prds=pid:111&q=test",
                    "source": "Google",
                    "details_text": "Bad LLM data",
                    "search_position": 1,
                }
            ],
            search_results=[
                {
                    "title": "ASUS TUF Gaming A15",
                    "price_text": "$1,299.99",
                    "link": "https://www.google.com/search?ibp=oshop&prds=pid:111&q=test",
                    "source": "Amazon",
                    "details_text": "Official shopping price",
                    "search_position": 1,
                }
            ],
        )
    finally:
        cleaner_module.requests.get = original_get

    assert len(cleaned) == 1
    assert cleaned[0]["title"] == "ASUS TUF Gaming A15"
    assert cleaned[0]["link"] == "https://www.amazon.com/dp/B0TEST1234"
    assert cleaned[0]["source"] == "amazon"
    assert cleaned[0]["price"] == 1299.99
    _log("Grounded cleaner resolution test passed.")


def _run_redirect_cleanup_test() -> None:
    _log("Running redirect cleanup test.")

    class _FakeResponse:
        def __init__(self, url: str, text: str = "", status_code: int = 200) -> None:
            self.url = url
            self.text = text
            self.status_code = status_code

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise RuntimeError(f"HTTP {self.status_code}")

    original_get = cleaner_module.requests.get

    def _fake_get(url: str, **kwargs):
        if "google.com/search" in url:
            html = (
                '<a href="/url?q=https://www.bestbuy.com/product/item/JJGQJH2LFP/sku/11871431'
                '?ref\\u003d212\\u0026utm_source\\u003dgoogle&amp;sa=U">Visit site</a>'
            )
            return _FakeResponse(url=url, text=html)
        if "bestbuy.com/product/item/JJGQJH2LFP/sku/11871431" in url:
            return _FakeResponse(url="https://www.bestbuy.com/product/item/JJGQJH2LFP/sku/11871431?ref=212")
        raise AssertionError(f"Unexpected URL requested during test: {url}")

    cleaner_module.requests.get = _fake_get
    try:
        cleaned = clean_products(
            products=[
                {
                    "title": "Gaming Laptop",
                    "link": "https://www.google.com/search?ibp=oshop&prds=pid:222&q=test",
                    "source": "Best Buy",
                    "search_position": 1,
                }
            ],
            search_results=[
                {
                    "title": "Gaming Laptop",
                    "price_text": "$1,149.99",
                    "link": "https://www.google.com/search?ibp=oshop&prds=pid:222&q=test",
                    "source": "Best Buy",
                    "search_position": 1,
                }
            ],
        )
    finally:
        cleaner_module.requests.get = original_get

    assert len(cleaned) == 1
    assert cleaned[0]["link"] == "https://www.bestbuy.com/product/item/JJGQJH2LFP/sku/11871431"
    assert cleaned[0]["source"] == "bestbuy"
    _log("Redirect cleanup test passed.")


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


def _run_live_mode(query: str, search_limit: int, top_k: int, gl: str | None, hl: str | None) -> None:
    _log("Running live mode.")
    _load_env_file()

    missing = [name for name in ("SERPER_API_KEY", "GROQ_API_KEY") if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    pipeline = SearchPipeline()
    results = pipeline.run(query=query, search_limit=search_limit, top_k=top_k, gl=gl, hl=hl)
    _assert_canonical_shape(results)
    print(json.dumps(results, indent=2, ensure_ascii=False))


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-test the standalone search pipeline.")
    parser.add_argument("--live", action="store_true", help="Run the real Serper + Groq pipeline.")
    parser.add_argument(
        "--query",
        default="best gaming laptop under 1500",
        help="Query used for live mode.",
    )
    parser.add_argument("--search-limit", type=int, default=5, help="Search result limit.")
    parser.add_argument("--top-k", type=int, default=5, help="Ranked product limit.")
    parser.add_argument("--gl", default=None, help="Optional country code for Serper.")
    parser.add_argument("--hl", default=None, help="Optional language code for Serper.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])

    try:
        if args.live:
            _run_live_mode(
                query=args.query,
                search_limit=args.search_limit,
                top_k=args.top_k,
                gl=args.gl,
                hl=args.hl,
            )
        else:
            _run_smoke_test()
            _run_fallback_test()
            _run_empty_search_test()
            _run_blank_query_test()
            _run_google_link_preservation_test()
            _run_search_limit_test()
            _run_grounded_cleaner_test()
            _run_redirect_cleanup_test()
    except Exception as exc:
        print(f"Smoke script failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
