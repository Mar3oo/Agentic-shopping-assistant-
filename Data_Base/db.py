"""MongoDB connection helpers with a cached client and required indexes."""

from typing import Optional

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection

from .config import COLLECTION_NAME, DB_NAME, get_mongo_uri

_CLIENT: Optional[MongoClient] = None
_COLLECTION: Optional[Collection] = None
_INDEX_READY = False


def _create_client() -> MongoClient:
    """Create a MongoClient using the local configured URI."""
    return MongoClient(get_mongo_uri(), serverSelectionTimeoutMS=5000)


def get_collection() -> Collection:
    """Return the target collection and ensure a unique index on product.link."""
    global _CLIENT, _COLLECTION, _INDEX_READY

    if _CLIENT is None:
        _CLIENT = _create_client()

    if _COLLECTION is None:
        _COLLECTION = _CLIENT[DB_NAME][COLLECTION_NAME]

    if not _INDEX_READY:
        _COLLECTION.create_index(
            [("product.link", ASCENDING)],
            unique=True,
            name="uniq_product_link",
        )
        _INDEX_READY = True

    return _COLLECTION


def close_client() -> None:
    """Close and reset cached MongoDB client state."""
    global _CLIENT, _COLLECTION, _INDEX_READY

    if _CLIENT is not None:
        _CLIENT.close()

    _CLIENT = None
    _COLLECTION = None
    _INDEX_READY = False
