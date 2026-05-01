"""Cleaning and validation stage for the standalone product search pipeline."""

from __future__ import annotations

import base64
import html
import re
from typing import Any
from urllib.parse import parse_qs, parse_qsl, unquote, urlencode, urlparse, urlunparse

import requests


REQUEST_TIMEOUT_SECONDS = 10
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
}
SOCIAL_DOMAINS = {
    "facebook",
    "instagram",
    "reddit",
    "tiktok",
    "twitter",
    "x",
    "youtube",
}
TRACKING_QUERY_KEYS = {
    "adgroup",
    "afid",
    "campaign",
    "cid",
    "cpng",
    "fbclid",
    "gclid",
    "g",
    "loc",
    "mc_cid",
    "mc_eid",
    "ref",
    "ref_",
    "selectedsellerid",
    "srsltid",
    "tag",
    "tcid",
    "tracking",
    "vid",
    "wmlspartner",
}
COMMON_SECOND_LEVEL_DOMAINS = {"co", "com", "edu", "gov", "net", "org"}


def _log(message: str) -> None:
    print(f"[search_pipeline.cleaner] {message}")


def clean_products(
    products: list[dict],
    search_results: list[dict] | None = None,
) -> list[dict]:
    """Normalize, ground, resolve, and deduplicate product dictionaries."""
    resolver_cache: dict[str, str] = {}
    grounding_index = _build_grounding_index(search_results or [])

    normalized = []
    for item in products:
        if not isinstance(item, dict):
            continue
        grounded = _match_grounding(item, grounding_index)
        cleaned = _normalize_product(
            item=item,
            grounded=grounded,
            resolver_cache=resolver_cache,
        )
        if cleaned is not None:
            normalized.append(cleaned)

    by_link = _deduplicate_by_link(normalized)
    deduplicated = _deduplicate_by_title(by_link)
    _log(
        f"Cleaned {len(products)} raw products into {len(deduplicated)} validated products.",
    )
    return deduplicated


def _normalize_product(
    item: dict[str, Any],
    grounded: dict[str, Any] | None,
    resolver_cache: dict[str, str],
) -> dict | None:
    title = _clean_text((grounded or {}).get("title") or item.get("title"), max_length=200)
    original_link = _normalize_link((grounded or {}).get("link") or item.get("link"))
    if not title or not original_link:
        return None

    resolved_link = _resolve_product_link(
        original_link,
        expected_source=(grounded or {}).get("source") or item.get("source"),
        product_title=title,
        resolver_cache=resolver_cache,
    )
    final_link = _normalize_link(resolved_link) or original_link

    details_text = _clean_text(
        (grounded or {}).get("details_text")
        or item.get("details_text")
        or item.get("snippet")
        or item.get("description"),
        max_length=500,
    )

    price_text = _extract_grounded_price_text(item=item, grounded=grounded, details_text=details_text)
    price = _parse_price(price_text)

    source = _extract_source_from_url(final_link)
    if not source:
        source = _extract_source_from_url(original_link)
    if not source:
        source = _normalize_source_label((grounded or {}).get("source") or item.get("source"))

    return {
        "title": title,
        "price": price,
        "currency": _infer_currency(price_text),
        "price_text": price_text,
        "link": final_link,
        "source": source,
        "details_text": details_text,
        "search_position": _to_int((grounded or {}).get("search_position") or item.get("search_position")),
    }


def _build_grounding_index(search_results: list[dict]) -> dict[str, Any]:
    by_position: dict[int, dict[str, Any]] = {}
    by_link: dict[str, dict[str, Any]] = {}
    by_title: dict[str, dict[str, Any]] = {}

    for result in search_results:
        if not isinstance(result, dict):
            continue

        position = _to_int(result.get("search_position"))
        if position is not None and position not in by_position:
            by_position[position] = result

        link = _normalize_link(result.get("link"))
        if link and link not in by_link:
            by_link[link] = result

        title = _title_key(result.get("title"))
        if title and title not in by_title:
            by_title[title] = result

    return {
        "by_position": by_position,
        "by_link": by_link,
        "by_title": by_title,
    }


def _match_grounding(item: dict[str, Any], grounding_index: dict[str, Any]) -> dict[str, Any] | None:
    position = _to_int(item.get("search_position"))
    if position is not None:
        grounded = grounding_index["by_position"].get(position)
        if grounded is not None:
            return grounded

    link = _normalize_link(item.get("link"))
    if link:
        grounded = grounding_index["by_link"].get(link)
        if grounded is not None:
            return grounded

    title = _title_key(item.get("title"))
    if title:
        return grounding_index["by_title"].get(title)

    return None


def _extract_grounded_price_text(
    item: dict[str, Any],
    grounded: dict[str, Any] | None,
    details_text: str | None,
) -> str | None:
    if grounded is not None:
        grounded_price_text = _clean_text(grounded.get("price_text"), max_length=80)
        if grounded_price_text:
            return grounded_price_text

        grounded_details = _clean_text(grounded.get("details_text"), max_length=500)
        extracted = _extract_price_from_text(grounded_details)
        if extracted:
            return extracted

    current_price_text = _clean_text(item.get("price_text"), max_length=80)
    if grounded is None and current_price_text:
        return current_price_text

    extracted = _extract_price_from_text(details_text)
    if extracted:
        return extracted

    if grounded is None:
        raw_price = item.get("price")
        if raw_price is not None:
            return _clean_text(str(raw_price), max_length=80)

    return None


def _resolve_product_link(
    url: str,
    expected_source: Any,
    product_title: str,
    resolver_cache: dict[str, str],
) -> str:
    cached = resolver_cache.get(url)
    if cached is not None:
        return cached

    resolved = url

    if _is_google_product_url(url):
        response = _safe_get(url)
        if response is not None:
            merchant_url = _extract_google_merchant_link(
                html_text=response.text,
                expected_source=expected_source,
                product_title=product_title,
            )
            if merchant_url:
                resolved = _follow_redirects(merchant_url)
            else:
                resolved = response.url or url
    else:
        resolved = _follow_redirects(url)

    resolver_cache[url] = resolved or url
    return resolver_cache[url]


def _extract_google_merchant_link(
    html_text: str,
    expected_source: Any,
    product_title: str,
) -> str | None:
    candidate_urls: list[str] = []

    for raw_url in re.findall(r'href="/url\?q=(https?://[^"&]+)', html_text):
        cleaned = _clean_embedded_url(raw_url)
        if cleaned and _is_merchant_candidate_url(cleaned):
            candidate_urls.append(cleaned)

    if not candidate_urls:
        for raw_url in re.findall(r'https?://[^"\s<>]+', html_text):
            cleaned = _clean_embedded_url(raw_url)
            if cleaned and _is_merchant_candidate_url(cleaned):
                candidate_urls.append(cleaned)

    if not candidate_urls:
        return None

    unique_candidates = list(dict.fromkeys(candidate_urls))
    expected_tokens = _source_tokens(expected_source)
    if expected_tokens:
        source_matched = [
            candidate
            for candidate in unique_candidates
            if _candidate_matches_source(candidate, expected_tokens)
        ]
        if source_matched:
            unique_candidates = source_matched
    title_tokens = _product_title_tokens(product_title)
    scored = sorted(
        unique_candidates,
        key=lambda candidate: _score_candidate_url(candidate, expected_tokens, title_tokens),
        reverse=True,
    )
    return scored[0]


def _score_candidate_url(
    url: str,
    expected_source_tokens: set[str],
    title_tokens: set[str],
) -> tuple[int, int, int, int]:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    host_tokens = set(re.findall(r"[a-z0-9]+", host))
    path_tokens = set(re.findall(r"[a-z0-9]+", parsed.path.casefold()))
    combined_tokens = host_tokens | path_tokens

    source_matches = len(expected_source_tokens & combined_tokens)
    title_matches = len(title_tokens & combined_tokens)
    has_path = 1 if parsed.path and parsed.path != "/" else 0
    query_bonus = 1 if parsed.query else 0

    return (source_matches, title_matches, has_path, query_bonus)


def _candidate_matches_source(url: str, expected_source_tokens: set[str]) -> bool:
    parsed = urlparse(url)
    combined_tokens = set(re.findall(r"[a-z0-9]+", f"{parsed.netloc} {parsed.path}".casefold()))
    return bool(expected_source_tokens & combined_tokens)


def _safe_get(url: str) -> requests.Response | None:
    try:
        response = requests.get(
            url,
            allow_redirects=True,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers=REQUEST_HEADERS,
        )
        response.raise_for_status()
        return response
    except requests.RequestException:
        return None


def _follow_redirects(url: str) -> str:
    unwrapped = _unwrap_known_redirect_url(url)
    response = _safe_get(unwrapped)
    if response is None:
        return unwrapped
    return _unwrap_known_redirect_url(response.url or unwrapped)


def _is_google_product_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    return host.endswith("google.com") and parsed.path == "/search" and "ibp=oshop" in parsed.query


def _is_merchant_candidate_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False

    host = parsed.netloc.lower()
    if not host:
        return False

    if host.endswith("google.com") or host.endswith("gstatic.com"):
        return False

    base_source = _extract_source_from_url(url)
    if base_source in SOCIAL_DOMAINS:
        return False

    return True


def _clean_embedded_url(value: str) -> str | None:
    if not value:
        return None

    cleaned = _decode_url_escapes(value)
    cleaned = cleaned.split("&sa=")[0].split("&ved=")[0].split("&usg=")[0].split("&opi=")[0]
    cleaned = cleaned.split("\\x26")[0]
    cleaned = unquote(cleaned)
    normalized = _normalize_link(cleaned)
    if normalized is None:
        return None
    return _unwrap_known_redirect_url(normalized)


def _decode_url_escapes(value: str) -> str:
    decoded = html.unescape(value)
    decoded = re.sub(r"\\u([0-9a-fA-F]{4})", lambda match: chr(int(match.group(1), 16)), decoded)
    decoded = re.sub(r"\\x([0-9a-fA-F]{2})", lambda match: chr(int(match.group(1), 16)), decoded)
    return decoded


def _unwrap_known_redirect_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if (
        host.endswith("walmart.com") and parsed.path == "/blocked"
    ) or (
        host.endswith("samsclub.com") and parsed.path == "/are-you-human"
    ):
        encoded_values = parse_qs(parsed.query).get("url")
        if not encoded_values:
            return url
        decoded_path = _decode_walmart_blocked_path(encoded_values[0])
        if decoded_path:
            if decoded_path.startswith("http://") or decoded_path.startswith("https://"):
                return decoded_path
            base_host = "https://www.samsclub.com" if host.endswith("samsclub.com") else "https://www.walmart.com"
            return _normalize_link(f"{base_host}{decoded_path}") or url
    return url


def _decode_walmart_blocked_path(value: str) -> str | None:
    candidate = value.strip()
    if not candidate:
        return None

    padding = "=" * (-len(candidate) % 4)
    try:
        decoded = base64.b64decode(candidate + padding).decode("utf-8")
    except Exception:
        return None

    return decoded.strip() or None


def _extract_source_from_url(url: str | None) -> str | None:
    if not url:
        return None

    parsed = urlparse(url)
    host = parsed.netloc.lower().split("@")[-1].split(":")[0]
    if not host:
        return None

    parts = [part for part in host.split(".") if part and part not in {"m", "www"}]
    if not parts:
        return None

    if len(parts) >= 3 and len(parts[-1]) == 2 and parts[-2] in COMMON_SECOND_LEVEL_DOMAINS:
        return parts[-3]

    if len(parts) >= 2:
        return parts[-2]

    return parts[0]


def _normalize_source_label(value: Any) -> str | None:
    cleaned = _clean_text(value, max_length=80)
    if not cleaned:
        return None
    tokens = re.findall(r"[a-z0-9]+", cleaned.casefold())
    if not tokens:
        return None
    return "".join(tokens)


def _source_tokens(value: Any) -> set[str]:
    cleaned = _clean_text(value, max_length=80)
    if not cleaned:
        return set()

    tokens = set(re.findall(r"[a-z0-9]+", cleaned.casefold()))
    if len(tokens) > 1:
        tokens.add("".join(re.findall(r"[a-z0-9]+", cleaned.casefold())))
    return tokens


def _product_title_tokens(value: Any) -> set[str]:
    cleaned = _clean_text(value, max_length=200)
    if not cleaned:
        return set()

    stop_words = {"a", "an", "and", "for", "gaming", "inch", "laptop", "of", "the", "with"}
    return {token for token in re.findall(r"[a-z0-9]+", cleaned.casefold()) if token not in stop_words}


def _extract_price_from_text(value: str | None) -> str | None:
    if not value:
        return None

    patterns = [
        r"(?:(?:USD|EUR|GBP|EGP|AED|SAR)\s*)?[$\u20ac\u00a3]?\s?\d[\d,]*(?:\.\d{1,2})?",
        r"\b\d[\d,]*(?:\.\d{1,2})?\s*(?:USD|EUR|GBP|EGP|AED|SAR)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, value, flags=re.IGNORECASE)
        if match:
            return _clean_text(match.group(0), max_length=80)
    return None


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

    for key, query_value in query_items:
        lowered = key.casefold()
        if lowered.startswith("utm_") or lowered in TRACKING_QUERY_KEYS:
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

    upper_text = str(price_text).upper()
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


def _title_key(value: Any) -> str | None:
    cleaned = _clean_text(value, max_length=200)
    if not cleaned:
        return None
    return cleaned.casefold()


def _deduplicate_by_link(products: list[dict]) -> list[dict]:
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
        1 if product.get("source") else 0,
        1 if product.get("details_text") else 0,
        1 if product.get("search_position") is not None else 0,
        len(product.get("details_text") or ""),
    )
