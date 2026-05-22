import os
import requests

def validate_env():
    required = ["TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID", "SERPAPI_KEY"]
    missing = [r for r in required if not os.environ.get(r)]
    if missing:
        raise RuntimeError(f"缺少環境變數: {', '.join(missing)}")

validate_env()
TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
SERPAPI_KEY = os.environ["SERPAPI_KEY"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

# ==================== 任務 A：泰國曼谷（強行簡化發送） ====================
def check_thailand():
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_flights", "departure_id": "HKG", "arrival_id": "BKK",
        "outbound_date": "2026-07-17", "return_date": "2026-07-20",
        "currency": "HKD", "hl": "zh-tw", "gl": "hk", "api_key": SERPAPI_KEY
    }
    try:
        res = requests.get(url, params=params).json()
        price = (res.get("best_flights", []) + res.get("other_flights", [{}]))[0].get("price", "未知")
        send_telegram(f"🇹🇭 泰國特工回報：\n📅 7月17-20日\n💵 最低價：${price} HKD")
    except Exception as e:
        send_telegram(f"❌ 查泰國失敗: {e}")

# ==================== 任務 B：台東單程（分拆上市，獨立發送！） ====================
def check_taiwan_tokyo_independent():
    legs = [
        {"name": "1. 💒 香港 ➡️ 台北", "dep": "HKG", "arr": "TPE", "date": "2026-10-24"},
        {"name": "2. 🗼 台北 ➡️ 東京", "dep": "TPE", "arr": "TYO", "date": "2026-10-25"},
        {"name": "3. 🛍️ 東京 ➡️ 香港", "dep": "TYO", "arr": "HKG", "date": "2026-10-28"}
    ]
    
    send_telegram("🚀 💒 【10月台東婚禮特工】正在獨立為你查詢三段單程...")
    
    for leg in legs:
        url = "https://serpapi.com/search"
        params = {
            "engine": "google_flights",
            "departure_id": leg["dep"],
            "arrival_id": leg["arr"],
            "outbound_date": leg["date"],
            "currency": "HKD", "hl": "zh-tw", "gl": "hk",
            "type": "2", # 單程
            "api_key": SERPAPI_KEY
        }
        try:
            res = requests.get(url, params=params).json()
            flights = res.get("best_flights", []) + res.get("other_flights", [])
            if flights:
                p = flights[0].get("price", "未知")
                airline = flights[0].get("flights", [{}])[0].get("airline", "未知航空")
                dep_time = flights[0].get("flights", [{}])[0].get("departure_time", "未知時間")
                
                msg = f"✈️ {leg['name']}\n📅 日期：{leg['date']}\n💵 單程票價：${p} HKD\n⏰ 時間：{dep_time} ({airline})"
                send_telegram(msg)
            else:
                send_telegram(f"⚠️ {leg['name']} 查不到當天航班資料")
        except Exception as e:
            send_telegram(f"❌ {leg['name']} 查詢出錯: {e}")

if __name__ == "__main__":
    check_thailand()
    check_taiwan_tokyo_independent()
