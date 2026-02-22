from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import json
import os
from datetime import datetime


def create_brave_driver(
    brave_path=r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    headless=False,
    disable_images=True,
    disable_notifications=True,
    mute_audio=True,
    disable_extensions=True,
    incognito=False,
    window_size="1920,1080",
):
    """
    Initialize a Selenium WebDriver using Brave with performance optimizations.

    Parameters:
        brave_path (str): Path to brave.exe
        headless (bool): Run browser without UI
        disable_images (bool): Block images for faster loading
        disable_notifications (bool): Block website notifications
        mute_audio (bool): Mute browser audio
        disable_extensions (bool): Disable extensions
        incognito (bool): Open in incognito mode
        window_size (str): Browser window size (e.g., "1920,1080")

    Returns:
        driver (webdriver.Chrome)
    """

    chrome_options = Options()

    # Use Brave instead of Chrome
    chrome_options.binary_location = brave_path

    # Performance arguments
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

    # Preferences (important for speed)
    prefs = {}

    if disable_images:
        prefs["profile.managed_default_content_settings.images"] = 2

    if disable_notifications:
        prefs["profile.default_content_setting_values.notifications"] = 2

    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_experimental_option("detach", True)

    # Create driver using webdriver-manager
    driver_path = ChromeDriverManager().install()

    # webdriver-manager can return a non-executable metadata file on Windows.
    # Normalize to the actual chromedriver binary if needed.
    if not driver_path.lower().endswith(".exe"):
        exe_path = os.path.join(os.path.dirname(driver_path), "chromedriver.exe")
        if os.path.exists(exe_path):
            driver_path = exe_path

    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver


def create_metadata(source, search_query, page_number):
    return {
        "source": source,
        "scraped_at": datetime.now().isoformat(),
        "search_query": search_query,
        "page_number": page_number,
    }


def build_records(products, source, search_query, page_number, normalize_fn):

    records = []

    for product in products:
        product = normalize_fn(product)
        metadata = create_metadata(source, search_query, page_number)

        record = {
            "metadata": metadata,
            "product": product,
        }
        records.append(record)

    return records


def upsert_records(records, file_path="data/products.json"):
    """
    Save records into one file.
    Use product.link as primary key.
    Update if exists, insert if new.
    """

    # Load existing data
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except:
                data = {}
    else:
        data = {}

    new_count = 0
    updated_count = 0

    for record in records:
        url = record["product"].get("link")
        if not url:
            continue

        # Normalize URL (remove tracking params)
        url = url.split("?")[0]
        record["product"]["link"] = url

        # Update scraped time
        record["metadata"]["scraped_at"] = datetime.now().isoformat()

        if url in data:
            updated_count += 1
        else:
            new_count += 1

        # Upsert
        data[url] = record

    # Save back to file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"New: {new_count} | Updated: {updated_count} | Total: {len(data)}")
