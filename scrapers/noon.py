from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import re
from urllib.parse import quote_plus


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
