from datetime import datetime
from typing import Optional, Dict

from .db import get_profile_collection


def get_profile(user_id: str) -> Optional[Dict]:
    collection = get_profile_collection()
    doc = collection.find_one({"user_id": user_id})
    if doc:
        return doc.get("profile")
    return None


def save_profile(user_id: str, profile: Dict):
    collection = get_profile_collection()

    collection.update_one(
        {"user_id": user_id},
        {"$set": {"profile": profile, "updated_at": datetime.utcnow()}},
        upsert=True,
    )
