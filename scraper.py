from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random


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

    # Small delay (important to avoid blocking)
    time.sleep(random.uniform(1, 2))

    # Close tab
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

    return {"details_text": details_text, "seller_score": seller_score}


# Usage
driver = create_brave_driver(
    headless=False,
    disable_images=True,
    disable_notifications=True,
    mute_audio=True,
    incognito=True,
)

jumia_url = "https://www.jumia.com.eg/"

driver.get(jumia_url)

wait = WebDriverWait(driver, 10)

# Wait until the popup button appears and is clickable
popup_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "cls")))

popup_btn.click()

products = get_all_products(driver, wait, query="iphone", pages=1)

print("Total products:", len(products))

for product in products[:3]:
    extra = get_product_extra_info(driver, wait, product["link"])
    product.update(extra)

for p in products[:3]:
    print(p)
