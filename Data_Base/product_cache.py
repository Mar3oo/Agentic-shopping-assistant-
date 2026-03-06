from Data_base.db import get_collection


def has_enough_products(
    product_type: str,
    price_min: float | None = None,
    price_max: float | None = None,
    min_count: int = 30,
) -> bool:
    """
    Check if database already has enough products
    for a given product type and optional price range.

    If count >= min_count → skip scraping.
    """

    collection = get_collection()

    query = {"product.embedding": {"$exists": True}}

    # filter by product type
    if product_type:
        query["product.product_type"] = product_type

    # filter by price
    if price_min is not None or price_max is not None:
        query["product.price"] = {}

        if price_min is not None:
            query["product.price"]["$gte"] = price_min

        if price_max is not None:
            query["product.price"]["$lte"] = price_max

    count = collection.count_documents(query)

    print(f"[CACHE CHECK] Found {count} products for type={product_type}")

    return count >= min_count
