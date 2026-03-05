from datetime import datetime
from .db import get_feedback_collection


def save_feedback(user_id, product_link, liked=True):
    collection = get_feedback_collection()

    collection.insert_one(
        {
            "user_id": user_id,
            "product_link": product_link,
            "liked": liked,
            "timestamp": datetime.utcnow(),
        }
    )


def get_user_feedback(user_id):
    collection = get_feedback_collection()

    return list(collection.find({"user_id": user_id}, {"_id": 0}))
