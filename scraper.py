from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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
