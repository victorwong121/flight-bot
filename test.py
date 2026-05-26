import os
import re
from pathlib import Path
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "").strip()

SERPAPI_URL = "https://serpapi.com/search.json"
SCRIPT_DIR = Path(__file__).resolve().parent

# ==================== 參數設定 ====================
# 任務 A：曼谷雙機場來回監測（直航）
THAI_DATE_PAIRS = [
    ("2026-07-03", "2026-07-06"),
    ("2026-07-17", "2026-07-20"),
    ("2026-07-24", "2026-07-27"),
]
THAI_FROM = "HKG"
THAI_AIRPORTS = ["BKK", "DMK"]

# 任務 B：台北婚禮雙城連線（三段單程，全部直航）
MULTI_CITY_SEGMENTS = [
    {"name": "1. 💒 飲衫首航：香港(HKG) ➡️ 台北(TPE)", "date": "2026-10-24", "from": "HKG", "to": "TPE", "daytime_only": True},
    {"name": "2. 🗼 東京度假：台北(TPE) ➡️ 東京成田(NRT)", "date": "2026-10-25", "from": "TPE", "to": "NRT", "daytime_only": False},
    {"name": "3. 🛍️ 凱旋回港：東京成田(NRT) ➡️ 香港(HKG)", "date": "2026-10-28", "from": "NRT", "to": "HKG", "daytime_only": False},
]

# ==================== 工具函數 ====================
def to_number(value):
    if isinstance(value, (int, float)): return float(value)
    if isinstance(value, str):
        digits = re.sub(r"[^\d.]", "", value)
        if digits: return float(digits)
    return None

def format_hkd(value):
    return f"HKD {value:,.0f}"

def extract_departure_time(flights):
    if not flights: return "未提供"
    time_text = flights[0].get("departure_airport", {}).get("time")
    return str(time_text).strip() if time_text else "未提供"

def parse_hour_from_text(time_text):
    if not time_text: return None
    text = str(time_text).strip().lower()
    m = re.search(r"(\d{1,2})(?::\d{2})?", text)
    if not m
