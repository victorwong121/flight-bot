import os
import json
import requests

# 1. 安全檢查：確保雲端保險箱有密碼
def validate_env():
    required = ["TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID", "SERPAPI_KEY"]
    missing = [r for r in required if not os.environ.get(r)]
    if missing:
        raise RuntimeError(f"缺少環境變數: {', '.join(missing)}")

validate_env()

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"] if "CHAT_ID" in os.environ else os.environ["TELEGRAM_CHAT_ID"]
SERPAPI_KEY = os.environ["SERPAPI_KEY"]

# 2. 設定監測目標：泰國曼谷雙機場（BKK & DMK）
DEPARTURE = "HKG"
# 我們定義 3 個黃金 4日3夜 組合
FLIGHT_COMBOS = [
    {"outbound": "2026-07-03", "return": "2026-07-06"},
    {"outbound": "2026-07-17", "return": "2026-07-20"},
    {"outbound": "2026-07-24", "return": "2026-07-27"}
]
AIRPORTS = ["BKK", "DMK"]

def format_hkd(val):
    return f"${val:,.0f} HKD" if val else "未知"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    res = requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    return res.status_code == 200

def check_flights():
    print("🛫 泰國雙機場密集降價雷達啟動...")
    
    for combo in FLIGHT_COMBOS:
        out_date = combo["outbound"]
        ret_date = combo["return"]
        
        lowest_price = float('inf')
        best_flight = None
        
        # 同時掃描 BKK 和 DMK
        for apt in AIRPORTS:
            url = "https://serpapi.com/search"
            params = {
                "engine": "google_flights",
                "departure_id": DEPARTURE,
                "arrival_id": apt,
                "outbound_date": out_date,
                "return_date": ret_date,
                "currency": "HKD",
                "hl": "zh-tw",
                "gl": "hk",
                "api_key": SERPAPI_KEY
            }
            
            try:
                response = requests.get(url, params=params).json()
                flights = response.get("best_flights", []) + response.get("other_flights", [])
                
                for f in flights:
                    p = f.get("price")
                    if p and p < lowest_price:
                        lowest_price = p
                        best_flight = {
                            "price_raw": p,
                            "airport": apt,
                            "airline": f.get("flights", [{}])[0].get("airline", "未知航空"),
                            "platform": "Google Flights"
                        }
            except Exception as e:
                print(f"查詢 {apt} 失敗: {e}")
        
        if best_flight:
            # 檔案紀錄命名，加上機場區分
            price_file = f"last_price_{out_date}_{ret_date}.txt"
            old_price = None
            if os.path.exists(price_file):
                with open(price_file, "r") as f:
                    try: old_price = float(f.read().strip())
                    except: pass
            
            # 第一次跑，強迫發送通知，打破「保持安靜」魔咒！
            if old_price is None:
                with open(price_file, "w") as f:
                    f.write(str(lowest_price))
                
                message = (
                    f"🔔 泰國雙機場動態首報！\n\n"
                    f"📅 日期：{out_date} 至 {ret_date}\n"
                    f"✈️ 航線：香港 (HKG) -> 曼谷 ({best_flight['airport']})\n"
                    f"💵 當前最低價：{format_hkd(lowest_price)}\n"
                    f"🏨 航空公司：{best_flight['airline']}\n"
                    f"🔍 🔎 機械人已開始為你 24 小時死守此日子！"
                )
                send_telegram(message)
                print(f"{out_date} 初始紀錄已建立，已強制發送 Telegram 通知！")
                
            elif lowest_price < old_price:
                cheaper = old_price - lowest_price
                with open(price_file, "w") as f:
                    f.write(str(lowest_price))
                    
                message = (
                    f"🔥 ✈️ 泰國機票降價大警告！！！\n\n"
                    f"📅 日期：{out_date} 至 {ret_date}\n"
                    f"✈️ 航線：香港 (HKG) -> 曼谷 ({best_flight['airport']})\n"
                    f"📉 舊價錢：{format_hkd(old_price)}\n"
                    f"💥 新價錢：{format_hkd(lowest_price)}\n"
                    f"🎉 慳咗：{format_hkd(cheaper)}\n"
                    f"🏨 航空公司：{best_flight['airline']}\n"
                    f"👉 快啲去搶飛啦！"
                )
                send_telegram(message)
                print(f"{out_date} 發現降價，已發送報警通知！")
            else:
                print(f"{out_date} 價格未變或上升，保持安靜。")

if __name__ == "__main__":
    check_flights()
