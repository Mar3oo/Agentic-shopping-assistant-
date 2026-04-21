from groq import Groq
import os
from dotenv import load_dotenv
from tavily import TavilyClient
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# Load environment variables
load_dotenv()

# Get API key
groq_api_key = os.getenv("GROQ_API_KEY")
tavily_api_key = os.getenv("TAVILY_API_KEY")


class ComparisonAgent:
    def __init__(self):
        self.products = []
        self.comparison_active = False

        self.raw_contents = None
        self.comparison_result = None

        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.tavily = TavilyClient(api_key=tavily_api_key)
        self.model = "llama-3.3-70b-versatile"

    def _is_new_comparison(self, text: str):
        text = text.lower().strip()

        return (
            text == "new_comparison"
            or "compare" in text
            or "vs" in text
            or "difference between" in text
        )

    def handle_message(self, user_input: str):

        # 🔥 force new session
        if user_input.lower().strip() == "new_comparison":
            self.comparison_active = False
            self.products = []
            self.raw_contents = None
            self.comparison_result = None
            return "Ready for a new comparison. Please enter products."

        # detect new comparison
        if self._is_new_comparison(user_input):
            return self.start_comparison(user_input)

        # no active session
        if not self.comparison_active:
            return "Please start a comparison first."

        # follow-up
        return self.answer_followup(user_input)

    def start_comparison(self, user_input: str):

        products = self._parse_products(user_input)

        if len(products) < 2:
            return "Please provide at least two products to compare."

        self.products = products
        self.comparison_active = True

        # reset old state
        self.raw_contents = None
        self.comparison_result = None

        # 🔥 run full pipeline automatically
        return self.run_comparison_pipeline()

    def answer_followup(self, user_input: str):
        """
        Use LLM to answer follow-up questions based on stored products.
        """

        if not self.products:
            return "No active comparison. Please start first."

        combined_text = "\n\n".join(self.raw_contents)
        combined_text = combined_text[:6000]

        prompt = f"""
                    You are a product comparison expert.

                    The user is comparing these products:
                    {", ".join(self.products)}
                    
                    Context data:
                    ----------------
                    {combined_text}
                    ----------------
                    
                    Existing comparison:
                    ----------------
                    {self.comparison_result}
                    ----------------
                    
                    User question:
                    {user_input}

                    Instructions:
                    - Answer ONLY based on these products
                    - Be clear and helpful
                    - If it's a comparison question, compare directly
                    - If it's about one feature (camera, battery, etc), focus on that
                    - Keep answer concise but informative
                    """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        return response.choices[0].message.content.strip()

    def _parse_products(self, text: str):
        """
        TEMPORARY: Simple rule-based parsing.
        """
        text = text.lower()

        if "vs" in text:
            parts = text.split("vs")
        elif "compare" in text:
            parts = text.replace("compare", "").split("and")
        else:
            parts = []

        return [p.strip() for p in parts if p.strip()]

    def generate_search_queries(self):
        """
        Generate a single comparison query
        """

        if len(self.products) < 2:
            return []

        p1, p2 = self.products[0], self.products[1]

        return [f"{p1} vs {p2} comparison"]

    def search_tavily(self, query: str):
        """
        Search using Tavily API
        """

        try:
            response = self.tavily.search(
                query=query,
                search_depth="basic",  # later: advanced
                max_results=5,
            )

            results = response.get("results", [])

            links = [r["url"] for r in results if "url" in r]

            return links

        except Exception as e:
            print("Tavily error:", e)
            return []

    def search_all_queries(self, queries: list):
        all_links = []

        for q in queries:
            links = self.search_tavily(q)
            all_links.extend(links)

        return list(set(all_links))

    def fetch_with_playwright(self, url: str):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                page.goto(url, timeout=60000)

                # 🔥 مهم: استنى لحد ما الصفحة تخلص loading
                page.wait_for_load_state("networkidle")

                # 🔥 حاول تستنى عنصر حقيقي من الصفحة
                # nanoreview فيه table comparison
                try:
                    page.wait_for_selector("table", timeout=10000)
                except:
                    pass  # لو مش موجود نكمل عادي

                content = page.content()

                browser.close()

                return content

        except Exception as e:
            print("Playwright error:", e)
            return None

    def fetch_and_clean(self, url: str):
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            # ---------- First try: requests ----------
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                html = response.text
            else:
                html = None

            # ---------- If failed or weak → use Playwright ----------
            if not html or len(html) < 2000:
                print(f"[Fallback] Using Playwright for {url}")
                html = self.fetch_with_playwright(url)

            if not html:
                return None

            soup = BeautifulSoup(html, "html.parser")

            # remove noise
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()

            text = soup.get_text(separator=" ", strip=True)

            # لو النص قليل → useless
            if len(text) < 500:
                return None

            return text[:8000]

        except Exception as e:
            print("Fetch error:", e)
            return None

    def fetch_all_links(self, links: list):
        """
        Fetch and clean multiple links
        """

        contents = []

        for link in links[:3]:  # 🔥 خليك في أول 3 بس
            text = self.fetch_and_clean(link)

            if text:
                contents.append(text)

        return contents

    def generate_comparison(self, contents: list):
        """
        Use LLM to generate comparison from scraped content
        """

        if not contents:
            return "No data available for comparison."

        # 🔥 نجمع كل المحتوى
        combined_text = "\n\n".join(contents)

        # ✂️ safety limit (مهم جدًا)
        combined_text = combined_text[:6000]

        prompt = f"""
                You are a professional product comparison expert.

                Products:
                {", ".join(self.products)}

                Below is extracted data from multiple websites:
                ----------------
                {combined_text}
                ----------------

                Your task:

                1) Identify the MOST IMPORTANT comparison factors for these products.
                - Choose relevant factors dynamically (e.g., performance, size, usability, features, durability, etc.)
                - Do NOT assume fixed categories

                2) Create a comparison table using ONLY the relevant factors.

                3) Highlight key differences (max 5 points)

                4) Give a final recommendation:
                - Who should choose Product 1 (max 3 points)
                - Who should choose Product 2 (max 3 points)

                Rules:
                - Adapt to the product type (phones, laptops, books, anything)
                - Do NOT use fixed categories like camera or battery unless relevant
                - Be concise and structured
                - Do NOT repeat yourself
                - Use ONLY the provided data
                """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        return response.choices[0].message.content.strip()

    def filter_links(self, links: list):
        """
        Remove unwanted links like YouTube and problematic domains
        """

        blocked = ["youtube.com", "youtu.be"]

        filtered = []

        for link in links:
            if any(domain in link for domain in blocked):
                continue
            filtered.append(link)

        return filtered[:2]

    def run_comparison_pipeline(self):
        """
        Full pipeline:
        search → fetch → compare → store results
        """

        queries = self.generate_search_queries()

        links = self.search_all_queries(queries)
        links = self.filter_links(links)

        contents = self.fetch_all_links(links)

        result = self.generate_comparison(contents)

        # 🔥 STORE HERE (correct place)
        self.raw_contents = contents
        self.comparison_result = result

        return result
