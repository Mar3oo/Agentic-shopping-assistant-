"""CLI orchestrator for scraping product data and ingesting normalized records into MongoDB."""

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from Data_Base.db import close_client
from Data_Base.ingestion import ingest_records
from scrapers import amazon, jumia, noon
from scrapers.base import build_records, create_brave_driver


def _prepare_jumia(driver, wait):
    """Open Jumia home page and dismiss popup when available."""
    driver.get("https://www.jumia.com.eg/")
    try:
        popup_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "cls")))
        popup_btn.click()
    except Exception:
        pass


def _prepare_noon(driver, _wait):
    """Open Noon landing page and trigger initial lazy content load."""
    driver.get("https://www.noon.com/egypt-en/")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)


def _prepare_amazon(driver, _wait):
    """Open Amazon Egypt landing page."""
    driver.get("https://www.amazon.eg")


SCRAPER_MAP = {
    "amazon": (amazon, _prepare_amazon),
    "jumia": (jumia, _prepare_jumia),
    "noon": (noon, _prepare_noon),
}


def run_scraping(site: str, query: str, pages: int) -> None:
    """Execute the full pipeline: scrape -> enrich -> build records -> ingest."""
    selected_site = site.strip().lower()
    scraper_entry = SCRAPER_MAP.get(selected_site)

    if scraper_entry is None:
        print("Invalid site")
        return

    scraper_module, prepare_fn = scraper_entry
    driver = create_brave_driver(incognito=True)
    wait = WebDriverWait(driver, 10)

    try:
        prepare_fn(driver, wait)

        products = scraper_module.get_all_products(driver, wait, query, pages)

        for product in products:
            link = product.get("link")
            if not link:
                continue

            try:
                extra_info = scraper_module.get_product_extra_info(driver, wait, link)
                product.update(extra_info)
            except Exception:
                # Keep the pipeline moving if one details page fails.
                continue

        records = build_records(
            products,
            selected_site,
            query,
            1,
            scraper_module.normalize_product,
        )

        summary = ingest_records(records)

        print(
            f"Source: {selected_site} | Scraped: {len(products)} | "
            f"Inserted: {summary['inserted']} | "
            f"Skipped: {summary['skipped']} | Failed: {summary['failed']}"
        )
    finally:
        driver.quit()
        close_client()


if __name__ == "__main__":
    site = input("Choose site (amazon/jumia/noon): ").strip().lower()
    query = input("Enter product: ").strip()

    try:
        pages = int(input("Pages: ").strip())
    except ValueError:
        pages = 1
        print("Invalid pages value. Defaulting to 1.")

    if pages < 1:
        pages = 1

    run_scraping(site, query, pages)
