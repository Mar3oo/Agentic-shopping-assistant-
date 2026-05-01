from groq import Groq
import os
from dotenv import load_dotenv
from tavily import TavilyClient
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import json
from agents.shared.product_name_extractor import extract_clean_product_mappings

# Load environment variables
load_dotenv()

# Get API key
groq_api_key = os.getenv("GROQ_API_KEY")
tavily_api_key = os.getenv("TAVILY_API_KEY")


class ComparisonAgent:
    def __init__(self):
        self.products = []
        self.product_pairs = []
        self.comparison_active = False

        self.search_queries = []
        self.source_urls = []
        self.raw_contents = None
        self.comparison_result = None

        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.tavily = TavilyClient(api_key=tavily_api_key)
        self.model = "llama-3.3-70b-versatile"

    def to_state(self) -> dict:
        return {
            "products": self.products,
            "product_pairs": self.product_pairs,
            "comparison_active": self.comparison_active,
            "search_queries": self.search_queries,
            "source_urls": self.source_urls,
            "raw_contents": self.raw_contents or [],
            "comparison_result": self.comparison_result,
        }

    @classmethod
    def from_state(cls, state: dict | None):
        agent = cls()
        state = state or {}
        agent.products = state.get("products") or []
        agent.product_pairs = state.get("product_pairs") or []
        agent.comparison_active = state.get("comparison_active", bool(agent.products))
        agent.search_queries = state.get("search_queries") or []
        agent.source_urls = state.get("source_urls") or []
        agent.raw_contents = state.get("raw_contents") or []
        agent.comparison_result = state.get("comparison_result")
        return agent

    def _is_new_comparison(self, text: str):
        text = text.lower().strip()

        return text == "new_comparison" or len(self._parse_products(text)) >= 2

    def handle_message(self, user_input: str):

        # 🔥 force new session
        if user_input.lower().strip() == "new_comparison":
            self.comparison_active = False
            self.products = []
            self.product_pairs = []
            self.search_queries = []
            self.source_urls = []
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

        raw_products = self._parse_products(user_input)

        if len(raw_products) < 2:
            return "Please provide at least two products to compare."

        product_pairs = extract_clean_product_mappings(raw_products)
        product_pairs = self._select_products_for_comparison(product_pairs)
        if len(product_pairs) < 2:
            return "Please provide at least two distinct products to compare."

        self.product_pairs = product_pairs
        self.products = [pair["product_clean"] for pair in product_pairs]
        self.comparison_active = True

        # reset old state
        self.search_queries = []
        self.source_urls = []
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

        combined_text = "\n\n".join(self.raw_contents or [])
        combined_text = combined_text[:6000]

        prompt = f"""
You are a structured product comparison assistant.

Products:
{", ".join(self.products)}

Normalized product names:
{self._product_prompt_block()}

Context:
----------------
{combined_text}
----------------

Existing comparison:
----------------
{self.comparison_result}
----------------

User question:
{user_input}

Return ONLY a valid JSON.

FORMAT:

{{
  "type": "feature_answer",
  "feature": "battery / performance / camera / etc",
  "comparison": {{
    "product_1": "...",
    "product_2": "..."
  }},
  "summary": "clear answer + short explanation"
}}

RULES:
- No markdown
- No extra text
- Keep answer concise
- Focus ONLY on what user asked
- Normalize product names before answering
- Use clean product names instead of long raw titles
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        raw = response.choices[0].message.content.strip()
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            cleaned = raw[start:end]

            result = json.loads(cleaned)
            if isinstance(result, dict):
                result.setdefault("products", self.product_pairs)
            return result
        except Exception:
            return {
                "type": "feature_answer",
                "feature": "unknown",
                "comparison": {},
                "summary": "Could not process the answer properly",
                "products": self.product_pairs,
            }

    def _parse_products(self, text: str):
        """
        Parse comparison requests while preserving the original product titles.
        """
        normalized = " ".join((text or "").strip().split())
        lowered = normalized.lower()

        if " versus " in lowered:
            parts = self._split_case_preserving(normalized, " versus ")
        elif " vs " in lowered:
            parts = self._split_case_preserving(normalized, " vs ")
        elif lowered.startswith("difference between "):
            remainder = normalized[len("difference between ") :]
            parts = self._split_case_preserving(remainder, " and ")
        elif lowered.startswith("compare "):
            remainder = normalized[len("compare ") :]
            parts = self._split_case_preserving(remainder, " and ")
        else:
            parts = []

        return [p.strip(" ,.?") for p in parts if p.strip(" ,.?")]

    @staticmethod
    def _split_case_preserving(text: str, separator: str) -> list[str]:
        lowered = text.lower()
        parts = []
        start = 0

        while True:
            index = lowered.find(separator, start)
            if index == -1:
                parts.append(text[start:])
                break

            parts.append(text[start:index])
            start = index + len(separator)

        return parts

    def _select_products_for_comparison(
        self,
        product_pairs: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        # Recommendation flows already provide ranked products, so the first
        # distinct two products are the safest pair to compare.
        selected_pairs = []
        seen = set()

        for pair in product_pairs:
            clean_name = str(pair.get("product_clean") or "").strip()
            full_title = str(pair.get("product_full") or "").strip()
            if not clean_name or not full_title:
                continue

            key = clean_name.lower()
            if key in seen:
                continue

            seen.add(key)
            selected_pairs.append(
                {
                    "product_clean": clean_name,
                    "product_full": full_title,
                }
            )

            if len(selected_pairs) == 2:
                break

        return selected_pairs

    def _product_prompt_block(self) -> str:
        if not self.product_pairs:
            return "\n".join(f"- {product}" for product in self.products)

        return "\n".join(
            f"- Clean name: {pair['product_clean']} | Original title: {pair['product_full']}"
            for pair in self.product_pairs
        )

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
You are a professional product comparison system.

Products:
{", ".join(self.products)}

Normalized product names:
{self._product_prompt_block()}

Data:
----------------
{combined_text}
----------------

Return ONLY a valid JSON object.

FORMAT:

{{
  "summary": "3-4 lines giving a quick overall comparison",
  "products": [
    {{
      "product_clean": "...",
      "product_full": "..."
    }}
  ],
  "comparison_table": [
    {{
      "feature": "...",
      "product_1": "...",
      "product_2": "..."
    }}
  ],
  "key_differences": [
    "...",
    "..."
  ],
  "recommendation": {{
    "product_1": [
      "...",
      "..."
    ],
    "product_2": [
      "...",
      "..."
    ]
  }}
}}

RULES:
- No markdown
- No extra text
- Keep summary concise but useful
- Max 6 comparison rows
- Normalize product names before comparison
- Use clean product names in the summary, table, and reasoning
- Avoid repeating long raw titles unless absolutely necessary
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        raw = response.choices[0].message.content.strip()
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            cleaned = raw[start:end]

            result = json.loads(cleaned)
            if isinstance(result, dict):
                result.setdefault("products", self.product_pairs)
            return result
        except Exception:
            return {
                "summary": "Could not generate summary",
                "products": self.product_pairs,
                "comparison_table": [],
                "key_differences": ["Failed to parse comparison"],
                "recommendation": {},
            }

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

        # attach sources
        sources = [{"url": link} for link in links]

        # store
        self.search_queries = queries
        self.source_urls = links
        self.raw_contents = contents
        self.comparison_result = result

        # merge sources into result
        if isinstance(result, dict):
            result.setdefault("products", self.product_pairs)
            result["sources"] = sources

        return result
