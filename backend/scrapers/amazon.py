"""Amazon scraper that collects products, auto-paginates, and normalizes product fields."""

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


def get_products(driver):
    """Extract product title, price, and link from the current Amazon results page."""
    products = []
    items = driver.find_elements(
        By.XPATH,
        '//div[contains(@class,"s-result-item") and @data-asin]',
    )

    for item in items:
        try:
            title = item.find_element(
                By.CSS_SELECTOR,
                "h2.a-size-base-plus.a-spacing-none.a-color-base.a-text-normal span",
            ).text
        except Exception:
            title = None

        try:
            price_whole = item.find_element(By.CSS_SELECTOR, "span.a-price-whole").text
            price_fraction = item.find_element(
                By.CSS_SELECTOR, "span.a-price-fraction"
            ).text
            price = f"{price_whole}.{price_fraction}"
        except Exception:
            price = None

        try:
            link = item.find_element(
                By.CSS_SELECTOR,
                "a.a-link-normal.s-line-clamp-4.s-link-style.a-text-normal",
            ).get_attribute("href")
        except Exception:
            link = None

        if link and title and price:
            products.append({"title": title, "price": price, "link": link})

    return products


def _has_next_page(driver, current_page):
    """Return True when Amazon has a valid next-page control."""
    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, "a.s-pagination-next")
        classes = (next_btn.get_attribute("class") or "").lower()
        href = next_btn.get_attribute("href")
        if href and "s-pagination-disabled" not in classes:
            return True
    except Exception:
        pass

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
        url = f"https://www.amazon.eg/s?k={query_encoded}&page={page_num}"
        logger.info(f"Scraping page {page_num}")
        logger.info(f"URL: {url}")

        try:
            load_url_with_retry(
                driver,
                wait,
                url,
                lambda w: w.until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            '//div[contains(@class,"s-result-item") and @data-asin]',
                        )
                    )
                ),
                max_attempts=3,
            )
        except (TimeoutException, WebDriverException):
            break

        products = get_products(driver)
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
    """Open an Amazon product page in a new tab and extract details metadata."""
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
            lambda w: w.until(EC.presence_of_element_located((By.ID, "productTitle"))),
            max_attempts=2,
            min_delay=1.5,
            max_delay=3.0,
        )

        try:
            wait.until(EC.presence_of_element_located((By.ID, "feature-bullets")))

            bullets = driver.find_elements(By.CSS_SELECTOR, "#feature-bullets li")
            details_list = [
                b.text.strip()
                for b in bullets
                if b.text.strip() and "Loading" not in b.text
            ]

            details_text = "\n".join(details_list)

        except Exception:
            pass

        try:
            wait.until(
                EC.presence_of_element_located((By.ID, "averageCustomerReviews"))
            )

            rating_element = driver.find_element(
                By.CSS_SELECTOR, "#averageCustomerReviews span.a-size-small"
            )

            seller_score = rating_element.text

        except Exception:
            pass

        try:
            wait.until(
                EC.presence_of_element_located(
                    (By.ID, "wayfinding-breadcrumbs_feature_div")
                )
            )

            breadcrumb_elements = driver.find_elements(
                By.CSS_SELECTOR, "#wayfinding-breadcrumbs_feature_div li"
            )

            categories = [
                b.text.strip()
                for b in breadcrumb_elements
                if b.text.strip() and "›" not in b.text
            ]

            category = " > ".join(categories)
        except Exception:
            pass

        time.sleep(random.uniform(1.5, 2.5))
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
    """Normalize Amazon product URL, price, seller score, and text fields."""
    if product.get("link"):
        url = product["link"]
        match = re.search(r"/dp/([A-Z0-9]{10})", url)
        if match:
            asin = match.group(1)
            product["link"] = f"https://www.amazon.eg/dp/{asin}"
        else:
            product["link"] = url.split("?")[0].split("#")[0].strip()

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
