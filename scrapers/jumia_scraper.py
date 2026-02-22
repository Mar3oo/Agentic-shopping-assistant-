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


def get_products(driver):
    """
    Extract product title, price, and link from the current results page.
    Returns a list of dictionaries.
    """

    products = []

    # Get all product cards
    items = driver.find_elements(By.CSS_SELECTOR, "article.prd")

    for item in items:
        try:
            title = item.find_element(By.CSS_SELECTOR, "h3").text
        except:
            title = None

        try:
            price = item.find_element(By.CSS_SELECTOR, "div.prc").text
        except:
            price = None

        try:
            link = item.find_element(By.CSS_SELECTOR, "a.core").get_attribute("href")
        except:
            link = None

        products.append({"title": title, "price": price, "link": link})

    return products


def get_all_products(driver, wait, query, pages=3):
    all_products = []

    for page in range(1, pages + 1):
        url = f"https://www.jumia.com.eg/catalog/?q={query}&page={page}"
        print(f"Scraping page {page}")
        print("URL:", url)

        driver.get(url)

        # Wait for products to load
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "article.prd")))

        products = get_products(driver)
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
            By.CSS_SELECTOR, "div.markup.-mhm.-pvl.-oxa.-sc"
        )
        details_text = details_container.text
    except:
        pass

    # Seller score
    try:
        seller_score = driver.find_element(By.CSS_SELECTOR, "bdo.-m.-prxs").text
    except:
        pass

    # Category / Breadcrumb

    try:
        breadcrumbs = driver.find_elements(By.CSS_SELECTOR, "a.cbs")
        category = ",".join([b.text for b in breadcrumbs if b.text])
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
    # Normalize URL (remove tracking params)
    if product.get("link"):
        product["link"] = product["link"].split("?")[0]

    # Convert price to float if possible
    if product.get("price"):
        price = product["price"].replace("EGP", "").replace(",", "").strip()
        try:
            product["price"] = float(price)
        except:
            pass

    # Convert seller score (e.g., "58%") to float
    if product.get("seller_score"):
        score = product["seller_score"].replace("%", "").strip()
        try:
            product["seller_score"] = float(score) / 100
        except:
            pass

    return product


def create_metadata(source, search_query, page_number):
    return {
        "source": source,
        "scraped_at": datetime.now().isoformat(),
        "search_query": search_query,
        "page_number": page_number,
    }


def build_records(products, source, search_query, page_number):
    metadata = create_metadata(source, search_query, page_number)
    records = []

    for product in products:
        product = normalize_product(product)

        record = {
            "metadata": metadata,
            "product": product,
        }
        records.append(record)

    return records


def upsert_records(records, file_path="jumia_data.json"):
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


# Usage
driver = create_brave_driver(
    headless=False,
    disable_images=True,
    disable_notifications=True,
    mute_audio=True,
    incognito=True,
)

jumia_url = "https://www.jumia.com.eg/"

# Get user input
search_query = input("Enter product to search: ").strip()
pages_to_scrape = int(input("Enter number of pages to scrape: ").strip())


driver.get(jumia_url)

wait = WebDriverWait(driver, 10)

# Wait until the popup button appears and is clickable
popup_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "cls")))

popup_btn.click()

products = get_all_products(driver, wait, query=search_query, pages=pages_to_scrape)


print("Total products:", len(products))

# Get extra info for each product (limit first if testing)
for product in products:
    extra = get_product_extra_info(driver, wait, product["link"])
    product.update(extra)


records = build_records(
    products=products,
    source="jumia",
    search_query=search_query,
    page_number=1,  # or page if you build per page
)

upsert_records(records)
