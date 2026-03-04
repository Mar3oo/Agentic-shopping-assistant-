import os
from agents.recommendation.intent_router import RecommendationIntentRouter
from dotenv import load_dotenv

load_dotenv()

router = RecommendationIntentRouter(api_key=os.getenv("GROQ_API_KEY"))

dummy_recs = [
    {"title": "Dell Gaming Laptop", "price": 60000},
    {"title": "Lenovo LOQ RTX 4050", "price": 52000},
]

user_message = "I don't want Dell and my budget is 20000 to 30000"

result = router.route(user_message, dummy_recs)

print(result)
