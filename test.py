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
    if not m: return None
    hour = int(m.group(1))
    if any(x in text for x in ["pm", "下午", "晚上", "夜晚", "傍晚"]) and hour < 12: hour += 12
    if any(x in text for x in ["am", "上午", "凌晨", "清晨"]) and hour == 12: hour = 0
    return hour

def is_daytime_departure(time_text):
    if not time_text: return False
    if any(token in str(time_text).lower() for token in ["下午", "pm", "晚上", "夜晚", "傍晚"]): return False
    hour = parse_hour_from_text(time_text)
    return hour < 16 if hour is not None else False

def serpapi_request(params):
    response = requests.get(SERPAPI_URL, params=params, timeout=45)
    data = response.json()
    if data.get("error"): raise RuntimeError(f"SerpApi 回傳錯誤: {data['error']}")
    return data

def fetch_roundtrip_direct(departure_id, arrival_id, outbound_date, return_date):
    params = {
        "engine": "google_flights", "departure_id": departure_id, "arrival_id": arrival_id,
        "outbound_date": outbound_date, "return_date": return_date,
        "outbound_stops": "0", "return_stops": "0", "currency": "HKD", "hl": "zh-TW", "api_key": SERPAPI_KEY,
    }
    return serpapi_request(params)

def fetch_oneway_with_fallback(departure_id, arrival_id, outbound_date):
    params = {
        "engine": "google_flights", "type": "2", "departure_id": departure_id, "arrival_id": arrival_id,
        "outbound_date": outbound_date, "outbound_stops": "0", "currency": "HKD", "hl": "zh-TW", "api_key": SERPAPI_KEY,
    }
    try:
        data = serpapi_request(params)
        if data.get("best_flights") or data.get("other_flights"): return data, False
    except: pass
    
    # 降級寬鬆搜尋
    params.pop("outbound_stops", None)
    return serpapi_request(params), True

def is_direct_itinerary(item):
    if "stops" in item and to_number(item.get("stops")) == 0: return True
    if item.get("layovers"): return False
    flights = item.get("flights", [])
    if not flights or len(flights) > 1: return False
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

        # ⭐ Trip.com / OTA 深度比價邏輯
        final_price = price_value
        best_platform = "航空公司官網"
        target_otas = ["Trip.com", "永安旅遊", "Mytrip", "Agoda"]
        
        for opt in item.get("booking_options", []):
            opt_name = opt.get("name", "")
            opt_price = to_number(opt.get("price"))
            if opt_price and opt_price < final_price:
                if any(ota in opt_name for ota in target_otas):
                    final_price = opt_price
                    best_platform = f"🔥 {opt_name} 特價"

        airline_names = [seg.get("airline", "").strip() for seg in segments if seg.get("airline")]
        candidates.append({
            "price_value": final_price,
            "airline": " / ".join(dict.fromkeys(airline_names)) if airline_names else "未知航空",
            "platform": best_platform,
            "departure_time": departure_time,
        })

    return min(candidates, key=lambda x: x["price_value"]) if candidates else None

def send_telegram(text):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=20)

def notify_with_price_guard(price_file, current_price, first_msg, drop_msg, label):
    old_price = None
    if price_file.exists():
        raw = price_file.read_text(encoding="utf-8").strip()
        if raw: old_price = float(raw)

    if old_price is None:
        price_file.write_text(f"{current_price:.2f}", encoding="utf-8")
        send_telegram(first_msg)
        print(f"{label}: 首次運行，已發送首報通知。")
        return

    if current_price < old_price:
        price_file.write_text(f"{current_price:.2f}", encoding="utf-8")
        send_telegram(drop_msg(old_price))
        print(f"{label}: 已發送降價通知。")
        return

    print(f"{label}: 價格未變或上升，保持安靜。")

# ==================== 執行任務 ====================
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
            except: pass

        if not contenders: continue
        winner = min(contenders, key=lambda x: x["price_value"])
        price_file = SCRIPT_DIR / f"last_price_th_{outbound_date.replace('-', '')}_{return_date.replace('-', '')}.txt"
        
        first_msg = (
            "🇹🇭 曼谷雙機場首報通知\n"
            f"📅 日期: {outbound_date} → {return_date}\n"
            f"🛫 航線: {THAI_FROM} → {winner['airport']}\n"
            f"🏆 最低直航皇者: {format_hkd(winner['price_value'])}\n"
            f"⏰ 出發時間: {winner['departure_time']}\n"
            f"✈️ 航空公司: {winner['airline']}\n"
            f"🧭 平台: {winner['platform']}"
        )
        drop_msg = lambda old_price: (
            "🚨🇹🇭 曼谷雙機場降價大警告\n"
            f"📅 日期: {outbound_date} → {return_date}\n"
            f"🛫 航線: {THAI_FROM} → {winner['airport']}\n"
            f"💰 舊價: {format_hkd(old_price)} ➡️ 💥 新低價: {format_hkd(winner['price_value'])}\n"
            f"⏰ 出發時間: {winner['departure_time']}\n"
            f"✈️ 航空公司: {winner['airline']}\n"
            f"🧭 平台: {winner['platform']}"
        )
        notify_with_price_guard(price_file, winner["price_value"], first_msg, drop_msg, f"泰國 {outbound_date}")

def run_task_taipei_tokyo_combo():
    segment_results = []
    for seg in MULTI_CITY_SEGMENTS:
        try:
            data, used_fallback = fetch_oneway_with_fallback(seg["from"], seg["to"], seg["date"])
            best = extract_lowest_flight(data, daytime_only=seg.get("daytime_only"), enforce_direct=used_fallback)
            if not best:
                print(f"[台北婚禮] {seg['date']} {seg['from']}->{seg['to']} 無符合條件直航。")
                return
            best.update(seg)
            segment_results.append(best)
        except Exception as exc:
            print(f"[台北婚禮] {seg['date']} {seg['from']}->{seg['to']} 查詢失敗: {exc}")
            return

    total_price = sum(item["price_value"] for item in segment_results)
    # ⭐ 使用全新檔案名稱，確保第一次跑會強制發送 Telegram 通知給你驗收 Trip.com 價格
    price_file = SCRIPT_DIR / "last_price_taipeitokyo_tripcom_final.txt"
    
    seg_text = "\n".join([f"{item['name']} | {format_hkd(item['price_value'])} | {item['departure_time']} | {item['airline']} ({item['platform']})" for item in segment_results])

    first_msg = f"💍🛫 台北婚禮雙城連線首報\n（Trip.com 深度比價版）\n\n{seg_text}\n\n🧾 總預算: {format_hkd(total_price)}"
    drop_msg = lambda old_price: f"🚨💍 台北婚禮降價大警告\n\n{seg_text}\n\n💰 舊總價: {format_hkd(old_price)}\n💥 新總價: {format_hkd(total_price)}\n📉 平咗: {format_hkd(old_price - total_price)}"
    
    notify_with_price_guard(price_file, total_price, first_msg, drop_msg, "台北婚禮雙城連線")

def main():
    if not TELEGRAM_TOKEN or not SERPAPI_KEY: 
        print("缺少環境變數，終止執行")
        return
    run_task_thailand()
    run_task_taipei_tokyo_combo()

if __name__ == "__main__":
    main()
