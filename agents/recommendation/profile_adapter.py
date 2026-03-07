import re


def parse_budget(budget_text):
    """
    Convert budget text to min/max numbers.
    Example:
    "5000-8000 EGP" -> (5000, 8000)
    "under 7000" -> (None, 7000)
    """

    if not budget_text:
        return None, None

    numbers = re.findall(r"\d+", budget_text)

    if len(numbers) == 2:
        return float(numbers[0]), float(numbers[1])

    if len(numbers) == 1:
        return None, float(numbers[0])

    return None, None


def adapt_profile(profile: dict) -> dict:
    """
    Convert ProfileAgent schema → Recommendation schema
    """

    budget_min, budget_max = parse_budget(profile.get("budget"))

    return {
        "category": profile.get("product_category"),
        "use_case": profile.get("product_intent"),
        "budget_min": budget_min,
        "budget_max": budget_max,
        "preferences": profile.get("preferences", {}),
        "search_queries": profile.get("search_queries", []),
        "country": profile.get("country"),
    }