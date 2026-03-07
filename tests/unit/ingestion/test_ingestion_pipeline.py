import copy
from datetime import datetime

import pytest
from pymongo.errors import PyMongoError

from Data_base import ingestion


def test_to_datetime_parses_iso_and_z_suffix():
    # Arrange

    # Act
    parsed_z = ingestion._to_datetime("2026-03-01T10:00:00Z")
    parsed_offset = ingestion._to_datetime("2026-03-01T10:00:00+00:00")

    # Assert
    assert isinstance(parsed_z, datetime)
    assert isinstance(parsed_offset, datetime)
    assert parsed_z.year == 2026
    assert parsed_offset.year == 2026


def test_to_datetime_returns_none_for_invalid_inputs():
    # Arrange
    invalid_values = [None, "", "   ", "invalid-date", 123]

    # Act
    results = [ingestion._to_datetime(value) for value in invalid_values]

    # Assert
    assert all(result is None for result in results)


def test_to_float_handles_mixed_and_malformed_values():
    # Arrange

    # Act
    parsed_currency = ingestion._to_float("EGP 1,234.56")
    parsed_multi_dot = ingestion._to_float("1.2.3")
    parsed_large = ingestion._to_float("999999999999999999.99")
    parsed_empty = ingestion._to_float("")
    parsed_text = ingestion._to_float("N/A")
    parsed_bool = ingestion._to_float(False)

    # Assert
    assert parsed_currency == 1234.56
    assert parsed_multi_dot == 1.23
    assert parsed_large == 1000000000000000000.0
    assert parsed_empty is None
    assert parsed_text is None
    assert parsed_bool is None


def test_validate_and_prepare_normalizes_record_and_classifies_type(monkeypatch):
    # Arrange
    calls = []

    def fake_classify(text):
        calls.append(text)
        return "gaming_laptop"

    monkeypatch.setattr(ingestion, "classify_product_type", fake_classify)

    record = {
        "metadata": {
            "source": " amazon ",
            "scraped_at": "2026-03-01T10:00:00Z",
            "search_query": "gaming laptop",
            "page_number": 2,
        },
        "product": {
            "title": "  Legion Pro 5  ",
            "price": "50,000 EGP",
            "link": "https://www.amazon.eg/dp/B0TEST1234?tag=abc#section",
            "details_text": " Great thermals ",
            "seller_score": "4.7",
            "category": " Laptops ",
        },
    }

    # Act
    prepared = ingestion._validate_and_prepare(copy.deepcopy(record))

    # Assert
    assert prepared["metadata"]["source"] == "amazon"
    assert prepared["product"]["title"] == "Legion Pro 5"
    assert prepared["product"]["price"] == 50000.0
    assert prepared["product"]["link"] == "https://www.amazon.eg/dp/B0TEST1234"
    assert prepared["product"]["details_text"] == "Great thermals"
    assert prepared["product"]["seller_score"] == 4.7
    assert prepared["product"]["category"] == "Laptops"
    assert prepared["product"]["product_type"] == "gaming_laptop"
    assert calls == ["gaming laptop"]


def test_validate_and_prepare_rejects_invalid_records():
    # Arrange
    valid = {
        "metadata": {
            "source": "amazon",
            "scraped_at": "2026-03-01T10:00:00Z",
            "search_query": "gaming laptop",
            "page_number": 1,
        },
        "product": {
            "title": "Laptop",
            "price": 1000,
            "link": "https://example.com/p/1",
            "details_text": None,
            "seller_score": None,
            "category": None,
        },
    }

    missing_title = copy.deepcopy(valid)
    missing_title["product"]["title"] = ""

    invalid_datetime = copy.deepcopy(valid)
    invalid_datetime["metadata"]["scraped_at"] = "not-a-date"

    missing_link = copy.deepcopy(valid)
    missing_link["product"]["link"] = "   "

    # Act / Assert
    with pytest.raises(ValueError, match="product.title is required."):
        ingestion._validate_and_prepare(missing_title)

    with pytest.raises(ValueError, match="metadata.scraped_at must be a valid datetime."):
        ingestion._validate_and_prepare(invalid_datetime)

    with pytest.raises(ValueError, match="product.link is required."):
        ingestion._validate_and_prepare(missing_link)


def test_ingest_records_tracks_inserted_updated_and_failures(monkeypatch):
    # Arrange
    valid = {
        "metadata": {
            "source": "amazon",
            "scraped_at": "2026-03-01T10:00:00Z",
            "search_query": "laptop",
            "page_number": 1,
        },
        "product": {
            "title": "Laptop",
            "price": 1000,
            "link": "https://example.com/p/1",
        },
    }
    bad = {"metadata": {}, "product": {}}

    records = [valid, valid, bad, valid]

    def fake_upsert(_):
        fake_upsert.calls += 1
        if fake_upsert.calls == 1:
            return "inserted"
        if fake_upsert.calls == 2:
            return "updated"
        raise PyMongoError("db unavailable")

    fake_upsert.calls = 0

    monkeypatch.setattr(ingestion, "_upsert_record", fake_upsert)

    # Act
    summary = ingestion.ingest_records(records)

    # Assert
    assert summary["inserted"] == 1
    assert summary["updated"] == 1
    assert summary["failed"] == 2
    assert any(
        "is required" in msg and ("metadata.source" in msg or "product.title" in msg)
        for msg in summary["error_samples"]
    )
    assert any("db unavailable" in msg for msg in summary["error_samples"])
