from datetime import datetime
import uuid

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from Data_Base.db import get_users_collection


def _guest_document(user_id: str) -> dict:
    now = datetime.utcnow()
    return {
        "user_id": user_id,
        "mode": "guest",
        "email": None,
        "password_hash": None,
        "display_name": None,
        "created_at": now,
        "last_seen_at": now,
        "is_active": True,
    }


def _registered_document(
    user_id: str,
    email: str,
    password_hash: str,
    display_name: str | None = None,
) -> dict:
    now = datetime.utcnow()
    return {
        "user_id": user_id,
        "mode": "registered",
        "email": email,
        "password_hash": password_hash,
        "display_name": (display_name or "").strip() or None,
        "created_at": now,
        "last_seen_at": now,
        "is_active": True,
    }


def create_guest_user() -> dict:
    collection = get_users_collection()
    user = _guest_document(f"user_{uuid.uuid4().hex[:8]}")
    collection.insert_one(user)
    return user


def get_user(user_id: str) -> dict | None:
    return get_users_collection().find_one({"user_id": user_id}, {"_id": 0})


def get_user_by_email(email: str) -> dict | None:
    return get_users_collection().find_one({"email": email}, {"_id": 0})


def create_registered_user(
    email: str,
    password_hash: str,
    display_name: str | None = None,
) -> dict:
    collection = get_users_collection()
    user = _registered_document(
        user_id=f"user_{uuid.uuid4().hex[:8]}",
        email=email,
        password_hash=password_hash,
        display_name=display_name,
    )

    try:
        collection.insert_one(user)
    except DuplicateKeyError:
        raise

    return user


def update_last_seen(user_id: str) -> dict | None:
    return get_users_collection().find_one_and_update(
        {"user_id": user_id},
        {"$set": {"last_seen_at": datetime.utcnow()}},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )


def upsert_guest_user(user_id: str) -> dict:
    collection = get_users_collection()
    existing = collection.find_one({"user_id": user_id}, {"_id": 0})

    if existing:
        return update_last_seen(user_id) or existing

    user = _guest_document(user_id)
    collection.insert_one(user)
    return user
