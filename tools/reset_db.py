import logging

from Data_base.db import (
    get_collection,
    get_profile_collection,
    get_feedback_collection,
)

logger = logging.getLogger(__name__)

logger.info("Clearing database...")

logger.info(f"Products deleted: {get_collection().delete_many({}).deleted_count}")
logger.info(
    f"Profiles deleted: {get_profile_collection().delete_many({}).deleted_count}"
)
logger.info(
    f"Feedback deleted: {get_feedback_collection().delete_many({}).deleted_count}"
)

logger.info("Database reset complete.")
