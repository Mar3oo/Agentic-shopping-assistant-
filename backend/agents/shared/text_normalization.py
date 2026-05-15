import re


ARABIC_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670]")


def normalize_arabic(text: str) -> str:
    """
    Normalize Arabic text for better retrieval/search matching.
    """

    if not text:
        return ""

    text = text.strip().lower()

    # Remove Arabic diacritics
    text = re.sub(ARABIC_DIACRITICS, "", text)

    # Normalize Arabic letters
    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ى": "ي",
        "ة": "ه",
        "ؤ": "و",
        "ئ": "ي",
    }

    for src, target in replacements.items():
        text = text.replace(src, target)

    # Remove tatweel
    text = text.replace("ـ", "")

    # Remove extra punctuation
    text = re.sub(r"[^\w\s]", " ", text)

    # Normalize spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_text(text: str) -> str:
    """
    General multilingual normalization.
    """

    if not text:
        return ""

    text = normalize_arabic(text)

    return text.lower().strip()
