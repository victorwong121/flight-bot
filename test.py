import os
import json
import requests

def validate_env():
    required = ["TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID", "SERPAPI_KEY"]
    missing = [r for r in required if not os.environ.get(r)]
    if missing:
        raise RuntimeError(f"缺少環境變數: {', '.join(missing)}")

validate_env()

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"] if "CHAT_ID" in os.environ else os.environ["TELEGRAM_CHAT_ID"]
SERPAPI_KEY = os.environ["SERPAPI_KEY"]

def format_hkd(val):
    return f"${val:,.0f} HKD" if val else "未知"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    res = requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    return res.status_code == 200

# ==================== 任務 A：泰國曼谷（改名徹底刷新） ====================
def check_thailand():
    print("🛫 泰國雙機場密集降價雷達啟動...")
    th_combos = [
        {"outbound": "2026-07-03", "return": "2026-07-06"},
        {"outbound": "2026-07-17", "return": "2026-07-20"},
        {"outbound": "2026-07-24", "return": "2026-07-27"}
    ]
    airports = ["BKK", "DMK"]
    
    for combo in th_combos:
        out_date = combo["outbound"]
        ret_date = combo["return"]
        lowest_price = float('inf')
        best_flight = None
        
        for apt in airports:
            url = "https://serpapi.com/search"
            params = {
                "engine": "google_flights",
                "departure_id": "HKG",
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
                            "airline": f.get("flights", [{}])[0].get("airline", "未知航空")
                        }
            except Exception as e:
                print(f"查詢泰國 {apt} 失敗: {e}")
                
        if best_flight:
            # ⭐ 使用全新未用過的文件名，強行衝破所有雲端舊緩存！
            price_file = f"last_price_thailand_final_{out_date}.txt"
            old_price = None
            if os.path.exists(price_file):
                with open(price_file, "r") as f:
                    try: old_price = float(f.read().strip())
                    except: pass
            
            if old_price is None or lowest_price < old_price:
                with open(price_file, "w") as f:
                    f.write(str(lowest_price))
                
                if old_price is None:
                    msg = f"🔔 泰國雙機場動態首報！\n\n📅 日期：{out_date} 至 {ret_date}\n✈️ 航線：香港 -> 曼谷 ({best_flight['airport']})\n💵 最低價：{format_hkd(lowest_price)}\n🏨 航空：{best_flight['airline']}"
                else:
                    msg = f"🔥 泰國機票降價大警告！！！\n\n📅 日期：{out_date} 至 {ret_date}\n✈️ 航線：香港 -> 曼谷 ({best_flight['airport']})\n📉 舊價：{format_hkd(old_price)} -> 💥 新價：{format_hkd(lowest_price)}\n🏨 航空：{best_flight['airline']}"
                send_telegram(msg)

# ==================== 任務 B：台東雙城大連線（全新文件名，必響版） ====================
def check_taiwan_tokyo():
    print("💒 10月台東婚禮度假特工啟動...")
    legs = [
        {"id": "leg1", "name": "1. 💒 飲衫首航：香港 (HKG) ➡️ 台北 (TPE)", "dep": "HKG", "arr": "TPE", "date": "2026-10-24", "morning_only": True},
        {"id": "leg2", "name": "2. 🗼 東京度假：台北 (TPE) ➡️ 東京 (TYO)", "dep": "TPE", "arr": "TYO", "date": "2026-10-25", "morning_only": False},
        {"id": "leg3", "name": "3. 🛍️ 凱旋回港：東京 (TYO) ➡️ 香港 (HKG)", "dep": "TYO", "arr": "HKG", "date": "2026-10-28", "morning_only": False}
    ]
    
    total_trip_price = 0
    trip_details = []
    all_legs_success = True
    
    for leg in legs:
        url = "https://serpapi.com/search"
        params = {
            "engine": "google_flights",
            "departure_id": leg["dep"],
            "arrival_id": leg["arr"],
            "outbound_date": leg["date"],
            "currency": "HKD",
            "hl": "zh-tw",
            "gl": "hk",
            "type": "2", 
            "api_key": SERPAPI_KEY
        }
        
        try:
            response = requests.get(url, params=params).json()
            flights = response.get("best_flights", []) + response.get("other_flights", [])
            
            leg_lowest = float('inf')
            leg_best = None
            
            for f in flights:
                if leg["morning_only"]:
                    dep_time = f.get("flights", [{}])[0].get("departure_time", "")
                    if "下午" in dep_time or "PM" in dep_time or "晚上" in dep_time:
                        continue
                
                p = f.get("price")
                if p and p < leg_lowest:
                    leg_lowest = p
                    leg_best = {
                        "price": p,
                        "airline": f.get("flights", [{}])[0].get("airline", "未知航空"),
                        "dep_time": f.get("flights", [{}])[0].get("departure_time", "未知時間")
                    }
            
            if leg_best:
                total_trip_price += leg_best["price"]
                trip_details.append(f"{leg['name']}\n💵 票價：{format_hkd(leg_best['price'])}\n⏰ 出發：{leg_best['dep_time']} ({leg_best['airline']})")
            else:
                all_legs_success = False
                
        except Exception as e:
            print(f"查詢 {leg['name']} 失敗: {e}")
            all_legs_success = False

    if all_legs_success and total_trip_price > 0:
        # ⭐ 換上絕對乾淨、全新的紀錄檔名字！
        price_file = "last_price_taiwan_tokyo_ultimate_victory.txt"
        old_total = None
        if os.path.exists(price_file):
            with open(price_file, "r") as f:
                try: old_total = float(f.read().strip())
                except: pass
                
        if old_total is None or total_trip_price < old_total:
            with open(price_file, "w") as f:
                f.write(str(total_trip_price))
            
            detail_text = "\n\n".join(trip_details)
            if old_total is None:
                msg = f"💒 🎉 10月台東雙城大連線特工首報！\n\n💰 三段總預算估計：{format_hkd(total_trip_price)}\n\n{detail_text}\n\n🕵️ 機械人已啟動「日頭飛台北」嚴格篩選，開始為你死守降價！"
            else:
                cheaper = old_total - total_trip_price
                msg = f"🔥 💥 降價大震撼！！10月台東連線平咗 {format_hkd(cheaper)} 呀！\n\n📉 舊總價：{format_hkd(old_total)} ➡️ 🎉 新總價：{format_hkd(total_trip_price)}\n\n{detail_text}\n\n👉 快啲去搶飛湊拼圖！"
            send_telegram(msg)

if __name__ == "__main__":
    check_thailand()    
    check_taiwan_tokyo()
