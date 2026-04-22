import hashlib
import json

from Data_Base.cache_repo import get_cache_entry, upsert_cache_entry

DEFAULT_TTLS = {
    "comparison": 24 * 60 * 60,
    "review": 12 * 60 * 60,
    "search": 60 * 60,
}


def _normalize_value(value):
    if isinstance(value, str):
        return " ".join(value.lower().strip().split())
    if isinstance(value, dict):
        return {key: _normalize_value(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_normalize_value(item) for item in value]
    return value


def build_cache_key(namespace: str, fingerprint: dict, version: str = "v1") -> str:
    normalized = _normalize_value(fingerprint)
    digest = hashlib.sha256(
        json.dumps(normalized, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    return f"{namespace}:{version}:{digest}"


def load_cached_response(namespace: str, fingerprint: dict) -> dict | None:
    cache_key = build_cache_key(namespace, fingerprint)
    entry = get_cache_entry(cache_key)
    if not entry:
        return None
    return entry.get("response")


def store_cached_response(
    namespace: str,
    fingerprint: dict,
    response: dict,
    ttl_seconds: int | None = None,
) -> None:
    cache_key = build_cache_key(namespace, fingerprint)
    upsert_cache_entry(
        cache_key=cache_key,
        namespace=namespace,
        request_fingerprint=_normalize_value(fingerprint),
        response=response,
        ttl_seconds=ttl_seconds or DEFAULT_TTLS[namespace],
    )
