from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv
import re
from groq import Groq

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")

youtube = build("youtube", "v3", developerKey=API_KEY)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

# # Known product brands (helps detect model names)
# KNOWN_BRANDS = [
#     "apple",
#     "samsung",
#     "sony",
#     "dell",
#     "hp",
#     "lenovo",
#     "asus",
#     "acer",
#     "msi",
#     "razer",
#     "logitech",
#     "corsair",
#     "steelseries",
#     "xiaomi",
#     "huawei",
#     "google",
#     "oneplus",
#     "anker",
#     "bose",
#     "jbl",
# ]

SPEC_PATTERNS = [
    r"\b\d+gb\b",
    r"\b\d+tb\b",
    r"\b\d+[- ]?inch\b",
    r"\bssd\b",
    r"\bram\b",
    r"\bcpu\b",
    r"\bgpu\b",
    r"\bdisplay\b",
    r"\bkeyboard\b",
    r"\bversion\b",
    r"\bcolor\b",
    r"\bblack\b|\bwhite\b|\bsilver\b|\bblue\b|\bred\b",
]


def rule_based_product_name(title: str):
    """
    Fast heuristic cleaner.
    """
    if not title:
        return ""

    text = title.lower()

    # remove separators
    text = re.split(r"[|]", text)[0]

    # remove specs
    for p in SPEC_PATTERNS:
        text = re.sub(p, "", text)

    tokens = text.split()

    if len(tokens) <= 4:
        return " ".join(tokens).title(), True

    cleaned = " ".join(tokens[:4])

    return cleaned.title(), False


def llm_extract_product_name(title: str):
    """
    Use LLM to extract clean product name.
    """

    prompt = f"""
Extract the core product name from this e-commerce title.

Rules:
- Keep brand + model
- Remove specs, storage, color, marketing text
- Return ONLY the product name

Example:
Input:
Apple MacBook Air MRXQ3 | 13 Inch Display | Apple M3 Chip | 8GB RAM

Output:
Apple MacBook Air MRXQ3

Title:
{title}
"""

    response = groq_client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0
    )

    return response.choices[0].message.content.strip()


def extract_product_name(title: str):
    """
    Hybrid extractor:
    1) Try rule-based
    2) If low confidence → use LLM
    """

    rule_name, confident = rule_based_product_name(title)

    if confident:
        return rule_name

    try:
        return llm_extract_product_name(title)
    except Exception:
        return rule_name


def search_youtube(query, max_results=5):
    request = youtube.search().list(
        q=query, part="snippet", type="video", maxResults=max_results
    )

    response = request.execute()

    videos = []

    for item in response["items"]:
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        link = f"https://www.youtube.com/watch?v={video_id}"

        videos.append({"title": title, "video_id": video_id, "link": link})

    return videos


def get_transcripts_for_videos(video_ids):
    api = YouTubeTranscriptApi()
    transcripts = []

    for vid in video_ids:
        try:
            transcript = api.fetch(vid, languages=["en"])
            text = " ".join([item.text for item in transcript])
            transcripts.append(text)

        except Exception:
            continue

    return transcripts
