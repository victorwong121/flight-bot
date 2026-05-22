import os
import re
from pathlib import Path
from urllib.parse import urlparse

import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "").strip()

SERPAPI_URL = "https://serpapi.com/search.json"
SCRIPT_DIR = Path(__file__).resolve().parent

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
    {"date": "2026-10-24", "from": "HKG", "to": "TPE", "daytime_only": True},
    {"date": "2026-10-25", "from": "TPE", "to": "NRT", "daytime_only": False},
    {"date": "2026-10-28", "from": "NRT", "to": "HKG", "daytime_only": False},
]


def to_number(value):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        digits = re.sub(r"[^\d.]", "", value)
        if digits:
            return float(digits)
    return None


def format_hkd(value):
    return f"HKD {value:,.2f}"


def pick_platform(booking_option):
    platform = booking_option.get("platform")
    if platform:
        return platform

    link = booking_option.get("link", "")
    if not link:
        return "未提供平台"
    host = urlparse(link).netloc
    return host or "未提供平台"


def extract_departure_time(flights):
    if not flights:
        return "未提供"
    dep = flights[0].get("departure_airport", {})
    time_text = dep.get("time")
    return str(time_text).strip() if time_text else "未提供"


def parse_hour_from_text(time_text):
    if not time_text:
        return None

    text = str(time_text).strip().lower()
    m = re.search(r"(\d{1,2})(?::\d{2})?", text)
    if not m:
        return None

    hour = int(m.group(1))
    is_pm = (
        "pm" in text
        or "下午" in text
        or "晚上" in text
        or "夜晚" in text
        or "傍晚" in text
    )
    is_am = ("am" in text or "上午" in text or "凌晨" in text or "清晨" in text)

    if is_pm and hour < 12:
        hour += 12
    if is_am and hour == 12:
        hour = 0
    return hour


def is_daytime_departure(time_text):
    if not time_text:
        return False

    lowered = str(time_text).lower()
    blocked_tokens = ["下午", "pm", "晚上", "夜晚", "傍晚"]
    if any(token in lowered for token in blocked_tokens):
        return False

    hour = parse_hour_from_text(time_text)
    if hour is None:
        return False
    return hour < 16


def serpapi_request(params):
    response = requests.get(SERPAPI_URL, params=params, timeout=45)
    response.raise_for_status()
    data = response.json()
    if data.get("error"):
        raise RuntimeError(f"SerpApi 回傳錯誤: {data['error']}")
    return data


def fetch_roundtrip_direct(departure_id, arrival_id, outbound_date, return_date):
    params = {
        "engine": "google_flights",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "outbound_stops": "0",
        "return_stops": "0",
        "currency": "HKD",
        "hl": "zh-TW",
        "api_key": SERPAPI_KEY,
    }
    return serpapi_request(params)


def fetch_oneway_direct(departure_id, arrival_id, outbound_date):
    params = {
        "engine": "google_flights",
        "type": "2",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound_date,
        "outbound_stops": "0",
        "currency": "HKD",
        "hl": "zh-TW",
        "api_key": SERPAPI_KEY,
    }
    return serpapi_request(params)


def extract_lowest_flight(data, daytime_only=False):
    candidates = []
    flights = data.get("best_flights", []) + data.get("other_flights", [])

    for item in flights:
        price_value = to_number(item.get("price"))
        if price_value is None:
            continue

        segments = item.get("flights", [])
        departure_time = extract_departure_time(segments)
        if daytime_only and not is_daytime_departure(departure_time):
            continue

        airline_names = [seg.get("airline", "").strip() for seg in segments if seg.get("airline")]
        airline_text = " / ".join(dict.fromkeys(airline_names)) if airline_names else "未提供航空公司"

        booking_options = item.get("booking_options", [])
        platform_text = pick_platform(booking_options[0]) if booking_options else "未提供平台"

        candidates.append(
            {
                "price_value": price_value,
                "price_raw": item.get("price", "未提供"),
                "airline": airline_text,
                "platform": platform_text,
                "departure_time": departure_time,
            }
        )

    if not candidates:
        return None
    return min(candidates, key=lambda x: x["price_value"])


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    response = requests.post(url, json=payload, timeout=20)
    response.raise_for_status()
    result = response.json()
    if not result.get("ok"):
        raise RuntimeError(f"Telegram 回傳錯誤: {result}")


def read_last_price(path):
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    return float(raw)


def write_last_price(path, value):
    path.write_text(f"{value:.2f}", encoding="utf-8")


def validate_env():
    required = {
        "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
        "SERPAPI_KEY": SERPAPI_KEY,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise RuntimeError(f"缺少環境變數: {', '.join(missing)}")


def notify_with_price_guard(price_file, current_price, first_msg, drop_msg, label):
    old_price = read_last_price(price_file)
    if old_price is None:
        write_last_price(price_file, current_price)
        send_telegram(first_msg)
        print(f"{label}: 首次運行，已發送首報通知。")
        return

    if current_price < old_price:
        write_last_price(price_file, current_price)
        send_telegram(drop_msg(old_price))
        print(f"{label}: 已發送降價通知。")
        return

    print(f"{label}: 價格未變或上升，保持安靜。")


def run_task_thailand():
    for outbound_date, return_date in THAI_DATE_PAIRS:
        contenders = []

        for airport in THAI_AIRPORTS:
            try:
                data = fetch_roundtrip_direct(THAI_FROM, airport, outbound_date, return_date)
                best = extract_lowest_flight(data, daytime_only=False)
                if best:
                    best["airport"] = airport
                    contenders.append(best)
            except Exception as exc:
                print(f"[泰國 {outbound_date}->{return_date} {airport}] 查詢失敗: {exc}")

        if not contenders:
            print(f"[泰國 {outbound_date}->{return_date}] 找不到任何直航可比較資料。")
            continue

        winner = min(contenders, key=lambda x: x["price_value"])
        price_file = SCRIPT_DIR / f"last_price_th_{outbound_date.replace('-', '')}_{return_date.replace('-', '')}.txt"
        label = f"泰國 {outbound_date}->{return_date}"

        first_msg = (
            "🇹🇭 曼谷雙機場首報通知\n"
            f"📅 日期: {outbound_date} → {return_date}\n"
            f"🛫 航線: {THAI_FROM} → {winner['airport']}\n"
            f"🏆 最低直航皇者: {format_hkd(winner['price_value'])}\n"
            f"⏰ 出發時間: {winner['departure_time']}\n"
            f"✈️ 航空公司: {winner['airline']}\n"
            f"🧭 平台: {winner['platform']}"
        )

        def drop_msg(old_price):
            return (
                "🚨🇹🇭 曼谷雙機場降價大警告\n"
                f"📅 日期: {outbound_date} → {return_date}\n"
                f"🛫 航線: {THAI_FROM} → {winner['airport']}\n"
                f"💰 舊價: {format_hkd(old_price)}\n"
                f"💥 新低價: {format_hkd(winner['price_value'])}\n"
                f"📉 便宜了: {format_hkd(old_price - winner['price_value'])}\n"
                f"⏰ 出發時間: {winner['departure_time']}\n"
                f"✈️ 航空公司: {winner['airline']}\n"
                f"🧭 平台: {winner['platform']}"
            )

        notify_with_price_guard(price_file, winner["price_value"], first_msg, drop_msg, label)


def run_task_taipei_tokyo_combo():
    segment_results = []

    for seg in MULTI_CITY_SEGMENTS:
        try:
            data = fetch_oneway_direct(seg["from"], seg["to"], seg["date"])
            best = extract_lowest_flight(data, daytime_only=seg["daytime_only"])
            if not best:
                print(f"[台北婚禮任務] {seg['date']} {seg['from']}->{seg['to']} 無符合條件直航。")
                return
            best["date"] = seg["date"]
            best["from"] = seg["from"]
            best["to"] = seg["to"]
            segment_results.append(best)
        except Exception as exc:
            print(f"[台北婚禮任務] {seg['date']} {seg['from']}->{seg['to']} 查詢失敗: {exc}")
            return

    total_price = sum(item["price_value"] for item in segment_results)
    price_file = SCRIPT_DIR / "last_price_taipeitokyo.txt"
    label = "台北婚禮雙城連線"

    seg_lines = []
    for idx, item in enumerate(segment_results, start=1):
        seg_lines.append(
            f"{idx}. {item['date']} | {item['from']}→{item['to']} | "
            f"{format_hkd(item['price_value'])} | {item['departure_time']} | {item['airline']}"
        )
    seg_text = "\n".join(seg_lines)

    first_msg = (
        "💍🛫 台北婚禮雙城連線首報\n"
        "（三段直航單程拼圖）\n"
        f"{seg_text}\n"
        f"🧾 Total Price: {format_hkd(total_price)}"
    )

    def drop_msg(old_price):
        return (
            "🚨💍 台北婚禮雙城連線降價大警告\n"
            "（三段直航單程拼圖）\n"
            f"{seg_text}\n"
            f"💰 舊總價: {format_hkd(old_price)}\n"
            f"💥 新總價: {format_hkd(total_price)}\n"
            f"📉 便宜了: {format_hkd(old_price - total_price)}"
        )

    notify_with_price_guard(price_file, total_price, first_msg, drop_msg, label)


def main():
    validate_env()
    run_task_thailand()
    run_task_taipei_tokyo_combo()


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as exc:
        print(f"[網絡錯誤] {exc}")
        raise
    except Exception as exc:
        print(f"[程式錯誤] {exc}")
        raise
