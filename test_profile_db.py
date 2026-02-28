from Data_Base.profile_repo import save_profile, get_profile
from agents.profile.schemas import UserProfile

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
