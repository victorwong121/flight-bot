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

THAI_DATE_PAIRS = [
    ("2026-07-03", "2026-07-06"),
    ("2026-07-17", "2026-07-20"),
    ("2026-07-24", "2026-07-27"),
]
THAI_FROM = "HKG"
THAI_AIRPORTS = ["BKK", "DMK"]

# ⭐ 台北東京大解鎖：台北改查 TPE（桃園）和 TSA（松山），東京改查 NRT（成田）和 HND（羽田）
MULTI_CITY_SEGMENTS = [
    {"name": "1. 💒 飲衫首航：香港 (HKG) ➡️ 台北 (TPE)", "date": "2026-10-24", "from": "HKG", "to": "TPE", "daytime_only": True},
    {"name": "2. 🗼 東京度假：台北 (TPE) ➡️ 東京成田 (NRT)", "date": "2026-10-25", "from": "TPE", "to": "NRT", "daytime_only": False},
    {"name": "3. 🛍️ 凱旋回港：東京成田 (NRT) ➡️ 香港 (HKG)", "date": "2026-10-28", "from": "NRT", "to": "HKG", "daytime_only": False},
]

def to_number(value):
    if isinstance(value, (int, float)): return float(value)
    if isinstance(value, str):
        digits = re.sub(r"[^\d.]", "", value)
        if digits: return float(digits)
    return None

def format_hkd(value):
    return f"HKD {value:,.0f}"

def pick_platform(booking_option):
    platform = booking_option.get("platform")
    if platform: return platform
    link = booking_option.get("link", "")
    if not link: return "未提供平台"
    return urlparse(link).netloc or "未提供平台"

def extract_departure_time(flights):
    if not flights: return "未提供"
    time_text = flights[0].get("departure_airport", {}).get("time")
    return str(time_text).strip() if time_text else "未提供"

def is_daytime_departure(time_text):
    if not time_text: return False
    lowered = str(time_text).lower()
    blocked_tokens = ["下午", "pm", "晚上", "夜晚", "傍晚"]
    if any(token in lowered for token in blocked_tokens): return False
    return True

def serpapi_request(params):
    response = requests.get(SERPAPI_URL, params=params, timeout=45)
    data = response.json()
    if data.get("error"): raise RuntimeError(f"SerpApi 錯誤: {data['error']}")
    return data

def fetch_oneway_with_fallback(departure_id, arrival_id, outbound_date):
    # 嘗試強行直航
    params = {
        "engine": "google_flights", "type": "2",
        "departure_id": departure_id, "arrival_id": arrival_id,
        "outbound_date": outbound_date, "outbound_stops": "0",
        "currency": "HKD", "hl": "zh-TW", "api_key": SERPAPI_KEY,
    }
    try:
        data = serpapi_request(params)
        if data.get("best_flights") or data.get("other_flights"):
            return data, False
    except:
        pass

    # 降級寬鬆搜尋
    params.pop("outbound_stops", None)
    return serpapi_request(params), True

def is_direct_itinerary(item):
    if "stops" in item and to_number(item.get("stops")) == 0: return True
    if item.get("layovers"): return False
    flights = item.get("flights", [])
    if not flights: return False
    if len(flights) > 1: return False
    return to_number(flights[0].get("stops", 0)) == 0

def extract_lowest_flight(data, daytime_only=False, enforce_direct=False):
    candidates = []
    flights = data.get("best_flights", []) + data.get("other_flights", [])
    for item in flights:
        if enforce_direct and not is_direct_itinerary(item): continue
        price_value = to_number(item.get("price"))
        if price_value is None: continue
        segments = item.get("flights", [])
        departure_time = extract_departure_time(segments)
        if daytime_only and not is_daytime_departure(departure_time): continue
        airline_names = [seg.get("airline", "").strip() for seg in segments if seg.get("airline")]
        airline_text = " / ".join(dict.fromkeys(airline_names)) if airline_names else "未知航空"
        booking_options = item.get("booking_options", [])
        platform_text = pick_platform(booking_options[0]) if booking_options else "未提供平台"
        candidates.append({
            "price_value": price_value, "airline": airline_text,
            "platform": platform_text, "departure_time": departure_time,
        })
    return min(candidates, key=lambda x: x["price_value"]) if candidates else None

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=20)

# ==================== 任務 A：泰國曼谷來回 ====================
def run_task_thailand():
    for outbound_date, return_date in THAI_DATE_PAIRS:
        contenders = []
        for airport in THAI_AIRPORTS:
            try:
                # 這裡直接用簡化版直航查詢
                params = {
                    "engine": "google_flights", "departure_id": THAI_FROM, "arrival_id": airport,
                    "outbound_date": outbound_date, "return_date": return_date,
                    "outbound_stops": "0", "return_stops": "0", "currency": "HKD", "hl": "zh-TW", "api_key": SERPAPI_KEY,
                }
                data = serpapi_request(params)
                best = extract_lowest_flight(data, daytime_only=False)
                if best:
                    best["airport"] = airport
                    contenders.append(best)
            except:
                pass
        if contenders:
            winner = min(contenders, key=lambda x: x["price_value"])
            msg = (
                "🇹🇭 曼谷雙機場巡邏回報\n"
                f"📅 日期: {outbound_date} → {return_date}\n"
                f"🛫 航線: {THAI_FROM} → {winner['airport']}\n"
                f"🏆 最低直航價: {format_hkd(winner['price_value'])}\n"
                f"⏰ 出發時間: {winner['departure_time']}\n"
                f"✈️ 航空公司: {winner['airline']}"
            )
            send_telegram(msg)

# ==================== 任務 B：台北喜酒多城連線（暴力單程拆開轟炸版） ====================
def run_task_taipei_tokyo_combo():
    send_telegram("🚀 💒 【10月台北喜酒度假任務】獨立起飛...")
    total_price = 0
    all_success = True
    
    for seg in MULTI_CITY_SEGMENTS:
        try:
            data, used_fallback = fetch_oneway_with_fallback(seg["from"], seg["to"], seg["date"])
            best = extract_lowest_flight(data, daytime_only=seg["daytime_only"], enforce_direct=used_fallback)
            
            if best:
                total_price += best["price_value"]
                msg = (
                    f"✈️ {seg['name']}\n"
                    f"📅 日期: {seg['date']}\n"
                    f"💵 唯一直航最平: {format_hkd(best['price_value'])}\n"
                    f"⏰ 出發時間: {best['departure_time']}\n"
                    f"🏨 航空公司: {best['airline']}"
                )
                send_telegram(msg) # 👈 查到一段，立刻發一段！絕對不裝死！
            else:
                all_success = False
                send_telegram(f"⚠️ {seg['name']} 查不到符合直航/時間要求的航班資料。")
        except Exception as e:
            all_success = False
            send_telegram(f"❌ {seg['name']} 後台查詢出錯: {e}")

    if all_success:
        send_telegram(f"🧾 💒 10月多城總預算拼圖完成！\n💰 三段直航單程總價：{format_hkd(total_price)}")

def main():
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID or not SERPAPI_KEY: return
    run_task_thailand()
    run_task_taipei_tokyo_combo()

if __name__ == "__main__":
    main()
