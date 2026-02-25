"""Shared scraper utilities for browser setup and metadata/product record construction."""

from datetime import datetime, timezone
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def create_brave_driver(
    brave_path=r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    headless=False,
    disable_images=True,
    disable_notifications=True,
    mute_audio=True,
    disable_extensions=True,
    incognito=False,
    window_size="1920,1080",
    detach=False,
):
    """Initialize a Selenium Chrome driver configured to use Brave."""

    chrome_options = Options()
    chrome_options.binary_location = brave_path

    chrome_options.add_argument(f"--window-size={window_size}")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    if headless:
        chrome_options.add_argument("--headless=new")

    if disable_extensions:
        chrome_options.add_argument("--disable-extensions")

    if incognito:
        chrome_options.add_argument("--incognito")

    if mute_audio:
        chrome_options.add_argument("--mute-audio")

    prefs = {}
    if disable_images:
        prefs["profile.managed_default_content_settings.images"] = 2
    if disable_notifications:
        prefs["profile.default_content_setting_values.notifications"] = 2

    chrome_options.add_experimental_option("prefs", prefs)
    if detach:
        chrome_options.add_experimental_option("detach", True)

    driver_path = ChromeDriverManager().install()

    # webdriver-manager can return a metadata path on Windows.
    if not driver_path.lower().endswith(".exe"):
        exe_path = os.path.join(os.path.dirname(driver_path), "chromedriver.exe")
        if os.path.exists(exe_path):
            driver_path = exe_path

    service = Service(driver_path)
    return webdriver.Chrome(service=service, options=chrome_options)


def create_metadata(source, search_query, page_number):
    """Create the metadata object embedded in each stored record."""
    return {
        "source": source,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "search_query": search_query,
        "page_number": page_number,
    }


def build_records(products, source, search_query, page_number, normalize_fn):
    """Build storage-ready records in {metadata, product} format."""

    records = []
    for product in products:
        normalized_product = normalize_fn(product)
        metadata = create_metadata(source, search_query, page_number)
        records.append({"metadata": metadata, "product": normalized_product})

    return records
