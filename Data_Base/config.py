"""Runtime configuration for MongoDB-backed raw product ingestion."""

import os

from dotenv import load_dotenv

load_dotenv()

DB_NAME = "graduation_project_db"
COLLECTION_NAME = "products_raw"
MONGO_URI_CLOUD = os.getenv("MONGO_URI_CLOUD", "").strip()


def get_mongo_uri() -> str:
    """Return the configured MongoDB URI or raise a clear configuration error."""
    if not MONGO_URI_CLOUD:
        raise ValueError("Missing MONGO_URI_CLOUD in environment variables.")
    return MONGO_URI_CLOUD
