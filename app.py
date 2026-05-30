import streamlit as st
import openai
import os
import re

# 1. 頁面基本設定 (Premium 模式)
st.set_page_config(
    page_title="Japan 2026 旅遊儲錢規劃特工",
    page_icon="✈️",
    layout="wide"
)

# 2. 注入自訂 CSS 樣式 (全新 Vibrant Green #00D4A5 + Energetic Orange #FF9500 系統)
st.markdown("""
    <style>
    /* Premium 模式背景 */
    .stApp {
        background-color: #0E1117;
        color: #E0E2E5;
    }
    /* 標題與晶片樣式 */
    .hero-title {
        background: linear-gradient(45deg, #00D4A5, #FF9500);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.5rem;
    }
    /* 綠色到橙色漸變按鈕 */
    .stButton>button {
        background: linear-gradient(90deg, #00D4A5, #FF9500);
        color: white !important;
        border-radius: 8px;
        border: none;
        padding: 12px 28px;
        font-weight: bold;
        transition: transform 0.2s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 15px rgba(0, 212, 165, 0.4);
    }
    /* 預算卡片樣式 */
    .tier-card {
        background-color: #1A1F2C;
        padding: 20px;
        border-radius: 12px;
        border-top: 4px solid #00D4A5;
        margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .tier-orange {
        border-top: 4px solid #FF9500;
    }
    /* 側邊欄與分帳橫幅 */
    [data-testid="stSidebar"] {
        background-color: #121620;
    }
    .split-banner {
        background-color: #1A2E2A;
        padding: 15px;
        border-left: 5px solid #00D4A5;
        border-radius: 6px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. 初始化 DeepSeek 用戶端
api_key = st.secrets.get("DEEPSEEK_API_KEY", os.environ.get("DEEPSEEK_API_KEY", ""))

st.markdown('<p class="hero-title">✈️ Japan 2026 旅遊預算與 AI 視覺特工</p>', unsafe_allow_html=True)
st.caption("幫緊你幫緊你！地道港人團隊專屬的東京/大阪/北海道出發大計 🇯🇵（綠橙視覺相簿版）")

# 4. 側邊欄設定
with st.sidebar:
    st.header("⚙️ 大腦設定後台")
    user_key = st.text_input("輸入 DeepSeek API Key", value=api_key, type="password")
    model_choice = st.selectbox("選擇 AI 模特兒", ["deepseek-chat", "deepseek-v4-flash"])
    st.markdown("---")
    st.subheader("👥 權限與成員管理")
    st.markdown("🔒 當前用戶角色：**「財政大佬」** (擁有完整編輯權限)")

# 5. 基本資料輸入
col1, col2, col3 = st.columns(3)
with col1:
    days = st.number_input("出發天數 (日)", min_value=1, max_value=30, value=5)
with col2:
    num_people = st.number_input("總人數 (人)", min_value=1, max_value=20, value=2)
with col3:
    target_fund = st.number_input("共同儲錢目標 (HKD)", min_value=0, value=20000)

# 6. 自動相片生成與關鍵字提取 pipeline
def render_ai_photo_gallery(text_result):
    # 簡單提取文本中的潛在景點關鍵字（例如 Day 1, 東京, 築地, 買物 等）
    keywords = ["tokyo", "japan", "travel"] # 預設值
    
    if "大阪" in text_result or "osaka" in text_result.lower():
        keywords = ["osaka", "dotonbori", "kyoto"]
    elif "北海道" in text_result or "hokkaido" in text_result.lower():
        keywords = ["hokkaido", "sapporo", "snow"]
    elif "東京" in text_result:
        keywords = ["shinjuku", "shibuya", "akihabara"]

    st.markdown("### 📸 AI 景點視覺靈感相簿")
    p_col1, p_col2, p_col3 = st.columns(3)
    with p_col1:
        st.image(f"https://picsum.photos/seed/{keywords[0]}/400/300", caption=f"景點靈感探秘 - {keywords[0].upper()}")
    with p_col2:
        st.image(f"https://picsum.photos/seed/{keywords[1]}/400/300", caption=f"行程視覺參考 - {keywords[1].upper()}")
    with p_col3:
        st.image(f"https://picsum.photos/seed/{keywords[2]}/400/300", caption=f"當地風情預覽 - {keywords[2].upper()}")

# 7. 調用 DeepSeek API
def call_deepseek(prompt_input, key, model):
    if not key:
        return "⚠️ 大佬，你未喺側邊欄輸入 DeepSeek API Key 呀！"
    client = openai.OpenAI(api_key=key, base_url="https://api.deepseek.com")
    
    system_prompt = (
        "你是一個地道的香港旅遊專家兼頂級導遊，說話幽默地道並常用香港廣東話（如：大佬、搞掂、性價比高、眼冤、圍番、一家大細）。"
        "請根據用戶輸入，規劃精簡行程，並必須清晰列出三檔預算：1) 窮遊檔（慳得就慳）、2) 平衡檔（性價比最高）、3) 豪華檔（財政大佬豪得起）。"
    )
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_input}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ 門戶大腦接駁失敗！原因：{str(e)}"

# 行程觸發
st.write("---")
destination = st.text_input("想去日本邊度？(例如：東京/大阪/築地食海鮮)", value="東京")

if st.button("🚀 發動 AI 特工規劃 (連線視覺相簿)"):
    with st.spinner("幫緊你幫緊你，AI 特工正九秒九為你提取視覺景點與行程預算..."):
        prompt = f"我想去{destination}玩{days}日，總共有{num_people}個人。請幫忙規劃並計算三檔預算。"
        ai_output = call_deepseek(prompt, user_key, model_choice)
        
        # 左右佈局：左邊文字行程，右邊視覺相片
        layout_col1, layout_col2 = st.columns([3, 2])
        with layout_col1:
            st.markdown("### 🗺️ AI 建議行程與預算分析")
            st.write(ai_output)
        with layout_col2:
            render_ai_photo_gallery(ai_output)

# 8. 基金與進度自動分攤橫幅
st.write("---")
st.markdown('<div class="split-banner">📊 <b>團隊儲錢與自動分攤狀態 (三檔同步中)</b></div>', unsafe_allow_html=True)

col_f1, col_f2 = st.columns(2)
with col_f1:
    current_saved = st.number_input("目前團隊已儲資金 (HKD)", min_value=0, value=6000)
with col_f2:
    st.markdown(f"💰 <b>目標總額</b>：HKD {target_fund:,.0f} | 👥 <b>總人數</b>：{num_people} 人")
    per_person_target = target_fund / num_people if num_people > 0 else 0
    st.markdown(f"📌 <b>每人平均需儲</b>：HKD {per_person_target:,.0f}")

if target_fund > 0:
    progress = (current_saved / target_fund) * 100
    st.progress(min(progress / 100, 1.0))
    st.write(f"📈 團隊當前進度：**{progress:.1f}%**")
    
    if current_saved >= target_fund:
        st.balloons()
        st.success("🎉 掂呀大佬！儲夠錢出發啦！「財政大佬」批准即刻去買機票！")
    else:
        remains = target_fund - current_saved
        remains_per_person = remains / num_people
        st.info(f"💪 仲差 **HKD {remains:,.0f}** 先達標！每人要再供多 **HKD {remains_per_person:,.0f}**！大家加把勁！")
