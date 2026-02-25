"""Record ingestion pipeline for validating, normalizing, and storing products in MongoDB."""

from datetime import datetime
import re
from typing import Any, Dict, List

from pymongo.errors import DuplicateKeyError, PyMongoError

from .db import get_collection


def _is_blank(value: Any) -> bool:
    """Return True when a required value is missing or empty."""
    return value is None or (isinstance(value, str) and not value.strip())


def _to_datetime(value: Any) -> datetime | None:
    """Convert an ISO datetime string (or datetime) into a datetime object."""
    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"

        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            return None

    return None


def _to_float(value: Any) -> float | None:
    """Safely convert mixed numeric representations into a float."""
    if isinstance(value, bool) or value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        cleaned = re.sub(r"[^\d.]", "", value)
        if not cleaned:
            return None

        if cleaned.count(".") > 1:
            first, *rest = cleaned.split(".")
            cleaned = first + "." + "".join(rest)

        try:
            return float(cleaned)
        except ValueError:
            return None

    return None


def _trim_text(value: Any, max_length: int = 1000) -> str | None:
    """Return a stripped string capped to max_length characters."""
    if value is None:
        return None
    return str(value).strip()[:max_length]


def _validate_and_prepare(record: Dict[str, Any]) -> Dict[str, Any]:
    """Validate required fields and normalize the record for storage."""
    if not isinstance(record, dict):
        raise ValueError("Record must be a dictionary.")

    metadata = record.get("metadata")
    product = record.get("product")

    if not isinstance(metadata, dict):
        raise ValueError("metadata must be a dictionary.")
    if not isinstance(product, dict):
        raise ValueError("product must be a dictionary.")

    if _is_blank(metadata.get("source")):
        raise ValueError("metadata.source is required.")

    scraped_at = _to_datetime(metadata.get("scraped_at"))
    if scraped_at is None:
        raise ValueError("metadata.scraped_at must be a valid datetime.")

    title = product.get("title")
    if _is_blank(title):
        raise ValueError("product.title is required.")

    price = _to_float(product.get("price"))
    if price is None:
        raise ValueError("product.price must be a valid number.")

    link = product.get("link")
    if _is_blank(link):
        raise ValueError("product.link is required.")

    normalized = {
        "metadata": dict(metadata),
        "product": dict(product),
    }

    normalized["metadata"]["source"] = str(metadata["source"]).strip()
    normalized["metadata"]["scraped_at"] = scraped_at

    normalized["product"]["title"] = str(title).strip()
    normalized["product"]["price"] = price

    normalized_link = str(link).strip().split("?")[0].split("#")[0]
    if not normalized_link:
        raise ValueError("product.link is empty after normalization.")
    normalized["product"]["link"] = normalized_link

    details_text = product.get("details_text")
    if details_text is not None:
        normalized["product"]["details_text"] = _trim_text(details_text, max_length=1000)

    return normalized


def ingest_records(records: List[Dict[str, Any]]) -> Dict[str, int]:
    """Insert validated records into MongoDB and report inserted/skipped/failed counts."""
    summary = {"inserted": 0, "skipped": 0, "failed": 0}

    if not isinstance(records, list):
        raise TypeError("records must be a list of dictionaries.")

    collection = get_collection()

    for record in records:
        try:
            prepared = _validate_and_prepare(record)
            collection.insert_one(prepared)
            summary["inserted"] += 1
        except DuplicateKeyError:
            summary["skipped"] += 1
        except (ValueError, TypeError, PyMongoError):
            summary["failed"] += 1

    return summary
