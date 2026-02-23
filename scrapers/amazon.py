import time
import random
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote_plus


def get_products(driver):
    products = []

    # Wait for product cards
    items = wait(driver, 10).until(
        EC.presence_of_all_elements_located(
            (By.XPATH, '//div[contains(@class,"s-result-item") and @data-asin]')
        )
    )

    print(f"Products found: {len(items)}")

    for item in items:
        try:
            title = item.find_element(
                By.CSS_SELECTOR,
                "h2.a-size-base-plus.a-spacing-none.a-color-base.a-text-normal span",
            ).text
        except:
            title = None

        # Price
        try:
            price_whole = item.find_element(By.CSS_SELECTOR, "span.a-price-whole").text
            price_fraction = item.find_element(
                By.CSS_SELECTOR, "span.a-price-fraction"
            ).text
            price = price_whole + "." + price_fraction
        except:
            price = None

        # Link
        try:
            link = item.find_element(
                By.CSS_SELECTOR,
                "a.a-link-normal.s-line-clamp-4.s-link-style.a-text-normal",
            ).get_attribute("href")
        except:
            link = None
        if link:  # avoid empty cards
            products.append({"title": title, "price": price, "link": link})

    return products


def get_all_products(driver, wait, query, pages=3):
    all_products = []

    query_encoded = quote_plus(query)

    for page in range(1, pages + 1):
        url = f"https://www.amazon.eg/s?k={query_encoded}&page={page}"
        print(f"Scraping page {page}")
        print("URL:", url)

        driver.get(url)

        # Wait for product cards to load
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[contains(@class,"s-result-item") and @data-asin]')
            )
        )

        # # Amazon sometimes lazy-loads results
        # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # time.sleep(2)

        products = get_products(driver)
        print("Products found:", len(products))

        all_products.extend(products)

        # Small delay between pages (important for Amazon)
        time.sleep(3)

    return all_products


def get_product_extra_info(driver, wait, link):
    # Open new tab
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])

    driver.get(link)

    # Wait for main product title (better than waiting for body)
    wait.until(EC.presence_of_element_located((By.ID, "productTitle")))

    details_text = None
    seller_score = None
    category = None

    try:
        details_text = driver.find_element(By.CSS_SELECTOR, "#productDescription").text
    except:
        pass

    # Rating (Amazon shows rating like "4.5 out of 5 stars")
    try:
        seller_score = driver.find_element(
            By.CSS_SELECTOR, "span.a-size-small.a-color-base"
        ).text
    except:
        pass

    # Category / Breadcrumb
    try:
        breadcrumbs = driver.find_elements(
            By.CSS_SELECTOR, "#wayfinding-breadcrumbs_feature_div ul li a"
        )
        category = ",".join([b.text.strip() for b in breadcrumbs if b.text.strip()])
    except:
        pass

    # Small delay (important for Amazon)
    time.sleep(random.uniform(1.5, 2.5))

    # Close tab
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

    return {
        "details_text": details_text,
        "seller_score": seller_score,
        "category": category,
    }


import re


def normalize_product(product):

    # ---------- URL (extract ASIN) ----------
    if product.get("link"):
        url = product["link"]

        # Extract ASIN from /dp/ASIN
        match = re.search(r"/dp/([A-Z0-9]{10})", url)
        if match:
            asin = match.group(1)
            product["link"] = f"https://www.amazon.eg/dp/{asin}"
        else:
            # fallback: remove parameters
            url = url.split("?")[0].split("#")[0]
            product["link"] = url.strip()

    # ---------- Price ----------
    if product.get("price"):
        price_text = product["price"]

        # Remove commas and any non-numeric except dot
        price_text = re.sub(r"[^\d.]", "", price_text)

        try:
            product["price"] = float(price_text)
        except:
            product["price"] = None

    # ---------- Seller score (convert to 0–1 scale) ----------
    if product.get("seller_score"):
        score_text = product["seller_score"]

        # Extract number (handles "4.5 out of 5 stars" or "4.5")
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
