import os


APP_TITLE = "AI Shopping Assistant"
BACKEND_BASE_URL = os.getenv(
    "SHOPPING_ASSISTANT_BACKEND_URL",
    "http://127.0.0.1:8000",
).rstrip("/")
REQUEST_TIMEOUT_SECONDS = int(os.getenv("SHOPPING_ASSISTANT_TIMEOUT_SECONDS", "120"))

AUTH_PAGE = "pages/auth.py"
RECOMMENDATION_PAGE = "pages/recommendation.py"
COMPARISON_PAGE = "pages/comparison.py"
REVIEW_PAGE = "pages/review.py"
SEARCH_PAGE = "pages/search.py"
