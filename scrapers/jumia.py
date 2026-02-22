from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import random


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
