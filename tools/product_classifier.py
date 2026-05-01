import re


CATEGORY_KEYWORDS = {
    # ---------- AUDIO DEVICES ----------
    "wireless_earbuds": [
        "wireless earbuds",
        "true wireless earbuds",
        "tws earbuds",
        "airpods",
    ],
    "earbuds": ["earbuds", "in-ear headphones", "in-ear earphones"],
    "headphones": ["headphones", "over-ear headphones", "on-ear headphones"],
    "gaming_headset": [
        "gaming headset",
        "gaming headphones",
        "gaming headset with mic",
    ],
    "earphones": ["earphones", "wired earphones", "in-ear earphones"],
    "microphone": ["microphone", "usb microphone", "studio microphone"],
    "speaker": ["speaker", "bluetooth speaker", "portable speaker"],
    "soundbar": ["soundbar", "tv soundbar"],
    "subwoofer": ["subwoofer", "bass speaker"],
    # ---------- COMPUTERS ----------
    "gaming_laptop": ["gaming laptop", "gaming notebook"],
    "laptop": ["laptop", "notebook", "ultrabook", "macbook"],
    "desktop": ["desktop pc", "desktop computer", "tower pc"],
    "all_in_one_pc": ["all in one pc", "aio computer"],
    "mini_pc": ["mini pc", "compact pc"],
    "workstation": ["workstation pc", "workstation computer"],
    # ---------- COMPUTER COMPONENTS ----------
    "graphics_card": ["gpu", "graphics card", "video card", "rtx", "radeon"],
    "processor": ["cpu", "processor", "intel core", "amd ryzen"],
    "motherboard": ["motherboard", "mainboard"],
    "ram": ["ram", "memory", "ddr4", "ddr5"],
    "power_supply": ["power supply", "psu"],
    "pc_case": ["pc case", "computer case", "gaming case"],
    "cooling_system": ["cpu cooler", "liquid cooler", "cooling fan"],
    # ---------- STORAGE ----------
    "external_hard_drive": ["external hard drive", "external hdd"],
    "hard_drive": ["hard drive", "hdd"],
    "ssd": ["ssd", "solid state drive", "nvme", "m.2 ssd"],
    "usb_flash_drive": ["usb flash drive", "flash drive", "pen drive"],
    "memory_card": ["sd card", "micro sd", "memory card"],
    # ---------- MOBILE DEVICES ----------
    "smartwatch": ["smartwatch", "apple watch", "galaxy watch"],
    "fitness_tracker": ["fitness tracker", "fitness band", "smart band"],
    "tablet": ["tablet", "ipad", "android tablet"],
    "e_reader": ["e reader", "kindle", "ebook reader"],
    "smartphone": ["smartphone", "iphone", "android phone", "mobile phone"],
    "feature_phone": ["feature phone", "button phone"],
    # ---------- INPUT DEVICES ----------
    "mechanical_keyboard": ["mechanical keyboard", "gaming keyboard"],
    "keyboard": ["keyboard", "wireless keyboard"],
    "gaming_mouse": ["gaming mouse"],
    "mouse": ["mouse", "wireless mouse"],
    "trackpad": ["trackpad", "touchpad"],
    "drawing_tablet": ["drawing tablet", "graphics tablet", "pen tablet"],
    # ---------- DISPLAYS ----------
    "gaming_monitor": ["gaming monitor", "144hz monitor", "240hz monitor"],
    "monitor": ["monitor", "computer monitor"],
    "tv": ["tv", "smart tv", "television"],
    "projector": ["projector", "home projector"],
    # ---------- NETWORKING ----------
    "router": ["router", "wifi router"],
    "modem": ["modem"],
    "network_switch": ["network switch", "ethernet switch"],
    "wifi_adapter": ["wifi adapter", "wireless adapter"],
    # ---------- GAMING ----------
    "gaming_console": ["gaming console", "playstation", "xbox", "nintendo switch"],
    "vr_headset": ["vr headset", "virtual reality headset"],
    "gaming_controller": ["gaming controller", "gamepad"],
    # ---------- ACCESSORIES ----------
    "webcam": ["webcam", "usb webcam"],
    "laptop_stand": ["laptop stand"],
    "dock_station": ["dock station", "docking station"],
    "usb_hub": ["usb hub"],
    "charging_adapter": ["charger", "charging adapter", "power adapter"],
    "power_bank": ["power bank", "portable charger"],
    "cable": ["usb cable", "hdmi cable", "charging cable"],
    "phone_case": ["phone case", "mobile case"],
    "screen_protector": ["screen protector"],
}


def classify_product_type(search_query, category):

    if not search_query and not category:
        return "other"

    text = f"{search_query} {category}".lower()

    text = text.replace("-", " ")
    text = text.replace("_", " ")

    # remove punctuation
    text = re.sub(r"[^\w\s]", " ", text)

    words = text.split()

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in words:
                return category

    return "other"
