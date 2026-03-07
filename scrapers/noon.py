"""Noon scraper that collects products, auto-paginates, and normalizes product fields."""

import logging
import random
import re
import time
from urllib.parse import quote_plus

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from .base import load_url_with_retry

logger = logging.getLogger(__name__)

MAX_PAGES = 1


def get_products_noon(driver):
    """Extract product title, price, and link from the current Noon results page."""
    products = []
    product_cards = driver.find_elements(
        By.CSS_SELECTOR, "div[data-qa='plp-product-box']"
    )

    for item in product_cards:
        try:
            title = item.find_element(
                By.CSS_SELECTOR, "h2[data-qa='plp-product-box-name']"
            ).text
        except Exception:
            title = None

        try:
            price = item.find_element(By.CSS_SELECTOR, "strong[class*='amount']").text
        except Exception:
            price = None

        try:
            link = item.find_element(By.CSS_SELECTOR, "a[href*='/p/']").get_attribute(
                "href"
            )
        except Exception:
            link = None

        if link and title and price:
            products.append({"title": title, "price": price, "link": link})

    return products


def _has_next_page(driver, current_page):
    """Return True when Noon has a valid next-page control."""
    selectors = [
        "a[rel='next']",
        "a[aria-label*='Next']",
        "a[data-qa*='next']",
    ]

    for selector in selectors:
        for element in driver.find_elements(By.CSS_SELECTOR, selector):
            href = element.get_attribute("href")
            classes = (element.get_attribute("class") or "").lower()
            if href and "disabled" not in classes:
                return True

    next_page = current_page + 1
    return bool(
        driver.find_elements(By.XPATH, f"//a[contains(@href, 'page={next_page}')]")
    )


def get_all_products(driver, wait, query):
    """Scrape all available result pages for a query using automatic pagination."""
    all_products = []
    query_encoded = quote_plus(query)
    page_num = 1

    while page_num <= MAX_PAGES:
        url = f"https://www.noon.com/egypt-en/search?q={query_encoded}&page={page_num}"
        logger.info(f"Scraping page {page_num}")
        logger.info(f"URL: {url}")

        try:
            load_url_with_retry(
                driver,
                wait,
                url,
                lambda w: w.until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "div[data-qa='plp-product-box']")
                    )
                ),
                max_attempts=3,
            )
        except (TimeoutException, WebDriverException):
            break

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        products = get_products_noon(driver)
        logger.info(f"Products found: {len(products)}")

        if not products:
            break

        all_products.extend(products)

        if not _has_next_page(driver, page_num):
            break

        page_num += 1
        time.sleep(random.uniform(2, 4))

    return all_products


def get_product_extra_info(driver, wait, link):
    """Open a Noon product page in a new tab and extract details metadata."""
    details_text = None
    seller_score = None
    category = None

    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])

    try:
        load_url_with_retry(
            driver,
            wait,
            link,
            lambda w: w.until(EC.presence_of_element_located((By.TAG_NAME, "body"))),
            max_attempts=2,
            min_delay=1.5,
            max_delay=3.0,
        )

        try:
            wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div[class*="overviewDescriptionWrapper"]')
                )
            )

            paragraphs = driver.find_elements(
                By.CSS_SELECTOR, 'div[class*="overviewDescriptionWrapper"] p'
            )

            details_text = "\n".join(p.text for p in paragraphs if p.text.strip())

        except Exception:
            pass

        try:
            wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div[class*="RatingPreviewStarV2"]')
                )
            )

            rating_element = driver.find_element(
                By.CSS_SELECTOR, 'div[class*="RatingPreviewStarV2"] span[class*="text"]'
            )

            seller_score = rating_element.text.strip()

        except Exception:
            pass

        try:
            wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div[class*="Breadcrumb"]')
                )
            )

            breadcrumb_elements = driver.find_elements(
                By.CSS_SELECTOR, 'div[class*="Breadcrumb"] a'
            )

            categories = [b.text.strip() for b in breadcrumb_elements if b.text.strip()]

            category = " > ".join(categories)
        except Exception:
            pass

        time.sleep(random.uniform(1, 2))
    except (TimeoutException, WebDriverException):
        pass
    finally:
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

    return {
        "details_text": details_text,
        "seller_score": seller_score,
        "category": category,
    }


def normalize_product(product):
    """Normalize Noon product URL, price, seller score, and text fields."""
    if product.get("link"):
        product["link"] = str(product["link"]).split("?")[0].split("#")[0].strip()

    if product.get("price"):
        price_text = re.sub(r"[^\d.]", "", str(product["price"]))
        try:
            product["price"] = float(price_text)
        except Exception:
            product["price"] = None

    if product.get("seller_score"):
        score_text = str(product["seller_score"])
        match = re.search(r"\d+(\.\d+)?", score_text)
        if match:
            product["seller_score"] = float(match.group()) / 5
        else:
            product["seller_score"] = None

    for field in ["title", "details_text", "category"]:
        if product.get(field):
            product[field] = " ".join(str(product[field]).split())

    return product
