from Data_base import product_cache


class FakeCollection:
    def __init__(self, count):
        self.count = count
        self.query = None

    def count_documents(self, query):
        self.query = query
        return self.count


def test_has_enough_products_applies_type_and_price_filters(monkeypatch):
    # Arrange
    fake_collection = FakeCollection(count=35)
    monkeypatch.setattr(product_cache, "get_collection", lambda: fake_collection)

    # Act
    enough = product_cache.has_enough_products(
        product_type="laptop",
        price_min=1000,
        price_max=5000,
        min_count=30,
    )

    # Assert
    assert enough is True
    assert fake_collection.query == {
        "product.embedding": {"$exists": True},
        "product.product_type": "laptop",
        "product.price": {"$gte": 1000, "$lte": 5000},
    }


def test_has_enough_products_returns_false_when_count_below_threshold(monkeypatch):
    # Arrange
    fake_collection = FakeCollection(count=5)
    monkeypatch.setattr(product_cache, "get_collection", lambda: fake_collection)

    # Act
    enough = product_cache.has_enough_products(product_type="earbuds", min_count=10)

    # Assert
    assert enough is False
    assert fake_collection.query["product.product_type"] == "earbuds"
