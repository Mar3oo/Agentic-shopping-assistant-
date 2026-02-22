from scrapers.base import create_brave_driver, build_records, upsert_records
from scrapers import jumia, noon
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time

site = input("Choose site (jumia/noon): ").strip().lower()
query = input("Enter product: ")
pages = int(input("Pages: "))

driver = create_brave_driver(incognito=True)
wait = WebDriverWait(driver, 10)

if site == "jumia":
    driver.get("https://www.jumia.com.eg/")

    # Wait until the popup button appears and is clickable
    popup_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "cls")))

    popup_btn.click()

    products = jumia.get_all_products(driver, wait, query, pages)

    for p in products:
        p.update(jumia.get_product_extra_info(driver, wait, p["link"]))

    records = build_records(products, "jumia", query, 1, jumia.normalize_product)
    upsert_records(records, "data/jumia.json")

elif site == "noon":
    driver.get("https://www.noon.com/egypt-en/")

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    products = noon.get_all_products(driver, wait, query, pages)

    for p in products:
        p.update(noon.get_product_extra_info(driver, wait, p["link"]))

    records = build_records(products, "noon", query, 1, noon.normalize_product)
    upsert_records(records, "data/noon.json")

else:
    print("Invalid site")
