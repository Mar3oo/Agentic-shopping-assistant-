"""Record ingestion pipeline responsible for validating and upserting product records into MongoDB."""

from datetime import datetime
import re
from typing import Any, Dict, List

from pymongo.errors import PyMongoError
from agents.recommendation.embedding_model import get_embedding_model

from .db import get_collection


def _is_blank(value: Any) -> bool:
    """Return True when a required value is missing or empty."""
    return value is None or (isinstance(value, str) and not value.strip())


def _to_datetime(value: Any) -> datetime | None:
    """Convert a datetime value (or ISO datetime string) into a datetime object."""
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


def _classify_product_type(search_query: str) -> str:
    q = (search_query or "").lower()

    if "laptop" in q:
        return "laptop"
    if "keyboard" in q:
        return "keyboard"
    if "book" in q:
        return "book"
    if "phone" in q or "smartphone" in q:
        return "phone"
    if "headphone" in q:
        return "headphones"

    return "other"


def _validate_and_prepare(record: Dict[str, Any]) -> Dict[str, Any]:
    """Validate mandatory fields and normalize a record before MongoDB upsert."""
    if not isinstance(record, dict):
        raise ValueError("Record must be a dictionary.")

    metadata = record.get("metadata")
    product = record.get("product")

    if not isinstance(metadata, dict):
        raise ValueError("metadata must be a dictionary.")
    if not isinstance(product, dict):
        raise ValueError("product must be a dictionary.")

    source = metadata.get("source")
    if _is_blank(source):
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

    normalized_link = str(link).strip().split("?")[0].split("#")[0]
    if not normalized_link:
        raise ValueError("product.link is empty after normalization.")

    details_text = _trim_text(product.get("details_text"), max_length=1000)
    seller_score = _to_float(product.get("seller_score"))

    category = product.get("category")
    if _is_blank(category):
        category = None
    else:
        category = str(category).strip()

    search_query = metadata.get("search_query")
    product_type = _classify_product_type(search_query)

    return {
        "metadata": {
            "source": str(source).strip(),
            "scraped_at": scraped_at,
            "search_query": metadata.get("search_query"),
            "page_number": metadata.get("page_number"),
        },
        "product": {
            "title": str(title).strip(),
            "price": price,
            "link": normalized_link,
            "details_text": details_text,
            "seller_score": seller_score,
            "category": category,
            "product_type": product_type,
        },
    }


def _build_product_semantic_text(prepared: Dict[str, Any]) -> str:
    """
    Build semantic text representation for embedding.
    Handles missing fields safely.
    """
    product = prepared["product"]

    parts = []

    if product.get("title"):
        parts.append(f"Title: {product['title']}")

    if product.get("category"):
        parts.append(f"Category: {product['category']}")

    if product.get("details_text"):
        parts.append(f"Details: {product['details_text']}")

    return "\n".join(parts)


def _upsert_record(prepared: Dict[str, Any]) -> str:
    """
    Upsert one normalized record.
    If inserted → generate embedding.
    If updated → do not re-embed (performance optimization).
    """
    collection = get_collection()
    link = prepared["product"]["link"]

    # Check if product already exists
    existing = collection.find_one({"product.link": link}, {"_id": 1})

    update_doc = {
        "$set": {
            "metadata.source": prepared["metadata"]["source"],
            "metadata.search_query": prepared["metadata"].get("search_query"),
            "metadata.page_number": prepared["metadata"].get("page_number"),
            "metadata.scraped_at": prepared["metadata"]["scraped_at"],
            "product.title": prepared["product"]["title"],
            "product.price": prepared["product"]["price"],
            "product.details_text": prepared["product"].get("details_text"),
            "product.seller_score": prepared["product"].get("seller_score"),
            "product.category": prepared["product"].get("category"),
            "product.product_type": prepared["product"].get("product_type"),
        },
        "$setOnInsert": {
            "product.link": link,
        },
    }

    # If new product → generate embedding
    if existing is None:
        semantic_text = _build_product_semantic_text(prepared)

        if semantic_text.strip():
            model = get_embedding_model()
            embedding = model.encode([semantic_text])[0].tolist()

            update_doc["$set"]["product.embedding"] = embedding

    result = collection.update_one({"product.link": link}, update_doc, upsert=True)

    if result.upserted_id is not None:
        return "inserted"

    return "updated"


def ingest_records(records: List[Dict[str, Any]]) -> Dict[str, int]:
    """Upsert records into MongoDB and return inserted/updated/failed summary."""
    if not isinstance(records, list):
        raise TypeError("records must be a list of dictionaries.")

    summary = {"inserted": 0, "updated": 0, "failed": 0, "error_samples": []}

    for record in records:
        try:
            prepared = _validate_and_prepare(record)
            status = _upsert_record(prepared)
            summary[status] += 1
        except (ValueError, TypeError, PyMongoError) as exc:
            summary["failed"] += 1
            if len(summary["error_samples"]) < 3:
                summary["error_samples"].append(str(exc))

    return summary
