import re


def parse_budget(budget_text):
    if not budget_text:
        return None, None

    text = budget_text.lower().strip()

    # handle "k"
    text = text.replace("k", "000")

    numbers = re.findall(r"\d+", text)

    if not numbers:
        return None, None

    numbers = [float(n) for n in numbers]

    if len(numbers) == 2:
        return numbers[0], numbers[1]

    if len(numbers) == 1:
        return None, numbers[0]

    return None, None


def _to_float_or_none(value):
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_text(value):
    if value is None:
        return None
    return str(value).strip()


def adapt_profile(profile: dict) -> dict:
    """
    Convert ProfileAgent schema → Recommendation schema.
    Also accepts already-adapted profiles.
    """

    if not profile:
        return {}

    # -------------------------
    # Normalize core fields
    # -------------------------
    category = _clean_text(profile.get("product_category", profile.get("category")))

    use_case = _clean_text(profile.get("product_intent", profile.get("use_case")))

    # -------------------------
    # Budget handling
    # -------------------------
    if profile.get("budget_min") is not None or profile.get("budget_max") is not None:
        budget_min = _to_float_or_none(profile.get("budget_min"))
        budget_max = _to_float_or_none(profile.get("budget_max"))
    else:
        budget_min, budget_max = parse_budget(profile.get("budget"))

    # -------------------------
    # Final normalized profile
    # -------------------------
    return {
        "category": category,
        "use_case": use_case,
        "budget_min": budget_min,
        "budget_max": budget_max,
        # user context
        "user_type": _clean_text(profile.get("user_type")),
        "target_user": _clean_text(profile.get("target_user")),
        "usage_intensity": _clean_text(profile.get("usage_intensity")),
        # preferences
        "priorities": profile.get("priorities") or {},
        "must_have_features": profile.get("must_have_features") or [],
        "nice_to_have_features": profile.get("nice_to_have_features") or [],
        "preferences": profile.get("preferences") or {},
        # retrieval signals
        "search_queries": profile.get("search_queries") or [],
        #  original user input (future use)
        "original_query": profile.get("original_query"),
    }
