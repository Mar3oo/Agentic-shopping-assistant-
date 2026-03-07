from selenium.common.exceptions import TimeoutException

from scrapers import amazon
from scrapers.base import load_url_with_retry


class FakeDriver:
    def __init__(self, failures_before_success=1):
        self.failures_before_success = failures_before_success
        self.calls = 0

    def get(self, _url):
        self.calls += 1
        if self.calls <= self.failures_before_success:
            raise TimeoutException("temporary timeout")


def test_amazon_normalize_product_handles_malformed_price_and_link():
    # Arrange
    product = {
        "title": "  Test   Product  ",
        "price": "EGP 1,999.50",
        "link": "https://www.amazon.eg/product-name/dp/B0ABC12345?ref=abc#anchor",
        "seller_score": "4.5 out of 5",
        "details_text": "  Good    value ",
        "category": " Electronics  ",
    }

    # Act
    normalized = amazon.normalize_product(product)

    # Assert
    assert normalized["link"] == "https://www.amazon.eg/dp/B0ABC12345"
    assert normalized["price"] == 1999.5
    assert normalized["seller_score"] == 0.9
    assert normalized["title"] == "Test Product"
    assert normalized["details_text"] == "Good value"
    assert normalized["category"] == "Electronics"


def test_load_url_with_retry_retries_then_succeeds(monkeypatch):
    # Arrange
    driver = FakeDriver(failures_before_success=2)
    wait = object()
    condition_calls = {"count": 0}

    def wait_condition(_):
        condition_calls["count"] += 1

    monkeypatch.setattr("scrapers.base.time.sleep", lambda *_: None)

    # Act
    load_url_with_retry(
        driver,
        wait,
        "https://example.com",
        wait_condition,
        max_attempts=3,
        min_delay=0,
        max_delay=0,
    )

    # Assert
    assert driver.calls == 3
    assert condition_calls["count"] == 1
