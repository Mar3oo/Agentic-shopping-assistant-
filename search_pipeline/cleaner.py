"""Cleaning and validation stage for the standalone product search pipeline."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def _log(message: str) -> None:
    print(f"[search_pipeline.cleaner] {message}")


def clean_products(products: list[dict]) -> list[dict]:
    """Normalize, validate, and deduplicate product dictionaries."""
    normalized = [_normalize_product(item) for item in products if isinstance(item, dict)]
    normalized = [item for item in normalized if item is not None]
    by_link = _deduplicate_by_link(normalized)
    deduplicated = _deduplicate_by_title(by_link)
    _log(f"Cleaned {len(products)} raw products into {len(deduplicated)} validated products.")
    return deduplicated


def _normalize_product(item: dict[str, Any]) -> dict | None:
    title = _clean_text(item.get("title"), max_length=200)
    link = _normalize_link(item.get("link"))
    if not title or not link:
        return None

    details_text = _clean_text(
        item.get("details_text") or item.get("snippet") or item.get("description"),
        max_length=500,
    )
    price_text = _clean_text(item.get("price_text"), max_length=80)
    raw_price = item.get("price")
    price = _parse_price(raw_price)
    if price is None and price_text:
        price = _parse_price(price_text)
    if price_text is None and raw_price is not None:
        price_text = _clean_text(str(raw_price), max_length=80)

    currency = _clean_text(item.get("currency"), max_length=12)
    if currency:
        currency = currency.upper()
    if not currency:
        currency = _infer_currency(price_text)

    return {
        "title": title,
        "price": price,
        "currency": currency,
        "price_text": price_text,
        "link": link,
        "source": _clean_text(item.get("source"), max_length=80),
        "details_text": details_text,
        "search_position": _to_int(item.get("search_position")),
    }


def _clean_text(value: Any, max_length: int) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).strip().split())
    if not text:
        return None
    return text[:max_length]


def _normalize_link(value: Any) -> str | None:
    if value is None:
        return None

    raw = str(value).strip()
    if not raw:
        return None

    parsed = urlparse(raw)
    if not parsed.scheme or not parsed.netloc:
        return None

    query_items = parse_qsl(parsed.query, keep_blank_values=True)
    filtered_query = []
    removable_keys = {
        "campaign",
        "cid",
        "fbclid",
        "gclid",
        "mc_cid",
        "mc_eid",
        "ref",
        "ref_",
        "tag",
        "tracking",
    }

    for key, query_value in query_items:
        lowered = key.casefold()
        if lowered.startswith("utm_") or lowered in removable_keys:
            continue
        filtered_query.append((key, query_value))

    cleaned = parsed._replace(query=urlencode(filtered_query, doseq=True), fragment="")
    return urlunparse(cleaned)


def _parse_price(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return None

    cleaned = re.sub(r"[^\d,.\-]", "", text)
    if not re.search(r"\d", cleaned):
        return None

    # Normalize comma/dot formats by treating the right-most separator as decimal
    # when it looks like a cents separator, and stripping the rest as thousands marks.
    if "," in cleaned and "." in cleaned:
        last_comma = cleaned.rfind(",")
        last_dot = cleaned.rfind(".")
        decimal_sep = "," if last_comma > last_dot else "."
        thousands_sep = "." if decimal_sep == "," else ","
        cleaned = cleaned.replace(thousands_sep, "")
        cleaned = cleaned.replace(decimal_sep, ".")
    elif cleaned.count(",") > 1:
        cleaned = cleaned.replace(",", "")
    elif cleaned.count(".") > 1:
        parts = cleaned.split(".")
        if len(parts[-1]) <= 2:
            cleaned = "".join(parts[:-1]) + "." + parts[-1]
        else:
            cleaned = "".join(parts)
    elif "," in cleaned:
        before, after = cleaned.split(",", 1)
        cleaned = before + "." + after if 0 < len(after) <= 2 else before + after

    try:
        return float(cleaned)
    except ValueError:
        return None


def _infer_currency(price_text: str | None) -> str | None:
    if not price_text:
        return None

    raw_text = str(price_text)
    upper_text = raw_text.upper()

    patterns = {
        "USD": (r"\$", r"\bUSD\b", r"\bUS\s*DOLLARS?\b"),
        "EUR": (r"\u20ac", r"\bEUR\b", r"\bEUROS?\b"),
        "GBP": (r"\u00a3", r"\bGBP\b", r"\bPOUNDS?\b"),
        "EGP": (r"\bEGP\b", r"\bL\.?E\.?\b"),
        "AED": (r"\bAED\b", r"\bDIRHAMS?\b"),
        "SAR": (r"\bSAR\b", r"\bRIYALS?\b"),
    }

    for currency, currency_patterns in patterns.items():
        if any(re.search(pattern, upper_text) for pattern in currency_patterns):
            return currency
    return None


def _to_int(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _deduplicate_by_link(products: list[dict]) -> list[dict]:
    # Keep the richest product for each normalized link so better LLM or search fields win.
    best_by_link: dict[str, dict] = {}
    for product in products:
        existing = best_by_link.get(product["link"])
        if existing is None or _quality_score(product) > _quality_score(existing):
            best_by_link[product["link"]] = product
    return list(best_by_link.values())


def _deduplicate_by_title(products: list[dict]) -> list[dict]:
    best_by_title: dict[str, dict] = {}
    for product in products:
        normalized_title = product["title"].casefold()
        existing = best_by_title.get(normalized_title)
        if existing is None or _quality_score(product) > _quality_score(existing):
            best_by_title[normalized_title] = product
    return list(best_by_title.values())


def _quality_score(product: dict) -> tuple:
    return (
        1 if product.get("price") is not None else 0,
        1 if product.get("details_text") else 0,
        1 if product.get("source") else 0,
        1 if product.get("search_position") is not None else 0,
        len(product.get("details_text") or ""),
    )
