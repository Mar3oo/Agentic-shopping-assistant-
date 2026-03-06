from Data_base.db import (
    get_collection,
    get_profile_collection,
    get_feedback_collection,
)

print("Clearing database...")

print("Products deleted:", get_collection().delete_many({}).deleted_count)
print("Profiles deleted:", get_profile_collection().delete_many({}).deleted_count)
print("Feedback deleted:", get_feedback_collection().delete_many({}).deleted_count)

print("Database reset complete.")
