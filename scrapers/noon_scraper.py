from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import json
import os
from datetime import datetime
import re
from urllib.parse import quote_plus


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
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver


def get_products_noon(driver):
    """
    Extract product title, price, and link from Noon search page.
    Returns a list of dictionaries.
    """

    products = []

    PRODUCT_CARD_SELECTOR = "div[data-qa='plp-product-box']"

    TITLE_SELECTOR = "h2[data-qa='plp-product-box-name']"
    PRICE_SELECTOR = "strong[class*='amount']"
    LINK_SELECTOR = "a[href*='/p/']"  # this one is usually correct

    items = driver.find_elements(By.CSS_SELECTOR, PRODUCT_CARD_SELECTOR)

    print(f"Found {len(items)} product cards")

    for item in items:
        try:
            title = item.find_element(By.CSS_SELECTOR, TITLE_SELECTOR).text
        except:
            title = None

        try:
            price = item.find_element(By.CSS_SELECTOR, PRICE_SELECTOR).text
        except:
            price = None

        try:
            link = item.find_element(By.CSS_SELECTOR, LINK_SELECTOR).get_attribute(
                "href"
            )
        except:
            link = None

        if link:  # avoid empty cards
            products.append({"title": title, "price": price, "link": link})

    return products


def get_all_products(driver, wait, query, pages=3):
    all_products = []

    query_encoded = quote_plus(query)

    for page in range(1, pages + 1):
        url = f"https://www.noon.com/egypt-en/search?q={query_encoded}&page={page}"
        print(f"Scraping page {page}")
        print("URL:", url)

        driver.get(url)

        # Wait for products to load
        wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "div[data-qa='plp-product-box']")
            )
        )

        # Noon lazy loads → scroll once
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        products = get_products_noon(driver)
        print("Products found:", len(products))

        all_products.extend(products)

    return all_products


def get_product_extra_info(driver, wait, link):
    # Open new tab
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])

    driver.get(link)

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    details_text = None
    seller_score = None
    category = None

    # Product description
    try:
        details_container = driver.find_element(
            By.CSS_SELECTOR, "div[class*='overview'], div[id*='overview']"
        )
        details_text = details_container.text
    except:
        pass

    # Seller score
    try:
        seller_score = driver.find_element(
            By.CSS_SELECTOR, "div[class*='rating'] span"
        ).text
    except:
        pass

    # Category / Breadcrumb

    try:
        breadcrumbs = driver.find_elements(By.CSS_SELECTOR, "a[class*='breadcrumb']")
        category = ",".join([b.text.strip() for b in breadcrumbs if b.text.strip()])
    except:
        pass

    # Small delay (important to avoid blocking)
    time.sleep(random.uniform(1, 2))

    # Close tab
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

    return {
        "details_text": details_text,
        "seller_score": seller_score,
        "category": category,
    }


def normalize_product(product):

    # ---------- URL ----------
    if product.get("link"):
        url = product["link"]
        url = url.split("?")[0]
        url = url.split("#")[0]
        product["link"] = url.strip()

    # ---------- Price ----------
    if product.get("price"):
        price_text = product["price"]

        # Remove currency and commas
        price_text = re.sub(r"[^\d.]", "", price_text)

        try:
            product["price"] = float(price_text)
        except:
            product["price"] = None

    # ---------- Seller score (convert to 0–1 scale) ----------
    if product.get("seller_score"):
        score_text = product["seller_score"]

        match = re.search(r"\d+(\.\d+)?", score_text)
        if match:
            product["seller_score"] = float(match.group()) / 5
        else:
            product["seller_score"] = None

    # ---------- Clean text fields ----------
    for field in ["title", "details_text", "category"]:
        if product.get(field):
            product[field] = " ".join(product[field].split())

    return product


def create_metadata(source, search_query, page_number):
    return {
        "source": source,
        "scraped_at": datetime.now().isoformat(),
        "search_query": search_query,
        "page_number": page_number,
    }


def build_records(products, source, search_query, page_number):
    # metadata = create_metadata(source, search_query, page_number)
    records = []

    for product in products:
        product = normalize_product(product)

        metadata = create_metadata(source, search_query, page_number)

        record = {
            "metadata": metadata,
            "product": product,
        }
        records.append(record)

    return records


def upsert_records(records, file_path="noon_data.json"):
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

        # Normalize URL (important for Noon)
        url = url.split("?")[0].split("#")[0].strip()
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


# Usage
driver = create_brave_driver(
    headless=False,
    disable_images=True,
    disable_notifications=True,
    mute_audio=True,
    incognito=True,
)

noon_url = "http://noon.com/egypt-en/"

# Get user input
search_query = input("Enter product to search: ").strip()
pages_to_scrape = int(input("Enter number of pages to scrape: ").strip())


driver.get(noon_url)

wait = WebDriverWait(driver, 10)


driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(2)


products = get_all_products(driver, wait, query=search_query, pages=pages_to_scrape)


print("Total products:", len(products))

# Get extra info for each product (limit first if testing)
for product in products:
    extra = get_product_extra_info(driver, wait, product["link"])
    product.update(extra)


records = build_records(
    products=products,
    source="noon",
    search_query=search_query,
    page_number=1,  # or page if you build per page
)

upsert_records(records)
