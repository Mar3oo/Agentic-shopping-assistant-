from agents.reviews.youtube_service import search_youtube, get_transcripts_for_videos
from agents.reviews.sentiment_analyzer import analyze_reviews
from agents.shared.product_name_extractor import extract_clean_product_name
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()


class ReviewAgent:
    def __init__(self):
        self.product = None
        self.query = None
        self.sources = []
        self.reviews_data = None

        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"

    def to_state(self) -> dict:
        return {
            "product": self.product,
            "query": self.query,
            "sources": self.sources,
            "reviews_data": self.reviews_data,
        }

    @classmethod
    def from_state(cls, state: dict | None):
        agent = cls()
        state = state or {}
        agent.product = state.get("product")
        agent.query = state.get("query")
        agent.sources = state.get("sources") or []
        agent.reviews_data = state.get("reviews_data")
        return agent

    def handle_message(self, user_input: str):
        normalized = " ".join(user_input.lower().strip().split())

        if normalized == "new_review":
            self.product = None
            self.query = None
            self.sources = []
            self.reviews_data = None
            return "Ready for a new review search. Please enter a product."

        if self._is_new_review(user_input):
            return self.start_review(user_input)

        if not self.product:
            return "Please specify a product to review."

        return self.answer_followup(user_input)

    def _is_new_review(self, text: str):
        normalized = " ".join(text.lower().strip().split())
        return (
            normalized.startswith("review ")
            or normalized.startswith("reviews for ")
            or normalized.startswith("review of ")
            or normalized.startswith("show reviews for ")
            or normalized.startswith("get reviews for ")
            or normalized.startswith("find reviews for ")
            or normalized.endswith(" review")
            or normalized.endswith(" reviews")
        )

    def start_review(self, user_input: str):

        product = self._parse_product(user_input)

        if not product:
            return "Please specify a product."

        self.product = extract_clean_product_name(product)

        return self.run_review_pipeline()

    def _parse_product(self, text: str):
        normalized = " ".join((text or "").strip().split())
        lowered = normalized.lower()
        prefixes = (
            "reviews for ",
            "review of ",
            "show reviews for ",
            "get reviews for ",
            "find reviews for ",
            "review ",
        )

        for prefix in prefixes:
            if lowered.startswith(prefix):
                normalized = normalized[len(prefix) :]
                break

        lowered = normalized.lower()
        if lowered.endswith(" reviews"):
            normalized = normalized[: -len(" reviews")]
        elif lowered.endswith(" review"):
            normalized = normalized[: -len(" review")]

        return normalized.strip(" .,!?")

    def run_review_pipeline(self):
        """
        Full pipeline:
        search → transcripts → sentiment → store
        """

        query = f"{self.product} honest review"

        videos = search_youtube(query)

        video_ids = [v["video_id"] for v in videos]

        transcripts = get_transcripts_for_videos(video_ids[:3])

        if not transcripts:
            return "Could not fetch reviews."

        result = analyze_reviews(self.product, transcripts)

        # attach YouTube sources
        sources = [
            {
                "title": v["title"],
                "url": v["link"],
                "thumbnail": f"https://img.youtube.com/vi/{v['video_id']}/hqdefault.jpg",
            }
            for v in videos[:3]
        ]

        # merge into result
        if isinstance(result, dict):
            result["sources"] = sources

        # store
        self.query = query
        self.sources = sources
        self.reviews_data = result

        return result

    def answer_followup(self, user_input: str):

        if not self.reviews_data:
            return "No review data available."

        prompt = f"""
You are answering a follow-up question about a product.

Product: {self.product}

Existing review summary:
----------------
{self.reviews_data}
----------------

User question:
{user_input}

Answer briefly and do NOT repeat the full review.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        return response.choices[0].message.content.strip()
