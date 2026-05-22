import os
import re
from pathlib import Path
from urllib.parse import urlparse

import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "").strip()

DEPARTURE_ID = "HKG"
ARRIVAL_ID = "NRT"
DATE_PAIRS = [
    ("2026-06-15", "2026-06-20"),
    ("2026-07-10", "2026-07-15"),
    ("2026-08-14", "2026-08-19"),
]


def to_number(value):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        digits = re.sub(r"[^\d.]", "", value)
        if digits:
            return float(digits)
    return None


def pick_platform(booking_option):
    platform = booking_option.get("platform")
    if platform:
        return platform
    link = booking_option.get("link", "")
    if not link:
        return "未提供平台"
    host = urlparse(link).netloc
    return host or "未提供平台"


def find_lowest_roundtrip(data):
    candidates = []
    flights = data.get("best_flights", []) + data.get("other_flights", [])

    for item in flights:
        price_value = to_number(item.get("price"))
        if price_value is None:
            continue

        segments = item.get("flights", [])
        airline_names = [seg.get("airline", "").strip() for seg in segments if seg.get("airline")]
        airline_text = " / ".join(dict.fromkeys(airline_names)) if airline_names else "未提供航空公司"

        booking_options = item.get("booking_options", [])
        platform_text = pick_platform(booking_options[0]) if booking_options else "未提供平台"

        candidates.append(
            {
                "price_raw": item.get("price", "未提供"),
                "price_value": price_value,
                "airline": airline_text,
                "platform": platform_text,
            }
        )

    if not candidates:
        return None
    return min(candidates, key=lambda x: x["price_value"])


def fetch_google_flights(outbound_date, return_date):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_flights",
        "departure_id": DEPARTURE_ID,
        "arrival_id": ARRIVAL_ID,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "currency": "HKD",
        "hl": "zh-TW",
        "api_key": SERPAPI_KEY,
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    response = requests.post(url, json=payload, timeout=15)
    response.raise_for_status()
    result = response.json()
    if not result.get("ok"):
        raise RuntimeError(f"Telegram 回傳失敗: {result}")


def format_hkd(value):
    return f"HKD {value:,.2f}"


def get_price_file(outbound_date, return_date):
    outbound_tag = outbound_date.replace("-", "")
    return_tag = return_date.replace("-", "")
    filename = f"price_{outbound_tag}_{return_tag}.txt"
    return Path(__file__).with_name(filename)


def read_last_price(price_file):
    if not price_file.exists():
        return None
    raw = price_file.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    return float(raw)


def write_last_price(price_file, price_value):
    price_file.write_text(f"{price_value:.2f}", encoding="utf-8")


def validate_env():
    required = {
        "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
        "SERPAPI_KEY": SERPAPI_KEY,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"缺少環境變數: {joined}")


def main():
    validate_env()

    for outbound_date, return_date in DATE_PAIRS:
        data = fetch_google_flights(outbound_date, return_date)
        best = find_lowest_roundtrip(data)

        if not best:
            print(f"{outbound_date} 至 {return_date}: 未找到可比較的價格資料，保持安靜")
            continue

        price_file = get_price_file(outbound_date, return_date)
        latest_price = best["price_value"]
        old_price = read_last_price(price_file)

        if old_price is None:
            write_last_price(price_file, latest_price)
            print(f"{outbound_date} 至 {return_date}: 已建立初始價格紀錄，不發送通知")
            continue

        if latest_price < old_price:
            cheaper_amount = old_price - latest_price
            write_last_price(price_file, latest_price)
            message = (
                "機票降價通知！\n"
                f"路線: {DEPARTURE_ID} -> {ARRIVAL_ID}\n"
                f"日期: {outbound_date} 至 {return_date}\n"
                f"舊價錢: {format_hkd(old_price)}\n"
                f"新價錢: {best['price_raw']}\n"
                f"便宜了: {format_hkd(cheaper_amount)}\n"
                f"航空公司: {best['airline']}\n"
                f"平台: {best['platform']}"
            )
            send_telegram(message)
            print(f"{outbound_date} 至 {return_date}: 已發送降價 Telegram 通知。")
            continue

        print("價格未變或上升，保持安靜")


if __name__ == "__main__":
    main()
