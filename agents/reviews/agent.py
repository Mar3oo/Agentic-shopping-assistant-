from youtube_service import search_youtube, get_transcripts_for_videos
from sentiment_analyzer import analyze_reviews
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()


class ReviewAgent:
    def __init__(self):
        self.product = None
        self.reviews_data = None

        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"

    def handle_message(self, user_input: str):

        if self._is_new_review(user_input):
            return self.start_review(user_input)

        if not self.product:
            return "Please specify a product to review."

        return self.answer_followup(user_input)

    def _is_new_review(self, text: str):
        text = text.lower()
        return "review" in text or "reviews" in text

    def start_review(self, user_input: str):

        product = self._parse_product(user_input)

        if not product:
            return "Please specify a product."

        self.product = product

        return self.run_review_pipeline()

    def _parse_product(self, text: str):
        text = text.lower()

        text = text.replace("reviews for", "")
        text = text.replace("review", "")
        text = text.replace("reviews", "")

        return text.strip()

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
