"""Automated runner that scrapes configured sites/queries
and upserts normalized records to MongoDB."""

import logging
import os
import random
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# from Data_base.db import close_client
from Data_base.ingestion import ingest_records
from scrapers import amazon, jumia, noon
from scrapers.base import build_records, create_brave_driver

# Add this import to check for existing products before enrichment
from Data_base.db import get_collection

# from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

SKIP_EXISTING_PRODUCTS = True  # Toggle this when you want

# SEARCH_QUERIES = [
#     "laptop",
#     # "wireless headphones",
#     # "smartphones under 3000 EGP",
# ]

# Queries will be passed dynamically
SEARCH_QUERIES = None


def _prepare_jumia(driver, wait):
    """Open Jumia and dismiss popup when it appears."""
    driver.get("https://www.jumia.com.eg/")
    try:
        popup_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "cls")))
        popup_btn.click()
    except Exception:
        pass


def _prepare_noon(driver, _wait):
    """Open Noon home page and trigger initial lazy-load content."""
    driver.get("https://www.noon.com/egypt-en/")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)


def _prepare_amazon(driver, _wait):
    """Open Amazon Egypt home page."""
    driver.get("https://www.amazon.eg")


SITE_PIPELINE = [
    ("amazon", amazon, _prepare_amazon),
    ("noon", noon, _prepare_noon),
    ("jumia", jumia, _prepare_jumia),
]


def _print_query_summary(site_name, query, summary):
    """Print query-level ingestion summary in the requested format."""
    logger.info(f"Site: {site_name}")
    logger.info(f"Query: {query}")
    logger.info(f"Inserted: {summary['inserted']}")
    logger.info(f"Updated: {summary['updated']}")
    logger.info(f"Failed: {summary['failed']}")
    for error in summary.get("error_samples", []):
        logger.info(f"Failure sample: {error}")


def _print_site_summary(site_name, totals):
    """Print site-level totals after all queries are processed."""
    logger.info(f"Site: {site_name}")
    logger.info(f"Total inserted: {totals['inserted']}")
    logger.info(f"Total updated: {totals['updated']}")
    logger.info(f"Total failed: {totals['failed']}")


def load_existing_links():
    """
    Load all existing product links from MongoDB into a set.
    This allows very fast duplicate checking during scraping.
    """

    collection = get_collection()

    cursor = collection.find(
        {"product.link": {"$exists": True}},
        {"_id": 0, "product.link": 1},
    )

    links = set()

    for doc in cursor:
        link = doc.get("product", {}).get("link")
        if link:
            links.add(link)

    logger.info(f"[SCRAPER] Loaded {len(links)} existing product links")

    return links


def _process_product(scraper_module, driver, wait, product, existing_links):
    """
    Worker function for parallel product enrichment.
    """

    link = product.get("link")

    if not link:
        return product

    # Normalize link
    normalized_product = scraper_module.normalize_product(product.copy())
    normalized_link = normalized_product.get("link")

    # Fast duplicate check using set
    if SKIP_EXISTING_PRODUCTS and normalized_link and normalized_link in existing_links:
        return product

    try:
        # print("Scraping:", link)
        extra_info = scraper_module.get_product_extra_info(driver, wait, link)
        product.update(extra_info)
    except Exception:
        pass

    return product


existing_links = (
    load_existing_links()
)  # Load existing links once at the start of the scraper run


def _enrich_products(driver, wait, scraper_module, products):

    for product in products:
        try:
            _process_product(
                scraper_module,
                driver,
                wait,
                product,
                existing_links,
            )
        except Exception:
            pass


def _run_query(driver, wait, site_name, scraper_module, query):
    """Run the full scrape/enrich/build/upsert flow for a single query."""
    products = scraper_module.get_all_products(driver, wait, query)
    _enrich_products(driver, wait, scraper_module, products)

    records = build_records(
        products,
        site_name,
        query,
        1,
        scraper_module.normalize_product,
    )

    return ingest_records(records)


def run_site(site_name, scraper_module, prepare_fn):
    """Run all configured queries for one site using one headless browser session."""
    totals = {"inserted": 0, "updated": 0, "failed": 0}

    if site_name == "noon":
        headless_mode = False  # Set to False for Noon to avoid anti-scraping issues
    else:
        headless_mode = False

    driver = create_brave_driver(incognito=True, headless=headless_mode)
    wait = WebDriverWait(driver, 10)

    try:
        prepare_fn(driver, wait)

        # Limit to first query for testing; remove slicing for full run
        for query in SEARCH_QUERIES[:1]:
            summary = {"inserted": 0, "updated": 0, "failed": 0}
            try:
                summary = _run_query(driver, wait, site_name, scraper_module, query)
            except Exception as exc:
                summary["failed"] += 1
                logger.error(
                    f"Query processing failed for site={site_name}, query='{query}': {exc}"
                )

            _print_query_summary(site_name, query, summary)

            totals["inserted"] += summary["inserted"]
            totals["updated"] += summary["updated"]
            totals["failed"] += summary["failed"]

            time.sleep(random.uniform(5, 8))
    finally:
        driver.quit()

    _print_site_summary(site_name, totals)
    return totals


def run_all_sites(queries=None):
    """
    Execute the automated site order: Amazon -> Noon -> Jumia
    queries: list of search queries from profile agent
    """
    global SEARCH_QUERIES
    SEARCH_QUERIES = queries

    if not SEARCH_QUERIES:
        logger.info("No search queries provided.")
        return

    os.system("taskkill /f /im chromedriver.exe >nul 2>&1")

    try:
        for site_name, scraper_module, prepare_fn in SITE_PIPELINE:
            logger.info(f"[SCRAPER] Starting {site_name} scraper")

            run_site(site_name, scraper_module, prepare_fn)

            logger.info(f"[SCRAPER] Finished {site_name}")
    finally:
        pass


if __name__ == "__main__":
    run_all_sites()
