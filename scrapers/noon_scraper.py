import json
import random
import re
import time
from datetime import datetime
from html import unescape
from urllib.parse import quote_plus, urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright


class NoonScraper:
    PRODUCT_CONTAINER_SELECTORS = [
        "[data-qa='product']",
        ".productContainer",
        "div[class*='product']",
        "article",
        ".grid > div",
    ]
    PRODUCT_LINK_SELECTOR = "a[href*='/p/'], a[href*='/product/']"
    PRODUCT_PRESENCE_SELECTORS = PRODUCT_CONTAINER_SELECTORS + [PRODUCT_LINK_SELECTOR]

    def __init__(self, query, max_pages=30):
        self.query = query
        self.max_pages = max_pages
        self.products = []
        self.seen_urls = set()

    def run(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            print("Opening Noon...")
            loaded_url, response = self._open_search_page(page)
            if not loaded_url:
                print("Search page returned 404 for all known markets - stopping")
                browser.close()
                return
            print(f"Loaded search page: {loaded_url}")

            self.accept_cookies(page)
            page.mouse.wheel(0, 2500)
            time.sleep(1.5)

            selector = self._wait_for_products_with_retry(page, timeout=60000)
            if not selector:
                print("No products found on first page - stopping")
                browser.close()
                return
            print(f"Page 1 loaded with selector: {selector}")

            current_page = 1
            while current_page <= self.max_pages:
                # PAGINATION FIX
                if not self._validate_pagination_products(page):
                    break

                print(f"\nSCRAPING PAGE {current_page}")
                self.scrape_page(page, current_page)

                next_button = page.locator("a[rel='next'], a[aria-label='Next page']").first
                if next_button.count() == 0:
                    print("No next button found - stopping")
                    break

                if next_button.get_attribute("aria-disabled") == "true":
                    print("Last page reached")
                    break

                print("Moving to next page...")
                previous_url = page.url
                time.sleep(random.uniform(1.0, 2.0))
                next_button.click()

                try:
                    page.wait_for_url(lambda url: url != previous_url, timeout=30000)
                except PlaywrightTimeoutError:
                    pass

                try:
                    page.wait_for_load_state("networkidle", timeout=30000)
                except PlaywrightTimeoutError:
                    pass

                if self._is_404_page(page):
                    print("Reached 404 page - stopping")
                    break

                page.mouse.wheel(0, 2500)
                time.sleep(1.5)

                # PAGINATION FIX
                if not self._validate_pagination_products(page):
                    break

                current_page += 1

            self.save_results()
            browser.close()
            print("Browser closed")

    def _build_search_urls(self):
        encoded_query = quote_plus(self.query)
        return [
            f"https://www.noon.com/egypt-en/search?q={encoded_query}",
            f"https://www.noon.com/saudi-en/search?q={encoded_query}",
            f"https://www.noon.com/uae-en/search?q={encoded_query}",
            f"https://www.noon.com/search?q={encoded_query}",
        ]

    def _open_search_page(self, page):
        for candidate in self._build_search_urls():
            try:
                print(f"Trying: {candidate}")
                response = page.goto(candidate, wait_until="domcontentloaded", timeout=60000)
                if not self._is_404_page(page, response):
                    return candidate, response
                status = getattr(response, "status", None)
                print(f"Skipped (not found): status={status}, url={page.url}")
            except PlaywrightTimeoutError:
                print(f"Timed out loading: {candidate}")
                continue
            except Exception as exc:
                print(f"Failed loading {candidate}: {exc}")
                continue
        return None, None

    def accept_cookies(self, page):
        selectors = [
            "text=ACCEPT ALL",
            "button:has-text('Accept')",
            "button:has-text('I Accept')",
        ]
        for selector in selectors:
            try:
                button = page.locator(selector).first
                if button.count() > 0 and button.is_visible():
                    button.click()
                    print("Cookie banner accepted")
                    return
            except Exception:
                continue

    def _is_404_page(self, page, response=None):
        try:
            if response and hasattr(response, "status") and response.status in (404, 410):
                return True

            parsed = urlparse(page.url)
            path = parsed.path.lower()
            if path.endswith("/404") or "/404/" in path or "not-found" in path:
                return True

            title = (page.title() or "").strip().lower()
            if title.startswith("404") or "page not found" in title:
                return True

            body_text = ""
            try:
                body_text = page.locator("body").inner_text(timeout=5000).strip().lower()
            except Exception:
                pass

            not_found_phrases = (
                "page not found",
                "this page does not exist",
                "the page you requested cannot be found",
                "sorry, we couldn't find this page",
            )
            if any(phrase in body_text for phrase in not_found_phrases):
                return True

            return False
        except Exception:
            return False

    def _page_has_products(self, page):
        try:
            for selector in self.PRODUCT_PRESENCE_SELECTORS:
                if page.locator(selector).count() > 0:
                    return True
            return False
        except Exception:
            return False

    # PAGINATION FIX
    def _wait_for_product_grid(self, page, timeout=25000):
        grid_selectors = [
            "[data-qa='product-grid']",
            "[data-qa='products']",
            "[class*='productGrid']",
            "[class*='productsContainer']",
            "main",
        ]
        per_selector_timeout = max(1500, timeout // max(1, len(grid_selectors)))
        for selector in grid_selectors:
            try:
                page.locator(selector).first.wait_for(
                    state="visible", timeout=per_selector_timeout
                )
                return selector
            except PlaywrightTimeoutError:
                continue
            except Exception:
                continue
        return ""

    # PAGINATION FIX
    def _validate_pagination_products(self, page):
        self._wait_for_product_grid(page, timeout=25000)
        products = page.query_selector_all("a[href*='/p/'], a[href*='/product/']")
        product_count = len(products)

        if product_count == 0:
            print("No products found - ending pagination")
            return False

        if product_count < 3:
            time.sleep(3)
            products = page.query_selector_all("a[href*='/p/'], a[href*='/product/']")
            if len(products) == 0:
                print("No products found - ending pagination")
                return False

        return True

    def _wait_for_products_with_retry(self, page, timeout=60000, max_retries=2):
        for attempt in range(max_retries + 1):
            try:
                return self.wait_for_products(page, timeout)
            except PlaywrightTimeoutError:
                if attempt >= max_retries:
                    return None
                retry_delay = random.uniform(1.5, 3.0)
                print(
                    f"Products not loaded, retrying in {retry_delay:.1f}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(retry_delay)
                page.mouse.wheel(0, 1200)
                time.sleep(1)
        return None

    def wait_for_products(self, page, timeout=60000):
        per_selector_timeout = max(
            1500, timeout // max(1, len(self.PRODUCT_PRESENCE_SELECTORS))
        )
        for selector in self.PRODUCT_PRESENCE_SELECTORS:
            try:
                page.locator(selector).first.wait_for(
                    state="visible", timeout=per_selector_timeout
                )
                return selector
            except PlaywrightTimeoutError:
                continue
        raise PlaywrightTimeoutError("No product elements became visible in time.")

    def get_product_cards(self, page):
        for selector in self.PRODUCT_CONTAINER_SELECTORS:
            cards = page.locator(selector)
            if cards.count() > 0:
                return cards, selector

        links = page.locator(self.PRODUCT_LINK_SELECTOR)
        if links.count() > 0:
            return links, self.PRODUCT_LINK_SELECTOR

        return page.locator("div.__no_products__"), ""


    def _clean_text(self, value):
        if value is None:
            return None
        text = " ".join(str(value).replace("\xa0", " ").split())
        return text or None

    def _normalize_price(self, value):
        text = self._clean_text(value)
        if not text:
            return None
        match = re.search(r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?", text)
        if not match:
            return None
        number = match.group(0).replace(",", "")
        try:
            return round(float(number), 2)
        except Exception:
            return None

    def _normalize_rating(self, value):
        text = self._clean_text(value)
        if not text:
            return None
        match = re.search(r"\b([0-5](?:\.\d+)?)\b", text)
        if not match:
            return None
        try:
            return float(match.group(1))
        except Exception:
            return None

    def _extract_json_objects(self, raw_text):
        text = (raw_text or "").replace("<!--", "").replace("-->", "").strip()
        if text.endswith(";"):
            text = text[:-1].strip()
        if not text:
            return []

        parsed = []
        try:
            parsed.append(json.loads(text))
            return parsed
        except Exception:
            pass

        decoder = json.JSONDecoder()
        index = 0
        while index < len(text):
            while index < len(text) and text[index].isspace():
                index += 1
            if index >= len(text):
                break
            try:
                obj, end = decoder.raw_decode(text, index)
            except Exception:
                break
            parsed.append(obj)
            index = end
        return parsed

    def _iter_json_dicts(self, obj):
        if isinstance(obj, dict):
            yield obj
            for value in obj.values():
                yield from self._iter_json_dicts(value)
        elif isinstance(obj, list):
            for item in obj:
                yield from self._iter_json_dicts(item)

    def _is_product_schema(self, schema_obj):
        schema_type = schema_obj.get("@type")
        if isinstance(schema_type, list):
            values = [str(x).lower() for x in schema_type]
            return any("product" in value for value in values)
        if isinstance(schema_type, str):
            return "product" in schema_type.lower()
        return False

    def _extract_json_ld_product(self, page):
        extracted = {
            "title": None,
            "price": None,
            "seller_score": None,
            "category": None,
        }

        try:
            scripts = page.locator("script[type='application/ld+json']")
            count = scripts.count()
        except Exception:
            return extracted

        for idx in range(count):
            try:
                raw = scripts.nth(idx).inner_text()
            except Exception:
                continue

            for payload in self._extract_json_objects(raw):
                for node in self._iter_json_dicts(payload):
                    if not self._is_product_schema(node):
                        continue

                    if extracted["title"] is None:
                        extracted["title"] = self._clean_text(node.get("name"))

                    if extracted["price"] is None:
                        offers = node.get("offers")
                        offer_obj = None
                        if isinstance(offers, dict):
                            offer_obj = offers
                        elif isinstance(offers, list):
                            offer_obj = next(
                                (item for item in offers if isinstance(item, dict)),
                                None,
                            )
                        if offer_obj:
                            extracted["price"] = self._normalize_price(
                                offer_obj.get("price") or offer_obj.get("lowPrice")
                            )

                    if extracted["seller_score"] is None:
                        agg = node.get("aggregateRating")
                        if isinstance(agg, dict):
                            extracted["seller_score"] = self._normalize_rating(
                                agg.get("ratingValue")
                            )

                    if extracted["category"] is None:
                        category = node.get("category")
                        if isinstance(category, list) and category:
                            category = category[-1]
                        extracted["category"] = self._clean_text(category)

                    if (
                        extracted["title"] is not None
                        and extracted["price"] is not None
                        and extracted["seller_score"] is not None
                        and extracted["category"] is not None
                    ):
                        return extracted
        return extracted

    def _extract_title(self, page):
        for selector in ("main h1", "span[class*='ProductTitle']", "h1"):
            try:
                candidate = page.locator(selector).first
                if candidate.count() == 0:
                    continue
                text = self._clean_text(candidate.inner_text())
                if text:
                    return text
            except Exception:
                continue
        return None

    def _extract_price_dom(self, page):
        selectors = [
            "span[class*='priceNowText']",
            "span[class*='price']",
        ]

        for selector in selectors:
            try:
                node = page.locator(selector).first
                if node.count() == 0:
                    continue
                amount = self._normalize_price(node.inner_text())
                if amount:
                    return amount
            except Exception:
                continue

        try:
            currency_node = page.locator("span[class*='currency']").first
            amount_node = page.locator("span[class*='priceNowText']").first
            if currency_node.count() > 0 and amount_node.count() > 0:
                combined = f"{currency_node.inner_text()} {amount_node.inner_text()}"
                amount = self._normalize_price(combined)
                if amount:
                    return amount
        except Exception:
            pass
        return None

    def _clean_details_text(self, raw_text, title):
        if raw_text is None:
            return None

        text = str(raw_text)
        text = unescape(text)
        text = re.sub(r"(?i)<br\s*/?>|</p>|</li>|</div>|</h[1-6]>", "\n", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = (
            text.replace("\xa0", " ")
            .replace("\u200f", " ")
            .replace("\u200e", " ")
            .replace("\u202a", " ")
            .replace("\u202c", " ")
        )
        text = re.sub(r"[\x00-\x1f\x7f]", " ", text)

        title_clean = (self._clean_text(title) or "").lower()
        blocked_patterns = [
            r"frequently bought together",
            r"\bcoupons?\b",
            r"\bpayment\b",
            r"\bdelivery\b",
            r"\bcashback\b",
            r"\bbuy now pay later\b",
            r"\binstallments?\b",
            r"\bseller\b",
            r"\brating[s]?\b",
            r"\breviews?\b",
            r"\bprice\b",
            r"\bfree shipping\b",
            r"\byou may also like\b",
        ]
        price_line_pattern = r"(?:\b(?:aed|egp|sar)\b\s*\d|[\$]\s*\d)"
        breadcrumb_pattern = r"\bhome\b\s*(?:>|/)"

        lines = [line.strip() for line in text.splitlines()]
        kept = []
        for line in lines:
            compact = self._clean_text(line)
            if not compact:
                continue
            lowered = compact.lower()
            if lowered in ("product overview", "overview"):
                continue
            if title_clean and (lowered == title_clean or lowered.startswith(title_clean)):
                continue
            if re.search(breadcrumb_pattern, lowered):
                continue
            if re.search(price_line_pattern, lowered):
                continue
            if any(re.search(pattern, lowered) for pattern in blocked_patterns):
                continue
            kept.append(compact)

        if not kept:
            return None

        merged = "\n".join(kept)
        merged = re.sub(r"\n{2,}", "\n", merged).strip()
        merged = re.sub(r"[ \t]{2,}", " ", merged)
        merged = re.sub(r"([^\w\s\.,;:\-\(\)/%]){2,}", " ", merged)
        merged = self._clean_text(merged)
        if not merged:
            return None

        if title_clean and merged.lower().startswith(title_clean):
            merged = self._clean_text(merged[len(title_clean):])

        return merged

    def _details_has_forbidden_content(self, text):
        if not text:
            return True
        lowered = text.lower()

        forbidden_phrases = [
            "frequently bought",
            "coupon",
            "coupons",
            "payment",
            "delivery",
            "buy now pay later",
            "cashback",
        ]
        if any(phrase in lowered for phrase in forbidden_phrases):
            return True

        forbidden_patterns = [
            r"\bhome\b\s*(?:>|/)",
            r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:ratings?|reviews?)\b",
            r"\b(?:aed|egp|sar)\b\s*\d",
            r"[\$]\s*\d",
            r"\b\d+(?:\.\d+)?\s*/\s*5\b",
        ]
        return any(re.search(pattern, lowered) for pattern in forbidden_patterns)

    def _is_valid_details_text(self, text, min_len=80):
        if not text:
            return False
        candidate = self._clean_text(text)
        if not candidate:
            return False
        if len(candidate) <= min_len:
            return False
        if not re.search(r"[A-Za-z]", candidate):
            return False
        if self._details_has_forbidden_content(candidate):
            return False
        return True

    def _wait_for_details_sources(self, page, timeout_ms=25000):
        try:
            page.locator("h1").first.wait_for(state="visible", timeout=timeout_ms)
        except Exception:
            pass

        try:
            page.wait_for_function(
                """() => {
                    const hasJsonLd = Boolean(
                        document.querySelector("script[type='application/ld+json']")
                    );
                    const bodyText = (
                        document.body && document.body.innerText
                            ? document.body.innerText.toLowerCase()
                            : ""
                    );
                    return (
                        hasJsonLd ||
                        bodyText.includes("product overview") ||
                        bodyText.includes("specifications")
                    );
                }""",
                timeout=timeout_ms,
            )
        except Exception:
            pass

    def _extract_details_from_json_ld(self, page, title):
        product_descriptions = []
        try:
            scripts = page.locator("script[type='application/ld+json']")
            count = scripts.count()
        except Exception:
            return None

        for idx in range(count):
            try:
                raw = scripts.nth(idx).inner_text()
            except Exception:
                continue

            for payload in self._extract_json_objects(raw):
                for node in self._iter_json_dicts(payload):
                    if not isinstance(node, dict):
                        continue
                    if not self._is_product_schema(node):
                        continue

                    value = node.get("description")
                    if isinstance(value, list):
                        value = " ".join(str(item) for item in value if item is not None)
                    if not isinstance(value, str):
                        continue

                    lowered = value.lower()
                    if (
                        "noon is an e-commerce shopping website" in lowered
                        or "e-commerce shopping website" in lowered
                        or "online shopping website" in lowered
                    ):
                        continue

                    product_descriptions.append(value)

        seen = set()
        for description in product_descriptions:
            key = description.strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            cleaned = self._clean_details_text(description, title)
            if self._is_valid_details_text(cleaned, min_len=80):
                return cleaned
        return None

    def _extract_details_from_overview(self, page, title):
        try:
            raw = page.evaluate(
                """() => {
                    const clean = (value) => (value || "").replace(/\\s+/g, " ").trim();
                    const isVisible = (el) => {
                        if (!el) return false;
                        const style = window.getComputedStyle(el);
                        if (!style) return false;
                        if (style.display === "none" || style.visibility === "hidden") return false;
                        const rect = el.getBoundingClientRect();
                        return rect.width > 0 && rect.height > 0;
                    };
                    const getText = (el) => clean(el ? (el.innerText || el.textContent || "") : "");
                    const headingSelectors = "h1,h2,h3,h4,h5,h6,div,span,p,strong";
                    const headingNodes = Array.from(document.querySelectorAll(headingSelectors));

                    const dedupe = (items) => {
                        const seen = new Set();
                        const out = [];
                        for (const item of items) {
                            const key = clean(item).toLowerCase();
                            if (!key || seen.has(key)) continue;
                            seen.add(key);
                            out.push(clean(item));
                        }
                        return out;
                    };

                    const findHeading = (patterns) => {
                        for (const node of headingNodes) {
                            if (!isVisible(node)) continue;
                            const text = getText(node);
                            if (!text || text.length > 80) continue;
                            const lowered = text.toLowerCase();
                            if (patterns.some((pattern) => pattern.test(lowered))) {
                                return node;
                            }
                        }
                        return null;
                    };

                    const collectSiblingBlocks = (startNode, stopPatterns) => {
                        const blocks = [];
                        if (!startNode) return blocks;

                        let sibling = startNode.nextElementSibling;
                        let guard = 0;
                        while (sibling && guard < 120) {
                            guard += 1;
                            if (!isVisible(sibling)) {
                                sibling = sibling.nextElementSibling;
                                continue;
                            }

                            const siblingText = getText(sibling);
                            const siblingLower = siblingText.toLowerCase();
                            const headingLike = /^H[1-6]$/.test(sibling.tagName || "");
                            if (
                                siblingText &&
                                siblingText.length <= 80 &&
                                stopPatterns.some((pattern) => pattern.test(siblingLower))
                            ) {
                                break;
                            }
                            if (
                                headingLike &&
                                siblingText &&
                                stopPatterns.some((pattern) => pattern.test(siblingLower))
                            ) {
                                break;
                            }

                            const lis = Array.from(sibling.querySelectorAll("li"))
                                .map((li) => getText(li))
                                .filter(Boolean);
                            if (lis.length > 0) {
                                blocks.push(...lis);
                            } else if (siblingText && siblingText.length < 5000) {
                                blocks.push(siblingText);
                            }

                            sibling = sibling.nextElementSibling;
                        }
                        return blocks;
                    };

                    const overviewHeading = findHeading([/^product overview$/i, /product overview/i]);
                    let overview = "";
                    if (overviewHeading) {
                        const overviewBlocks = collectSiblingBlocks(overviewHeading, [
                            /^highlights?$/i,
                            /^specifications?$/i,
                        ]);
                        overview = dedupe(overviewBlocks).join("\\n");

                        if (!overview) {
                            const section = overviewHeading.closest("section,article,div");
                            if (section) {
                                const paragraphs = Array.from(section.querySelectorAll("p"))
                                    .map((p) => getText(p))
                                    .filter(Boolean);
                                overview = dedupe(paragraphs).join("\\n");
                            }
                        }
                    }

                    const highlightsHeading = findHeading([/^highlights?$/i]);
                    const highlightBlocks = collectSiblingBlocks(highlightsHeading, [
                        /^specifications?$/i,
                        /^product overview$/i,
                    ]);
                    const highlights = [];
                    for (const block of highlightBlocks) {
                        const parts = String(block).split(/\\n|\\u2022/g).map((x) => clean(x)).filter(Boolean);
                        if (parts.length > 1) {
                            highlights.push(...parts);
                        } else if (parts.length === 1) {
                            highlights.push(parts[0]);
                        }
                    }

                    const specificationsHeading = findHeading([/^specifications?$/i, /^specification$/i]);
                    const specificationRows = [];
                    if (specificationsHeading) {
                        const roots = [];
                        const root = specificationsHeading.closest("section,article,div") || specificationsHeading.parentElement;
                        if (root) roots.push(root);

                        let sibling = specificationsHeading.nextElementSibling;
                        let count = 0;
                        while (sibling && count < 30) {
                            count += 1;
                            if (isVisible(sibling)) roots.push(sibling);
                            const text = getText(sibling).toLowerCase();
                            if (/^(highlights?|product overview)$/.test(text)) break;
                            sibling = sibling.nextElementSibling;
                        }

                        const pushRow = (key, value) => {
                            const k = clean(key);
                            const v = clean(value);
                            if (!k || !v) return;
                            specificationRows.push(`${k}: ${v}`);
                        };

                        for (const scope of roots) {
                            const trs = Array.from(scope.querySelectorAll("tr"));
                            for (const tr of trs) {
                                if (specificationRows.length >= 80) break;
                                const cells = Array.from(tr.querySelectorAll("th,td"))
                                    .map((cell) => getText(cell))
                                    .filter(Boolean);
                                if (cells.length >= 2) {
                                    pushRow(cells[0], cells[1]);
                                }
                            }

                            const dts = Array.from(scope.querySelectorAll("dt"));
                            for (const dt of dts) {
                                if (specificationRows.length >= 80) break;
                                const dd = dt.nextElementSibling;
                                pushRow(getText(dt), getText(dd));
                            }

                            const lis = Array.from(scope.querySelectorAll("li"));
                            for (const li of lis) {
                                if (specificationRows.length >= 80) break;
                                const line = getText(li);
                                if (!line || !line.includes(":")) continue;
                                specificationRows.push(line);
                            }
                        }
                    }

                    return {
                        overview: overview || "",
                        highlights: dedupe(highlights),
                        specifications: dedupe(specificationRows),
                    };
                }"""
            )
        except Exception:
            raw = {}

        if not isinstance(raw, dict):
            return None

        def dedupe_lines(items):
            output = []
            seen = set()
            for item in items:
                key = (item or "").strip().lower()
                if not key or key in seen:
                    continue
                seen.add(key)
                output.append(item)
            return output

        overview = self._clean_details_text(raw.get("overview") or "", title)

        highlights = []
        for item in raw.get("highlights") or []:
            cleaned_item = self._clean_details_text(item, title) or self._clean_text(item)
            if not cleaned_item:
                continue
            if self._details_has_forbidden_content(cleaned_item):
                continue
            highlights.append(cleaned_item)
        highlights = dedupe_lines(highlights)

        specifications = []
        for row in raw.get("specifications") or []:
            line = self._clean_text(row)
            if not line or ":" not in line:
                continue
            if self._details_has_forbidden_content(line):
                continue
            specifications.append(line)
        specifications = dedupe_lines(specifications)

        sections = []
        if overview:
            sections.append(f"Product Overview:\n{overview}")
        if highlights:
            sections.append("Highlights:\n" + "\n".join(f"- {point}" for point in highlights))
        if specifications:
            sections.append("Specifications:\n" + "\n".join(specifications))

        if not sections:
            return None

        structured = "\n\n".join(sections)
        if self._is_valid_details_text(structured, min_len=80):
            return structured
        return None

    def _extract_details_from_specifications(self, page, title):
        try:
            raw = page.evaluate(
                """() => {
                    const clean = (value) => (value || "").replace(/\\s+/g, " ").trim();
                    const isVisible = (el) => {
                        if (!el) return false;
                        const style = window.getComputedStyle(el);
                        if (!style) return false;
                        if (style.display === "none" || style.visibility === "hidden") return false;
                        const rect = el.getBoundingClientRect();
                        return rect.width > 0 && rect.height > 0;
                    };
                    const getText = (el) => clean(el ? (el.innerText || el.textContent || "") : "");

                    const headers = Array.from(
                        document.querySelectorAll("h1,h2,h3,h4,h5,h6,div,span,p,strong")
                    ).filter((el) => isVisible(el) && /specifications/i.test(getText(el)));
                    if (!headers.length) return "";

                    const rows = [];
                    for (const header of headers.slice(0, 3)) {
                        const root = header.closest("section,article,div") || header.parentElement;
                        if (!root) continue;

                        const tableRows = Array.from(root.querySelectorAll("tr"));
                        for (const tr of tableRows) {
                            if (rows.length >= 40) break;
                            const cells = Array.from(tr.querySelectorAll("th,td"))
                                .map((cell) => getText(cell))
                                .filter(Boolean);
                            if (cells.length >= 2) {
                                rows.push(`${cells[0]}: ${cells[1]}`);
                            }
                        }
                        if (rows.length >= 40) break;

                        if (!rows.length) {
                            const dts = Array.from(root.querySelectorAll("dt"));
                            for (const dt of dts) {
                                if (rows.length >= 40) break;
                                const dd = dt.nextElementSibling;
                                const key = getText(dt);
                                const value = getText(dd);
                                if (key && value) rows.push(`${key}: ${value}`);
                            }
                        }

                        if (!rows.length) {
                            const lis = Array.from(root.querySelectorAll("li"));
                            for (const li of lis) {
                                if (rows.length >= 40) break;
                                const line = getText(li);
                                if (line.includes(":")) rows.push(line);
                            }
                        }

                        if (rows.length) break;
                    }

                    return rows.join("\\n");
                }"""
            )
        except Exception:
            raw = ""

        cleaned = self._clean_details_text(raw, title)
        if cleaned and len(cleaned) > 50 and re.search(r"[A-Za-z]", cleaned):
            return cleaned
        return None

    def _extract_details_from_smart_scan(self, page, title):
        try:
            raw = page.evaluate(
                """() => {
                    const clean = (value) => (value || "").replace(/\\s+/g, " ").trim();
                    const isVisible = (el) => {
                        if (!el) return false;
                        const style = window.getComputedStyle(el);
                        if (!style) return false;
                        if (style.display === "none" || style.visibility === "hidden") return false;
                        const rect = el.getBoundingClientRect();
                        return rect.width > 0 && rect.height > 0;
                    };
                    const selectors = [
                        "[class*='overview']",
                        "[id*='overview']",
                        "[class*='description']",
                        "[id*='description']",
                        "[class*='details']",
                        "[id*='details']",
                    ];

                    let longest = "";
                    for (const selector of selectors) {
                        const nodes = Array.from(document.querySelectorAll(selector));
                        for (const node of nodes) {
                            if (!isVisible(node)) continue;
                            const text = clean(node.innerText || node.textContent || "");
                            if (text.length > longest.length && text.length < 15000) {
                                longest = text;
                            }
                        }
                    }
                    return longest;
                }"""
            )
        except Exception:
            raw = ""

        cleaned = self._clean_details_text(raw, title)
        if self._is_valid_details_text(cleaned, min_len=80):
            return cleaned
        return None

    def _extract_details_text(self, page, title):
        self._wait_for_details_sources(page, timeout_ms=25000)

        details_text = self._extract_details_from_json_ld(page, title)
        if details_text:
            return details_text

        details_text = self._extract_details_from_overview(page, title)
        if details_text:
            return details_text

        details_text = self._extract_details_from_specifications(page, title)
        if details_text:
            if self._is_valid_details_text(details_text, min_len=80):
                return details_text
            return None

        details_text = self._extract_details_from_smart_scan(page, title)
        if details_text and self._is_valid_details_text(details_text, min_len=80):
            return details_text

        return None

    def _extract_seller_score(self, page):
        try:
            meta_rating = page.locator("meta[itemprop='ratingValue']").first
            if meta_rating.count() > 0:
                rating = self._normalize_rating(meta_rating.get_attribute("content"))
                if rating:
                    return rating
        except Exception:
            pass

        try:
            containers = page.locator("[class*='rating']")
            limit = min(containers.count(), 8)
            for idx in range(limit):
                text = containers.nth(idx).inner_text()
                rating = self._normalize_rating(text)
                if rating:
                    return rating
        except Exception:
            pass
        return None

    def _extract_category(self, page):
        try:
            active = page.locator("span[class*='Breadcrumb'][class*='active']").last
            if active.count() > 0:
                value = self._clean_text(active.inner_text())
                if value and value.lower() != "home":
                    return value
        except Exception:
            pass

        for selector in ("nav[aria-label='breadcrumb']", "[class*='breadcrumb']"):
            try:
                container = page.locator(selector).first
                if container.count() == 0:
                    continue
                crumbs = container.locator("a, span, li")
                for idx in range(crumbs.count() - 1, -1, -1):
                    value = self._clean_text(crumbs.nth(idx).inner_text())
                    if not value:
                        continue
                    lowered = value.lower()
                    if lowered in ("home", "/", ">"):
                        continue
                    return value
            except Exception:
                continue
        return None

    def _validate_extracted_product(self, product, url):
        warnings = []
        title = product.get("title")
        price = product.get("price")
        details_text = product.get("details_text")
        seller_score = product.get("seller_score")
        category = product.get("category")
        has_numeric_price = isinstance(price, (int, float)) and not isinstance(price, bool)
        has_numeric_seller_score = isinstance(seller_score, (int, float)) and not isinstance(
            seller_score, bool
        )

        if not title or len(title) <= 10:
            warnings.append("title length <= 10")
        if not has_numeric_price:
            warnings.append("price missing numeric content")
        if not details_text or len(details_text) <= 80:
            warnings.append("details_text length <= 80")
        if not has_numeric_seller_score:
            warnings.append("seller_score is not numeric-only")
        if not category or category.strip().lower() == "home":
            warnings.append("category missing or equals Home")

        if warnings:
            print(f"    Warning PDP validation for {url}: {'; '.join(warnings)}")

    def _extract_product_details(self, page, url):
        product = {
            "title": None,
            "price": None,
            "details_text": None,
            "seller_score": None,
            "category": None,
            "link": url,
        }

        json_ld = self._extract_json_ld_product(page)
        for field in ("title", "price", "seller_score", "category"):
            if json_ld.get(field) is not None:
                product[field] = json_ld[field]

        if product["title"] is None:
            product["title"] = self._extract_title(page)
        if product["price"] is None:
            product["price"] = self._extract_price_dom(page)
        if product["seller_score"] is None:
            product["seller_score"] = self._extract_seller_score(page)
        if product["category"] is None:
            product["category"] = self._extract_category(page)

        product["details_text"] = self._extract_details_text(page, product["title"])
        self._validate_extracted_product(product, url)
        return product

    def scrape_page(self, page, page_number):
        product_cards, selector = self.get_product_cards(page)
        count = product_cards.count()
        print(f"Found {count} product containers using selector: {selector or 'none'}")

        for i in range(count):
            try:
                card = product_cards.nth(i)
                link = (
                    card
                    if selector == self.PRODUCT_LINK_SELECTOR
                    else card.locator("a[href]").first
                )
                url = link.get_attribute("href")
                if not url:
                    continue

                if not url.startswith("http"):
                    url = "https://www.noon.com" + url

                if url in self.seen_urls:
                    continue
                self.seen_urls.add(url)

                name = link.inner_text().strip()
                if not name and selector != self.PRODUCT_LINK_SELECTOR:
                    name = card.inner_text().split("\n")[0].strip()
                if not name:
                    name = "Unnamed product"

                extracted_product = {
                    "title": None,
                    "price": None,
                    "details_text": None,
                    "seller_score": None,
                    "category": None,
                    "link": url,
                }

                current_search_url = page.url
                if url and url.startswith("http"):
                    try:
                        print(f"    Fetching details for: {name[:30]}...")
                        product_page_response = page.goto(
                            url, wait_until="domcontentloaded", timeout=30000
                        )

                        if product_page_response and product_page_response.status == 200:
                            time.sleep(1)
                            extracted_product = self._extract_product_details(page, url)
                    except Exception as e:
                        print(f"    Error fetching product details: {str(e)[:50]}")
                    finally:
                        try:
                            page.goto(
                                current_search_url,
                                wait_until="domcontentloaded",
                                timeout=30000,
                            )
                            time.sleep(0.5)
                        except Exception:
                            pass

                product_data = {
                    "metadata": {
                        "source": "noon",
                        "scraped_at": datetime.utcnow().isoformat(),
                        "search_query": self.query,
                        "page_number": int(page_number),
                    },
                    "product": extracted_product,
                }

                # FILTERING FIX
                category_value = extracted_product.get("category")
                title_value = extracted_product.get("title")
                allow_product = False

                if isinstance(category_value, str):
                    category_lower = category_value.lower()
                    if any(keyword in category_lower for keyword in ("laptop", "notebook")):
                        allow_product = True

                if not allow_product and isinstance(title_value, str):
                    title_lower = title_value.lower()
                    if any(keyword in title_lower for keyword in ("laptop", "notebook")):
                        allow_product = True

                if not allow_product:
                    continue

                self.products.append(product_data)
                print(f"  OK {name[:40]}")
            except Exception as exc:
                print(f"  Error on product {i}: {str(exc)[:80]}")
                continue

    def save_results(self):
        safe_query = self.query.replace(" ", "_")
        filename = f"noon_results_{safe_query}.json"
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(self.products, file, indent=4, ensure_ascii=False)
        print(f"\nSaved {len(self.products)} products to {filename}")


if __name__ == "__main__":
    query = input("Enter product search query: ")
    scraper = NoonScraper(query=query, max_pages=2)
    scraper.run()
