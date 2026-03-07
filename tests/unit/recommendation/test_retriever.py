from agents.recommendation import retriever as retriever_module


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.limit_value = None

    def limit(self, value):
        self.limit_value = value
        return self

    def __iter__(self):
        return iter(self.rows)


class FakeCollection:
    def __init__(self, rows):
        self.rows = rows
        self.find_calls = 0
        self.last_query = None
        self.last_projection = None
        self.last_cursor = None

    def find(self, query, projection):
        self.find_calls += 1
        self.last_query = query
        self.last_projection = projection
        self.last_cursor = FakeCursor(self.rows)
        return self.last_cursor


class FakeVectorIndex:
    def __init__(self):
        self.built_with = []
        self.links = []

    def build(self, product_type=None):
        self.built_with.append(product_type)

    def search(self, user_embedding, top_k=100):
        return self.links


def _build_retriever(monkeypatch, rows, links=None):
    fake_collection = FakeCollection(rows)

    monkeypatch.setattr(retriever_module, "get_collection", lambda: fake_collection)
    monkeypatch.setattr(retriever_module, "ProductVectorIndex", FakeVectorIndex)

    retriever = retriever_module.ProductRetriever()
    if links is not None:
        retriever.vector_index.links = links

    return retriever, fake_collection


def test_retriever_filters_by_product_type_and_price_range(monkeypatch):
    # Arrange
    rows = [{"product": {"link": "a"}}]
    retriever, fake_collection = _build_retriever(monkeypatch, rows)

    # Act
    results = retriever.retrieve_candidates(
        product_type="laptop",
        price_min=1000,
        price_max=5000,
        limit=25,
    )

    # Assert
    assert results == rows
    assert fake_collection.last_query == {
        "product.embedding": {"$exists": True},
        "product.product_type": "laptop",
        "product.price": {"$gte": 1000, "$lte": 5000},
    }
    assert fake_collection.last_cursor.limit_value == 25


def test_retriever_uses_cache_for_non_embedding_queries(monkeypatch):
    # Arrange
    rows = [{"product": {"link": "a"}}]
    retriever, fake_collection = _build_retriever(monkeypatch, rows)

    # Act
    first = retriever.retrieve_candidates(product_type="laptop")
    second = retriever.retrieve_candidates(product_type="laptop")

    # Assert
    assert first == second
    assert fake_collection.find_calls == 1


def test_retriever_applies_vector_link_filter_when_embedding_provided(monkeypatch):
    # Arrange
    rows = [{"product": {"link": "a"}}]
    retriever, fake_collection = _build_retriever(monkeypatch, rows, links=["a", "b"])

    # Act
    retriever.retrieve_candidates(
        product_type="earbuds",
        user_embedding=[0.1, 0.2, 0.3],
    )

    # Assert
    assert retriever.vector_index.built_with == ["earbuds"]
    assert fake_collection.last_query["product.link"] == {"$in": ["a", "b"]}


def test_retriever_skips_link_filter_when_vector_search_returns_empty(monkeypatch):
    # Arrange
    rows = [{"product": {"link": "a"}}]
    retriever, fake_collection = _build_retriever(monkeypatch, rows, links=[])

    # Act
    retriever.retrieve_candidates(user_embedding=[0.1, 0.2, 0.3])

    # Assert
    assert "product.link" not in fake_collection.last_query
    assert fake_collection.last_query["product.embedding"] == {"$exists": True}
