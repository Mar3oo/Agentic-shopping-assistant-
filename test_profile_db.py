from Data_base.profile_repo import save_profile, get_profile
# removed unused import to avoid requiring pydantic in this simple test

user_id = "user_001"

profile_data = {
    "product_category": "laptop",
    "product_intent": "programming",
    "budget": "800-1000",
    "country": "Egypt",
    "preferences": {},
    "search_queries": [],
}

save_profile(user_id, profile_data)

loaded = get_profile(user_id)

print("Loaded:", loaded)
