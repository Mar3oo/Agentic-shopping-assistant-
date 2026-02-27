"""Automated runner that scrapes configured sites/queries 
and upserts normalized records to MongoDB."""

import random
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from Data_base.db import close_client
from Data_base.ingestion import ingest_records
from scrapers import amazon, jumia, noon
from scrapers.base import build_records, create_brave_driver

SEARCH_QUERIES = []


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
    ("jumia", jumia, _prepare_jumia)
]


def _print_query_summary(site_name, query, summary):
    """Print query-level ingestion summary in the requested format."""
    print(f"Site: {site_name}")
    print(f"Query: {query}")
    print(f"Inserted: {summary['inserted']}")
    print(f"Updated: {summary['updated']}")
    print(f"Failed: {summary['failed']}")
    for error in summary.get("error_samples", []):
        print(f"Failure sample: {error}")


def _print_site_summary(site_name, totals):
    """Print site-level totals after all queries are processed."""
    print(f"Site: {site_name}")
    print(f"Total inserted: {totals['inserted']}")
    print(f"Total updated: {totals['updated']}")
    print(f"Total failed: {totals['failed']}")


def _enrich_products(driver, wait, scraper_module, products):
    """Fetch extra product details while tolerating per-product failures."""
    for product in products:
        link = product.get("link")
        if not link:
            continue

        try:
            extra_info = scraper_module.get_product_extra_info(driver, wait, link)
            product.update(extra_info)
        except Exception:
            continue


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
    driver = create_brave_driver(incognito=True, headless=True)
    wait = WebDriverWait(driver, 10)

    try:
        prepare_fn(driver, wait)

        for query in SEARCH_QUERIES:
            summary = {"inserted": 0, "updated": 0, "failed": 0}
            try:
                summary = _run_query(driver, wait, site_name, scraper_module, query)
            except Exception as exc:
                summary["failed"] += 1
                print(f"Query processing failed for site={site_name}, query='{query}': {exc}")

            _print_query_summary(site_name, query, summary)

            totals["inserted"] += summary["inserted"]
            totals["updated"] += summary["updated"]
            totals["failed"] += summary["failed"]

            time.sleep(random.uniform(5, 8))
    finally:
        driver.quit()

    _print_site_summary(site_name, totals)
    return totals


def run_all_sites():
    """Execute the automated site order: Amazon -> Noon -> Jumia."""
    try:
        for site_name, scraper_module, prepare_fn in SITE_PIPELINE:
            run_site(site_name, scraper_module, prepare_fn)
    finally:
        close_client()


if __name__ == "__main__":
    run_all_sites()
