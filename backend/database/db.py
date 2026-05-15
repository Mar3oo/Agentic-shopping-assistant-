"""MongoDB connection helpers with cached collections and required indexes."""

from typing import Optional

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.errors import OperationFailure

from .config import COLLECTION_NAME, DB_NAME, get_mongo_uri

_CLIENT: Optional[MongoClient] = None
_COLLECTION: Optional[Collection] = None
_PROFILE_COLLECTION: Optional[Collection] = None
_USERS_COLLECTION: Optional[Collection] = None
_SESSIONS_COLLECTION: Optional[Collection] = None
_MESSAGES_COLLECTION: Optional[Collection] = None
_CACHE_COLLECTION: Optional[Collection] = None
_FEEDBACK_COLLECTION: Optional[Collection] = None
_SEARCH_SESSIONS_COLLECTION: Optional[Collection] = None
_SEARCH_HISTORY_COLLECTION: Optional[Collection] = None
_INDEX_READY = False


def _create_client() -> MongoClient:
    return MongoClient(get_mongo_uri(), serverSelectionTimeoutMS=5000)


def _get_client() -> MongoClient:
    global _CLIENT

    if _CLIENT is None:
        _CLIENT = _create_client()

    return _CLIENT


def _has_unique_link_index(collection: Collection) -> bool:
    for index in collection.list_indexes():
        key_items = list(index.get("key", {}).items())
        if key_items == [("product.link", ASCENDING)] and index.get("unique", False):
            return True
    return False


def get_collection() -> Collection:
    global _COLLECTION, _INDEX_READY

    if _COLLECTION is None:
        _COLLECTION = _get_client()[DB_NAME][COLLECTION_NAME]

    if not _INDEX_READY:
        if not _has_unique_link_index(_COLLECTION):
            try:
                _COLLECTION.create_index([("product.link", ASCENDING)], unique=True)
            except OperationFailure as exc:
                if exc.code != 85:
                    raise
        _INDEX_READY = True

    return _COLLECTION


def get_profile_collection() -> Collection:
    global _PROFILE_COLLECTION

    if _PROFILE_COLLECTION is None:
        _PROFILE_COLLECTION = _get_client()[DB_NAME]["user_profiles"]

    return _PROFILE_COLLECTION


def get_users_collection() -> Collection:
    global _USERS_COLLECTION

    if _USERS_COLLECTION is None:
        _USERS_COLLECTION = _get_client()[DB_NAME]["users"]

    return _USERS_COLLECTION


def get_sessions_collection() -> Collection:
    global _SESSIONS_COLLECTION

    if _SESSIONS_COLLECTION is None:
        _SESSIONS_COLLECTION = _get_client()[DB_NAME]["sessions"]

    return _SESSIONS_COLLECTION


def get_messages_collection() -> Collection:
    global _MESSAGES_COLLECTION

    if _MESSAGES_COLLECTION is None:
        _MESSAGES_COLLECTION = _get_client()[DB_NAME]["messages"]

    return _MESSAGES_COLLECTION


def get_cache_collection() -> Collection:
    global _CACHE_COLLECTION

    if _CACHE_COLLECTION is None:
        _CACHE_COLLECTION = _get_client()[DB_NAME]["api_cache"]

    return _CACHE_COLLECTION


def get_feedback_collection() -> Collection:
    global _FEEDBACK_COLLECTION

    if _FEEDBACK_COLLECTION is None:
        _FEEDBACK_COLLECTION = _get_client()[DB_NAME]["user_feedback"]

    return _FEEDBACK_COLLECTION


def get_search_sessions_collection() -> Collection:
    global _SEARCH_SESSIONS_COLLECTION

    if _SEARCH_SESSIONS_COLLECTION is None:
        _SEARCH_SESSIONS_COLLECTION = _get_client()[DB_NAME]["search_sessions"]

    return _SEARCH_SESSIONS_COLLECTION


def get_search_history_collection() -> Collection:
    global _SEARCH_HISTORY_COLLECTION

    if _SEARCH_HISTORY_COLLECTION is None:
        _SEARCH_HISTORY_COLLECTION = _get_client()[DB_NAME]["search_history"]

    return _SEARCH_HISTORY_COLLECTION


def product_exists(link: str) -> bool:
    return get_collection().find_one({"product.link": link}, {"_id": 1}) is not None


def init_collections() -> None:
    profiles = get_profile_collection()
    profiles.create_index([("user_id", ASCENDING)], unique=True)

    users = get_users_collection()
    users.create_index([("user_id", ASCENDING)], unique=True)
    users.create_index(
        [("email", ASCENDING)],
        unique=True,
        partialFilterExpression={"email": {"$type": "string"}},
    )

    sessions = get_sessions_collection()
    sessions.create_index([("session_id", ASCENDING)], unique=True)
    sessions.create_index([("user_id", ASCENDING), ("updated_at", DESCENDING)])
    sessions.create_index(
        [("user_id", ASCENDING), ("agent_type", ASCENDING), ("status", ASCENDING)]
    )

    messages = get_messages_collection()
    messages.create_index([("session_id", ASCENDING), ("sequence", ASCENDING)], unique=True)
    messages.create_index([("session_id", ASCENDING), ("created_at", DESCENDING)])
    messages.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])

    cache = get_cache_collection()
    cache.create_index([("cache_key", ASCENDING)], unique=True)
    cache.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)

    search_sessions = get_search_sessions_collection()
    search_sessions.create_index([("user_id", ASCENDING)], unique=True)
    search_sessions.create_index([("updated_at", DESCENDING)])

    search_history = get_search_history_collection()
    search_history.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])


def close_client() -> None:
    global _CLIENT, _COLLECTION, _PROFILE_COLLECTION, _USERS_COLLECTION
    global _SESSIONS_COLLECTION, _MESSAGES_COLLECTION, _CACHE_COLLECTION
    global _FEEDBACK_COLLECTION, _SEARCH_SESSIONS_COLLECTION
    global _SEARCH_HISTORY_COLLECTION, _INDEX_READY

    if _CLIENT is not None:
        _CLIENT.close()

    _CLIENT = None
    _COLLECTION = None
    _PROFILE_COLLECTION = None
    _USERS_COLLECTION = None
    _SESSIONS_COLLECTION = None
    _MESSAGES_COLLECTION = None
    _CACHE_COLLECTION = None
    _FEEDBACK_COLLECTION = None
    _SEARCH_SESSIONS_COLLECTION = None
    _SEARCH_HISTORY_COLLECTION = None
    _INDEX_READY = False
