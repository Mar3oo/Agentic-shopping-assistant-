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


def _to_float_or_none(value):
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def adapt_profile(profile: dict) -> dict:
    """
    Convert ProfileAgent schema -> Recommendation schema.
    Also accepts an already-adapted recommendation profile.
    """
    if not profile:
        return {}
    
    category = profile.get("product_category", profile.get("category"))
    use_case = profile.get("product_intent", profile.get("use_case"))

    if profile.get("budget_min") is not None or profile.get("budget_max") is not None:
        budget_min = _to_float_or_none(profile.get("budget_min"))
        budget_max = _to_float_or_none(profile.get("budget_max"))
    else:
        budget_min, budget_max = parse_budget(profile.get("budget"))

    return {
        "category": category,
        "use_case": use_case,
        "budget_min": budget_min,
        "budget_max": budget_max,
        "preferences": profile.get("preferences") or {},
        "search_queries": profile.get("search_queries") or [],
        "country": profile.get("country"),
    }
