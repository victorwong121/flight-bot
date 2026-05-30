import streamlit as st
import json
import re
from openai import OpenAI
from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    RateLimitError,
)

st.set_page_config(page_title="專屬旅遊 AI 特工", page_icon="✈️", layout="wide")

# ══════════════════════════════════════════════════════════════════════════════
# PREMIUM CUSTOM CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    :root {
        --bg-grad: radial-gradient(circle at 10% -18%, #124238 0%, #0b141f 46%, #080f18 100%);
        --panel-grad: linear-gradient(145deg, #0f1928 0%, #111f32 100%);
        --card-grad: linear-gradient(155deg, #102325 0%, #172a32 100%);
        --input-bg: #102126;
        --input-border: #205354;
        --text-main: #eaf8ff;
        --text-muted: #9bc1d1;
        --accent-primary: #00d4a5;
        --accent-secondary: #46e3be;
        --accent-warm: #ff9500;
        --title-grad: linear-gradient(90deg, #00d4a5, #35e7bf, #ff9500);
        --button-grad: linear-gradient(100deg, #00d4a5 0%, #25d7b1 55%, #ff9500 100%);
    }

    .main, .stApp {
        background: var(--bg-grad) !important;
        color: var(--text-main);
    }
    .block-container {
        max-width: 1450px;
        padding-top: 1.1rem;
        padding-bottom: 2.2rem;
        padding-left: 1.2rem;
        padding-right: 1.2rem;
    }

    h1, h2, h3, h4 {
        letter-spacing: -0.02em;
        color: var(--text-main);
    }

    /* Hero */
    .hero-wrap {
        background: linear-gradient(130deg, rgba(25, 42, 62, 0.72) 0%, rgba(21, 31, 48, 0.45) 100%);
        border: 1px solid rgba(70, 171, 197, 0.32);
        border-radius: 24px;
        padding: 1.3rem 1.45rem 1.15rem;
        box-shadow: 0 16px 38px rgba(7, 14, 24, 0.48);
        margin-bottom: 0.35rem;
    }
    .hero-kicker {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.72rem;
        font-weight: 700;
        color: #0a2029;
        background: linear-gradient(90deg, #42f7d0, #ffa533);
        padding: 0.32rem 0.7rem;
        border-radius: 999px;
        margin-bottom: 0.55rem;
    }
    .themed-title {
        margin: 0;
        font-size: clamp(2.45rem, 5.2vw, 4.1rem) !important;
        line-height: 1.02;
        background: var(--title-grad);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        letter-spacing: -0.04em;
        text-shadow: 0 2px 22px rgba(57, 215, 220, 0.18);
    }
    .hero-sub {
        margin-top: 0.45rem;
        margin-bottom: 0;
        color: #a8d3dd;
        font-size: 1rem;
        font-weight: 500;
    }

    /* Section headers */
    .section-header {
        display: flex;
        flex-direction: column;
        gap: 0.24rem;
        margin-bottom: 0.8rem;
    }
    .section-chip {
        display: inline-flex;
        width: fit-content;
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 0.22rem 0.62rem;
        border-radius: 999px;
        color: #042530;
        background: linear-gradient(90deg, #86ffd9, #ffb34a);
    }
    .section-title {
        font-size: 1.38rem;
        font-weight: 800;
        margin: 0;
        color: #ebfbff;
        letter-spacing: -0.02em;
    }
    .section-desc {
        margin: 0;
        color: #94c1ce;
        font-size: 0.88rem;
    }
    .micro-note {
        color: #8eb6c3;
        font-size: 0.8rem;
        margin-top: -0.15rem;
        margin-bottom: 0.4rem;
    }
    .login-wrap {
        margin-top: 1.1rem;
        margin-bottom: 1rem;
    }
    .login-sub {
        color: #97c0cd;
        font-size: 0.9rem;
        margin-bottom: 0.6rem;
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea textarea {
        background-color: var(--input-bg) !important;
        color: var(--text-main) !important;
        border: 1px solid var(--input-border) !important;
        border-radius: 14px !important;
        transition: border 0.2s, box-shadow 0.2s, transform 0.2s;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 3px rgba(39, 212, 211, 0.22) !important;
        transform: translateY(-1px);
    }

    /* Selects: emoji support + premium shell */
    .stSelectbox > div > div {
        background-color: var(--input-bg) !important;
        border: 1px solid var(--input-border) !important;
        border-radius: 14px !important;
    }
    div[data-baseweb="select"] {
        font-family: "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", sans-serif !important;
        font-size: 1.08rem !important;
    }
    div[data-baseweb="select"] * {
        font-family: "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", sans-serif !important;
    }
    div[data-baseweb="popover"] li,
    ul[role="listbox"] li {
        font-family: "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", sans-serif !important;
        font-size: 1.08rem !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 15px !important;
        border: 1px solid rgba(84, 176, 196, 0.48) !important;
        font-weight: 700;
        letter-spacing: 0.01em;
        transition: transform 0.16s ease, box-shadow 0.2s ease, filter 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 26px rgba(14, 35, 52, 0.45);
        filter: saturate(1.07);
    }
    .stButton > button[kind="primary"] {
        background: var(--button-grad) !important;
        color: #05121d !important;
        border: none !important;
        box-shadow: 0 9px 24px rgba(18, 100, 119, 0.42);
    }

    /* Sidebar + cards */
    section[data-testid="stSidebar"] > div {
        background: linear-gradient(180deg, rgba(10, 29, 32, 0.96) 0%, rgba(8, 20, 29, 0.96) 100%);
        border-right: 1px solid var(--input-border);
    }
    .budget-card {
        background: linear-gradient(145deg, rgba(21, 37, 56, 0.98) 0%, rgba(17, 30, 46, 0.96) 100%);
        border: 1px solid rgba(82, 165, 190, 0.35);
        border-left: 5px solid var(--accent-primary);
        border-radius: 18px;
        padding: 0.82rem 0.96rem;
        margin-bottom: 0.62rem;
        color: var(--text-main);
        box-shadow: 0 10px 24px rgba(5, 16, 27, 0.36);
        transition: transform 0.16s ease, border-color 0.2s;
    }
    .budget-card:hover {
        transform: translateY(-2px);
        border-color: rgba(116, 214, 229, 0.58);
    }
    .budget-card .route { font-weight: 700; font-size: 0.9rem; color: var(--accent-primary); }
    .budget-card .price { font-size: 1.08rem; color: var(--accent-warm); font-weight: 800; margin-top: 0.2rem; }
    .budget-card .detail { font-size: 0.76rem; color: #9dc8d6; margin-top: 0.22rem; }

    /* st.container(border=True) cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--card-grad);
        border: 1px solid rgba(60, 130, 152, 0.42) !important;
        border-radius: 18px !important;
        padding: 0.95rem 0.95rem !important;
        box-shadow: 0 10px 28px rgba(6, 14, 24, 0.42);
        margin-bottom: 0.82rem;
        transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-2px);
        border-color: rgba(106, 203, 225, 0.52) !important;
        box-shadow: 0 14px 32px rgba(8, 16, 27, 0.5);
    }
    div[data-testid="stVerticalBlockBorderWrapper"] p,
    div[data-testid="stVerticalBlockBorderWrapper"] li {
        color: var(--text-main);
        line-height: 1.72;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] img {
        border-radius: 14px;
        margin: 0.62rem 0;
        box-shadow: 0 8px 20px rgba(8, 16, 26, 0.5);
        max-width: 100%;
    }

    /* Tier cards */
    .tier-card {
        border-radius: 20px;
        padding: 1.08rem 1rem 0.92rem;
        height: 100%;
        background: linear-gradient(160deg, #13243a 0%, #132034 100%);
        border: 1px solid rgba(66, 136, 157, 0.45);
        position: relative;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(5, 13, 22, 0.5);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .tier-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 16px 36px rgba(7, 16, 27, 0.62);
    }
    .tier-card.budget { border-top: 4px solid #00d4a5; }
    .tier-card.balance { border-top: 4px solid #34e8bb; background: linear-gradient(160deg, #102e2f 0%, #123438 100%); }
    .tier-card.luxury { border-top: 4px solid #ff9500; background: linear-gradient(160deg, #2d2417 0%, #352a1a 100%); }
    .tier-badge {
        display: inline-block;
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        padding: 0.24rem 0.62rem;
        border-radius: 999px;
        margin-bottom: 0.45rem;
        text-transform: uppercase;
    }
    .tier-badge.budget { background: rgba(0, 212, 165, 0.2); color: #80ffe3; }
    .tier-badge.balance { background: rgba(52, 232, 187, 0.22); color: #afffe9; }
    .tier-badge.luxury { background: rgba(255, 149, 0, 0.22); color: #ffd49c; }
    .tier-title { font-size: 1.18rem; font-weight: 800; color: #f1fdff; margin-bottom: 0.2rem; }
    .tier-subtitle { font-size: 0.82rem; color: #9cc2cf; margin-bottom: 0.7rem; }
    .tier-total {
        font-size: 1.94rem;
        font-weight: 900;
        margin: 0.22rem 0 0.7rem;
        background: linear-gradient(90deg, #dbfff6, #67ffd8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .tier-card.balance .tier-total {
        background: linear-gradient(90deg, #dcfff2, #4de9bc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .tier-card.luxury .tier-total {
        background: linear-gradient(90deg, #ffe4bc, #ff9500);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .tier-row {
        display: flex;
        justify-content: space-between;
        padding: 0.4rem 0;
        border-bottom: 1px dashed rgba(116, 167, 183, 0.25);
        font-size: 0.86rem;
    }
    .tier-row:last-child { border-bottom: none; }
    .tier-row .lbl { color: #96bcca; }
    .tier-row .val { color: #e6f8ff; font-weight: 700; }

    /* Traveler savings cards */
    .traveler-card-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.4rem;
        color: #a7d6e3;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .traveler-card-head .index-chip {
        background: rgba(41, 208, 203, 0.2);
        border: 1px solid rgba(73, 217, 224, 0.4);
        color: #8ff2ed;
        border-radius: 999px;
        padding: 0.2rem 0.58rem;
    }
    .traveler-card-head .tip {
        color: #8fb6c4;
        font-size: 0.75rem;
    }

    /* Metrics */
    .big-metric {
        background: linear-gradient(165deg, rgba(19, 37, 56, 0.96) 0%, rgba(22, 42, 64, 0.97) 100%);
        border: 1px solid rgba(82, 156, 179, 0.34);
        border-radius: 18px;
        padding: 1rem 1.03rem;
        text-align: left;
        box-shadow: 0 8px 20px rgba(7, 16, 25, 0.45);
    }
    .big-metric .lbl {
        font-size: 0.7rem;
        color: #8bb4c2;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        font-weight: 700;
        margin-bottom: 0.28rem;
    }
    .big-metric .val {
        font-size: 1.8rem;
        font-weight: 900;
        line-height: 1.1;
        background: linear-gradient(90deg, #9dffe8, #00d4a5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .big-metric.accent-blue .val {
        background: linear-gradient(90deg, #9cffea, #00d4a5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .big-metric.accent-pink .val {
        background: linear-gradient(90deg, #ffd7a3, #ff9500);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .big-metric .sub { font-size: 0.76rem; color: #8aa8b5; margin-top: 0.34rem; }

    /* progress section */
    .progress-wrap {
        background: linear-gradient(145deg, rgba(16, 33, 50, 0.94) 0%, rgba(14, 29, 45, 0.96) 100%);
        border: 1px solid rgba(79, 156, 176, 0.35);
        border-radius: 16px;
        padding: 0.85rem 1.02rem 0.8rem;
        margin: 0.9rem 0 0.5rem;
    }
    .progress-wrap .top {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 0.42rem;
    }
    .progress-wrap .top .left { font-size: 0.84rem; color: #9ec3cf; font-weight: 700; }
    .progress-wrap .top .right {
        font-size: 1.3rem;
        font-weight: 900;
        background: linear-gradient(90deg, #91ffe8, #00d4a5, #ff9500);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .progress-wrap .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #00d4a5, #34e8bb, #ff9500) !important;
        border-radius: 999px !important;
        height: 13px !important;
    }
    .progress-wrap .stProgress > div > div > div {
        background: rgba(27, 51, 71, 0.78) !important;
        border-radius: 999px !important;
        height: 13px !important;
    }

    /* notices */
    .treasurer-notice {
        background: linear-gradient(135deg, rgba(48, 31, 11, 0.92) 0%, rgba(56, 41, 15, 0.96) 100%);
        border: 1px solid rgba(255, 171, 83, 0.45);
        border-left: 4px solid #ffab53;
        border-radius: 15px;
        padding: 0.72rem 0.95rem;
        margin-top: 0.72rem;
        color: #ffe1bd;
        font-size: 0.9rem;
    }
    .treasurer-notice.unassigned {
        background: linear-gradient(135deg, rgba(51, 24, 24, 0.92) 0%, rgba(60, 28, 28, 0.94) 100%);
        border-color: rgba(236, 99, 99, 0.55);
        border-left-color: #f17171;
        color: #ffd0d0;
    }
    .treasurer-notice b { color: #ffd08f; }
    .treasurer-notice.unassigned b { color: #ffd0d0; }

    .per-person-banner {
        background: linear-gradient(135deg, rgba(20, 39, 60, 0.94) 0%, rgba(23, 45, 68, 0.94) 100%);
        border: 1px solid rgba(95, 169, 193, 0.4);
        border-left: 4px solid var(--accent-primary);
        border-radius: 15px;
        padding: 0.76rem 0.95rem;
        margin: 0.68rem 0 0.4rem;
        color: #e6f9ff;
        font-size: 0.95rem;
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 0.85rem;
        flex-wrap: wrap;
    }
    .per-person-banner .ppb-main b { color: #96f7ec; font-weight: 800; }
    .per-person-banner .ppb-amount {
        font-size: 1.3rem;
        font-weight: 900;
        background: linear-gradient(90deg, #8cffe4, #00d4a5, #ff9500);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .per-person-banner .ppb-sub {
        color: #b6d8e2;
        font-size: 0.84rem;
        font-weight: 600;
        text-align: right;
        flex: 1;
        min-width: 220px;
    }
    .photo-caption {
        margin-top: -0.2rem;
        margin-bottom: 0.5rem;
        color: #9fcbca;
        font-size: 0.8rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DYNAMIC THEME ENGINE
# ══════════════════════════════════════════════════════════════════════════════
THEMES = {
    "🏕️ 動森大地色 (Default)": {
        "bg_grad": "radial-gradient(circle at 10% -18%, #124238 0%, #0b141f 46%, #080f18 100%)",
        "card_grad": "linear-gradient(155deg, #102325 0%, #172a32 100%)",
        "input_bg": "#102126",
        "input_border": "#205354",
        "accent_primary": "#00d4a5",
        "accent_warm": "#ff9500",
        "title_grad": "linear-gradient(90deg, #00d4a5, #35e7bf, #ff9500)",
        "button_grad": "linear-gradient(100deg, #00d4a5 0%, #25d7b1 55%, #ff9500 100%)",
    },
    "🌸 東京櫻花粉": {
        "bg_grad": "radial-gradient(circle at 12% -20%, #173f31 0%, #111b22 52%, #0c1319 100%)",
        "card_grad": "linear-gradient(155deg, #102926 0%, #18342f 100%)",
        "input_bg": "#132722",
        "input_border": "#2a5f50",
        "accent_primary": "#00d4a5",
        "accent_warm": "#ffa122",
        "title_grad": "linear-gradient(90deg, #00e2ad, #3ae9c2, #ffad2f)",
        "button_grad": "linear-gradient(100deg, #00d4a5 0%, #30e3ba 52%, #ff9f1a 100%)",
    },
    "🌊 冰島極光藍": {
        "bg_grad": "radial-gradient(circle at 14% -18%, #0f3f35 0%, #0a1a1f 48%, #070f14 100%)",
        "card_grad": "linear-gradient(155deg, #112b27 0%, #173733 100%)",
        "input_bg": "#0e2722",
        "input_border": "#2d5f52",
        "accent_primary": "#00d4a5",
        "accent_warm": "#ff9500",
        "title_grad": "linear-gradient(90deg, #19e9ba, #6cf2cd, #ffad3a)",
        "button_grad": "linear-gradient(100deg, #00d4a5 0%, #32e1ba 52%, #ff9500 100%)",
    },
}


def inject_theme(theme_key: str):
    t = THEMES[theme_key]
    st.markdown(
        f"""
<style>
    :root {{
        --bg-grad: {t['bg_grad']};
        --card-grad: {t['card_grad']};
        --input-bg: {t['input_bg']};
        --input-border: {t['input_border']};
        --accent-primary: {t['accent_primary']};
        --accent-warm: {t['accent_warm']};
        --title-grad: {t['title_grad']};
        --button-grad: {t['button_grad']};
    }}
</style>
""",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# GEMINI PROMPT
# ══════════════════════════════════════════════════════════════════════════════
SYSTEM_CONTEXT = """你係一個香港本地旅遊 AI 特工，專門幫香港人規劃機票行程。
你識用香港人日常用語同廣東話口語，例如：正呀喂、chur、平靚正、搞掂、唔洗問、掃嘢、食番啖好嘢等。
你已經知道用戶嘅以下航班預算資料，規劃時要主動參考：

【已訂航班 1】
- 路線：香港 (HKG) → 台北 (TPE)
- 航空公司：大灣區航空 (Greater Bay Airlines)
- 日期：2024年10月24日 (早班機)
- 費用：已包含在 HKD 4,021 套票內（連同酷航 TPE→NRT）

【已訂航班 2】
- 路線：香港 (HKG) → 曼谷 (BKK，DMK 廊曼機場降落)
- 航空公司：聯合航空
- 日期：2024年7月
- 費用：HKD 2,294

規劃原則：
- 根據已訂航班時間自動配對行程，避免時間衝突
- 推介平靚正食肆、景點同交通方式
- 用廣東話口語作答，態度親切有趣，適當加 emoji
- 如涉及台北行程，記得提醒用戶 10/25 有酷航 TPE→NRT 14:00 起飛
- 回答要有實際行動步驟，唔好講廢話

【極重要 — 圖片嵌入規則（必須嚴格遵守）】

When you introduce a specific travel destination, city, or key attraction,
you MUST embed a relevant image using EXACTLY the following markdown format:

STRICT FORMAT (THE ONLY ALLOWED URL PATTERN):
![Travel Image](https://images.unsplash.com/featured/800x600/?{Keyword})

CRITICAL RULES — DO NOT VIOLATE:

1. The alt text inside the square brackets `[ ... ]` MUST be a SHORT English
   phrase ONLY. Maximum 3 words. Examples that are CORRECT:
   - `![Travel Image]`
   - `![Beijing]`
   - `![Forbidden City]`
   - `![Tokyo]`
   - `![Okinawa Beach]`

2. NEVER put long Chinese sentences inside the `[ ... ]` brackets.
   NEVER put descriptions, recommendations, or narrative text inside the alt
   text. The Chinese description must go on a SEPARATE line ABOVE or BELOW
   the image, never inside it.

3. Replace `{Keyword}` in the URL with a URL-safe, lowercase English search
   term that is directly relevant to the destination being described in
   that paragraph. Use hyphens for multi-word keywords. Examples:
   - `beijing`
   - `forbidden-city`
   - `great-wall`
   - `tokyo`
   - `shibuya-crossing`
   - `okinawa`
   - `iceland-glacier`
   - `blue-lagoon`

4. The base URL MUST be EXACTLY `https://images.unsplash.com/featured/800x600/?`
   followed by the keyword. DO NOT use any hardcoded photo ID like
   `photo-1542838132...`. DO NOT use `source.unsplash.com`. DO NOT add
   `auto=format`, `fit=crop`, `sig=`, or any other query parameters.

CORRECT EXAMPLE OUTPUT:
北京係中國嘅政治同文化中心，故宮絕對唔可以錯過！

![Forbidden City](https://images.unsplash.com/featured/800x600/?forbidden-city)

INCORRECT EXAMPLES (DO NOT DO THIS):
- ![北京係中國嘅政治中心，故宮一定要去...](https://...)        ← 中文長句喺 [ ] 入面
- ![Beijing](https://images.unsplash.com/photo-1542838132...)   ← 用咗 hardcoded photo ID
- ![Beijing](https://source.unsplash.com/featured/?beijing)     ← 用咗舊嘅 source.unsplash.com

每介紹一個主要地方就插一張圖，全篇大約 2–4 張圖。
圖嘅 markdown 必須獨立成行，前後留空行。每張圖嘅 keyword 必須對應緊鄰段落嘅地點。

【極重要 — 輸出格式（必須跟足）】
當用戶問及任何旅遊目的地或預算估算（例：「北京 5 日」、「日本 7 日」、「曼谷自由行」），
你必須先輸出純文字行程建議，然後喺最後一定要插入一個 JSON code block，
格式如下（JSON 內所有金額用整數港幣 HKD，唔好加千分位逗號、唔好加 "HKD" 字樣）：

```json
{
  "tiers": [
    {
      "name": "輕量小資",
      "tagline": "極致慳家，背包客之選",
      "flight": 1800,
      "hotel_per_night": 350,
      "food_per_day": 200,
      "activities": 500,
      "total": 5800
    },
    {
      "name": "標準平衡",
      "tagline": "性價比之王，最多人揀",
      "flight": 2800,
      "hotel_per_night": 750,
      "food_per_day": 400,
      "activities": 1200,
      "total": 9500
    },
    {
      "name": "豪華特工",
      "tagline": "豪到出汁，享受到極致",
      "flight": 5500,
      "hotel_per_night": 1800,
      "food_per_day": 800,
      "activities": 3000,
      "total": 18500
    }
  ]
}
```

JSON 之前可以加常規行程建議文字。JSON 之後唔好再加額外文字。
總額 (total) 要按天數合理計算（即包含住宿 × 晚數 + 飲食 × 日數 + 機票 + 活動）。
"""


def call_deepseek(deepseek_key: str, user_message: str, model_name: str) -> str:
    client = OpenAI(
        api_key=deepseek_key,
        base_url="https://api.deepseek.com",
    )

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_CONTEXT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
        )
        content = response.choices[0].message.content or ""
        if not content.strip():
            raise ValueError("🤖 AI 返回內容為空，請再試一次。")
        return content
    except AuthenticationError:
        raise ValueError("❌ DeepSeek API Key 無效，請檢查後再試。")
    except RateLimitError:
        raise ValueError("⏳ 請求太頻繁，請稍後再試。")
    except APIConnectionError:
        raise ValueError("🌐 連線 DeepSeek 失敗，請檢查網絡後重試。")
    except APIStatusError as err:
        raise ValueError(f"❌ DeepSeek API 錯誤：HTTP {err.status_code}")


def parse_tiers(reply_text: str):
    """Extract the JSON tier block; return (clean_text, tiers_list_or_None)."""
    match = re.search(r"```json\s*(\{.*?\})\s*```", reply_text, re.DOTALL)
    if not match:
        return reply_text, None
    try:
        data = json.loads(match.group(1))
        tiers = data.get("tiers")
        if not isinstance(tiers, list) or len(tiers) == 0:
            return reply_text, None
        clean_text = reply_text[: match.start()].strip()
        return clean_text, tiers
    except json.JSONDecodeError:
        return reply_text, None


TRAVEL_KEYWORD_MAP = {
    "東京": "tokyo",
    "大阪": "osaka",
    "京都": "kyoto",
    "沖繩": "okinawa beach",
    "北海道": "hokkaido",
    "台北": "taipei city",
    "曼谷": "bangkok travel",
    "北京": "beijing",
    "上海": "shanghai",
    "首爾": "seoul",
    "濟州": "jeju",
    "新加坡": "singapore skyline",
    "吉隆坡": "kuala lumpur",
    "冰島": "iceland glacier",
    "藍湖": "blue lagoon iceland",
    "富士山": "mt fuji",
    "澀谷": "shibuya crossing",
    "涉谷": "shibuya crossing",
    "東京塔": "tokyo tower",
    "海灘": "tropical beach",
}


def _pick_keyword_from_line(line: str):
    for zh_term, keyword in TRAVEL_KEYWORD_MAP.items():
        if zh_term in line:
            return keyword

    lowered = line.lower()
    for keyword in [
        "tokyo",
        "osaka",
        "kyoto",
        "okinawa",
        "beijing",
        "seoul",
        "bangkok",
        "taipei",
        "iceland",
        "fuji",
        "shibuya",
    ]:
        if keyword in lowered:
            return keyword

    english_tokens = re.findall(r"[a-zA-Z][a-zA-Z-]{2,}", line)
    for token in english_tokens:
        token_l = token.lower()
        if token_l not in {"day", "hkd", "travel", "budget", "hotel", "flight"}:
            return token_l
    return None


def extract_photo_keywords(text: str) -> list[str]:
    lines = [ln.strip(" -*") for ln in text.splitlines() if ln.strip()]
    day_lines = [ln for ln in lines if re.search(r"(?i)day\\s*\\d|第\\s*\\d+\\s*日", ln)]
    focus_lines = day_lines if day_lines else lines

    keywords: list[str] = []
    max_count = min(max(2, len(day_lines)), 6)

    for line in focus_lines:
        kw = _pick_keyword_from_line(line)
        if kw and kw not in keywords:
            keywords.append(kw)
        if len(keywords) >= max_count:
            break

    if len(keywords) < 2:
        for zh_term, kw in TRAVEL_KEYWORD_MAP.items():
            if zh_term in text and kw not in keywords:
                keywords.append(kw)
            if len(keywords) >= 2:
                break

    if not keywords:
        keywords = ["travel city", "beach sunset"]

    return keywords


def render_ai_photo_gallery(text: str):
    keywords = extract_photo_keywords(text)
    if not keywords:
        return
    st.markdown("##### 📸 旅程配圖")
    for kw in keywords:
        seed = re.sub(r"[^a-z0-9-]+", "-", kw.lower().replace(" ", "-")).strip("-")
        image_url = f"https://picsum.photos/seed/{seed}/960/600"
        st.image(image_url, use_container_width=True)
        st.markdown(
            f"<div class='photo-caption'>#{kw.replace('-', ' ')}</div>",
            unsafe_allow_html=True,
        )


# Visual config for the 3 tier columns (in display order)
TIER_STYLES = [
    {"key": "budget",  "icon": "💸", "badge": "BUDGET",  "default_name": "輕量小資"},
    {"key": "balance", "icon": "✈️", "badge": "BALANCE", "default_name": "標準平衡"},
    {"key": "luxury",  "icon": "👑", "badge": "LUXURY",  "default_name": "豪華特工"},
]

ROLE_OPTIONS = [
    "👑 財政大臣 (負責管數與集資)",
    "🗺️ 行程總監 (負責搵景點排行程)",
    "📸 首席攝影師 (負責影相打卡)",
    "🚗 歡樂跟隊員 (負責準時出席同讚賞)",
]
TREASURER_ROLE = ROLE_OPTIONS[0]
AVATAR_OPTIONS = ["🐶", "🦊", "🐱", "🐸", "🐼", "🐨", "🐧"]
SPECIAL_TREASURER_CODES = {"BOSS2026", "HKTREASURY", "FINANCE2026"}


def render_tier_card(tier: dict, style: dict):
    name = tier.get("name", style["default_name"])
    tagline = tier.get("tagline", "")
    total = tier.get("total", 0)
    flight = tier.get("flight", 0)
    hotel = tier.get("hotel_per_night", 0)
    food = tier.get("food_per_day", 0)
    activities = tier.get("activities", 0)

    return f"""
<div class="tier-card {style['key']}">
  <span class="tier-badge {style['key']}">{style['badge']}</span>
  <div class="tier-title">{style['icon']} {name}</div>
  <div class="tier-subtitle">{tagline}</div>
  <div class="tier-total">HKD {total:,}</div>
  <div class="tier-row"><span class="lbl">機票</span><span class="val">HKD {flight:,}</span></div>
  <div class="tier-row"><span class="lbl">住宿／晚</span><span class="val">HKD {hotel:,}</span></div>
  <div class="tier-row"><span class="lbl">飲食／日</span><span class="val">HKD {food:,}</span></div>
  <div class="tier-row"><span class="lbl">景點活動</span><span class="val">HKD {activities:,}</span></div>
</div>
"""


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE — flight budget list
# ══════════════════════════════════════════════════════════════════════════════
if "budget_data" not in st.session_state:
    st.session_state.budget_data = []
if "target_budget" not in st.session_state:
    st.session_state.target_budget = 15000
if "last_ai_text" not in st.session_state:
    st.session_state.last_ai_text = ""
if "last_tiers" not in st.session_state:
    st.session_state.last_tiers = None
if "selected_tier" not in st.session_state:
    st.session_state.selected_tier = None
if "team_pools" not in st.session_state:
    st.session_state.team_pools = {}
if "current_user" not in st.session_state:
    st.session_state.current_user = None


def _default_member_profile(member_count: int) -> dict:
    return {
        "avatar": AVATAR_OPTIONS[member_count % len(AVATAR_OPTIONS)],
        "saved": 0,
        "role": ROLE_OPTIONS[min(member_count, len(ROLE_OPTIONS) - 1)],
    }


def _ensure_member(pool: dict, nickname: str, is_treasurer: bool):
    if nickname not in pool["members"]:
        pool["members"][nickname] = _default_member_profile(len(pool["members"]))
    if is_treasurer:
        pool["members"][nickname]["role"] = TREASURER_ROLE


def delete_flight(index: int):
    st.session_state.budget_data.pop(index)


def add_flight(label: str, price_hkd: int, detail: str):
    st.session_state.budget_data.append(
        {"label": label, "price_hkd": price_hkd, "detail": detail, "icon": "✈️"}
    )


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
selected_theme = st.sidebar.selectbox(
    "🎨 選擇介面主題",
    options=list(THEMES.keys()),
    index=0,
    key="ui_theme",
)
inject_theme(selected_theme)
st.sidebar.divider()

if st.session_state.current_user:
    current_user = st.session_state.current_user
    st.sidebar.success(
        f"👤 {current_user['nickname']} ｜ 基金碼：{current_user['share_code']}"
    )
    if st.sidebar.button("🚪 登出", use_container_width=True):
        st.session_state.current_user = None
        st.session_state.last_ai_text = ""
        st.session_state.last_tiers = None
        st.session_state.selected_tier = None
        st.rerun()
    st.sidebar.divider()

if not st.session_state.current_user:
    st.markdown(
        "<div class='hero-wrap'>"
        "<span class='hero-kicker'>👋 Welcome</span>"
        "<h1 class='themed-title'>✈️ 出發啦</h1>"
        "<p class='hero-sub'>輸入邀請碼同暱稱，即刻加入你哋嘅旅行基金。</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    left_spacer, center_col, right_spacer = st.columns([1, 1.25, 1])
    with center_col:
        with st.container(border=True):
            st.markdown(
                "<div class='section-header login-wrap'>"
                "<span class='section-chip'>Join Fund</span>"
                "<h3 class='section-title'>登入旅行基金</h3>"
                "<p class='login-sub'>同隊友共用同一個邀請碼，即可同步大家儲蓄進度。</p>"
                "</div>",
                unsafe_allow_html=True,
            )
            share_code = st.text_input(
                "邀請碼",
                placeholder="例：Japan2026",
                key="login_share_code",
            )
            nickname = st.text_input(
                "我的暱稱",
                placeholder="例：阿明 / 阿強 / 阿珍",
                key="login_nickname",
            )
            st.caption("如果暱稱是「財政大佬」或使用特別邀請碼，會啟用管理模式。")
            if st.button("進入旅行基金", type="primary", use_container_width=True):
                code_clean = share_code.strip()
                nickname_clean = nickname.strip()
                if not code_clean or not nickname_clean:
                    st.error("請填寫邀請碼同暱稱先可以進入。")
                else:
                    normalized_code = code_clean.upper()
                    is_treasurer = (
                        nickname_clean == "財政大佬"
                        or normalized_code in SPECIAL_TREASURER_CODES
                    )
                    pool = st.session_state.team_pools.setdefault(
                        code_clean,
                        {"members": {}},
                    )
                    _ensure_member(pool, nickname_clean, is_treasurer)
                    st.session_state.current_user = {
                        "share_code": code_clean,
                        "nickname": nickname_clean,
                        "is_treasurer": is_treasurer,
                    }
                    st.rerun()
    st.stop()

st.sidebar.header("📊 我的實時航班預算庫")

if not st.session_state.budget_data:
    st.sidebar.caption("_仲未有任何航班記錄，撳下面 ➕ 新增航班 開始建立預算庫！_")

for i, item in enumerate(st.session_state.budget_data):
    card_col, del_col = st.sidebar.columns([5, 1])
    with card_col:
        st.markdown(
            f"""
<div class="budget-card">
  <div class="route">{item['icon']} {item['label']}</div>
  <div class="price">HKD {item['price_hkd']:,}</div>
  <div class="detail">{item['detail']}</div>
</div>""",
            unsafe_allow_html=True,
        )
    with del_col:
        st.markdown("<div style='margin-top:22px'></div>", unsafe_allow_html=True)
        if st.button("❌", key=f"del_flight_{i}", help="刪除此航班"):
            delete_flight(i)
            st.rerun()

total_budget = sum(f["price_hkd"] for f in st.session_state.budget_data)
flight_count = len(st.session_state.budget_data)
st.sidebar.markdown(
    f"**總預算使用：** `HKD {total_budget:,}`　**｜**　**已記錄行程：** {flight_count} 條"
)

with st.sidebar.expander("➕ 新增航班", expanded=False):
    new_label = st.text_input("航班名稱／描述", placeholder="例：11月首爾行", key="new_flight_label")
    new_price = st.number_input(
        "價格 (HKD)", min_value=0, max_value=500_000, value=0, step=100, key="new_flight_price"
    )
    new_detail = st.text_input(
        "補充說明（可選）", placeholder="例：香港快運 HKG→ICN", key="new_flight_detail"
    )
    if st.button("➕ 新增航班", use_container_width=True, key="add_flight_btn"):
        if new_label.strip():
            add_flight(new_label.strip(), int(new_price), new_detail.strip())
            st.rerun()
        else:
            st.warning("請先填寫航班名稱！")

st.sidebar.divider()

st.sidebar.subheader("🔑 AI 引擎設定（DeepSeek）")
deepseek_model = st.sidebar.selectbox(
    "選擇模型",
    options=["deepseek-v4-flash", "deepseek-chat"],
    index=0,
    help="預設用較平嘅 flash 模型；如帳號未開通可改用 deepseek-chat。",
)
deepseek_key = st.sidebar.text_input(
    "輸入你的 DeepSeek API Key：",
    type="password",
    help="可於 https://platform.deepseek.com 取得 API Key",
)
st.sidebar.caption("💡 DeepSeek 通常更平，而且香港用家多數唔使 VPN。")
st.sidebar.caption("安裝套件：`pip install openai`")
if deepseek_key:
    st.sidebar.success("✅ DeepSeek API Key 已載入")
else:
    st.sidebar.caption("_尚未輸入 API Key，AI 功能暫停。_")

current_user = st.session_state.current_user
current_pool = st.session_state.team_pools[current_user["share_code"]]


# ══════════════════════════════════════════════════════════════════════════════
# MAIN LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    "<div class='hero-wrap'>"
    "<span class='hero-kicker'>🔥 HK Friends Travel Savings</span>"
    "<h1 class='themed-title'>✈️ 出發啦</h1>"
    "<p class='hero-sub'>同班Friend一齊儲旅費、揀方案、即刻搞掂下一轉旅行計劃。</p>"
    "</div>",
    unsafe_allow_html=True,
)
st.divider()

left_col, right_col = st.columns([3, 2], gap="large")

# ── LEFT: AI Query ────────────────────────────────────────────────────────────
with left_col:
    with st.container(border=True):
        st.markdown(
            "<div class='section-header'>"
            "<span class='section-chip'>AI Planning</span>"
            "<h3 class='section-title'>💬 AI 行程規劃室</h3>"
            "<p class='section-desc'>輸入目的地或旅程目標，AI 會即時生成行程同三檔預算方案。</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        user_input = st.text_input(
            "請下達指令：",
            placeholder="例：北京 5 日遊預算係幾多？/ 冰島 8 日自駕遊大數據估算",
            label_visibility="collapsed",
        )
        st.markdown("<p class='micro-note'>提示：越具體越準，例如「4人、6日、想食好少少」。</p>", unsafe_allow_html=True)

        btn_col1, btn_col2 = st.columns([4, 1], gap="small")
        with btn_col1:
            launch = st.button("🚀 發動 AI 規劃", use_container_width=True, type="primary")
        with btn_col2:
            if st.button("🗑️ 清除", use_container_width=True):
                st.session_state.last_ai_text = ""
                st.session_state.last_tiers = None
                st.session_state.selected_tier = None
                st.rerun()

    if launch:
        if not user_input.strip():
            st.warning("⚠️ 請先輸入你的行程需求！")
        elif not deepseek_key.strip():
            st.error("🔑 請先喺左側 Sidebar 貼入你的 DeepSeek API Key！")
        else:
            with st.spinner("幫緊你、幫緊你..."):
                try:
                    ai_reply = call_deepseek(
                        deepseek_key.strip(),
                        user_input.strip(),
                        deepseek_model,
                    )
                    clean_text, tiers = parse_tiers(ai_reply)
                    st.session_state.last_ai_text = clean_text or ""
                    st.session_state.last_tiers = tiers
                    st.session_state.selected_tier = None
                    st.success("✨ AI 特工規劃完成！")
                except ValueError as e:
                    st.error(str(e))
                except (KeyError, IndexError):
                    st.error("🤖 AI 返回格式異常，請重試一次。")
                except Exception as e:
                    st.error(f"⚠️ 發生未預期錯誤：{e}")

    # ── Persisted AI response renderer (survives reruns from tier buttons) ──
    if st.session_state.last_ai_text or st.session_state.last_tiers:
        with st.container(border=True):
            st.markdown(
                "<div class='section-header'>"
                "<span class='section-chip'>AI Result</span>"
                "<h3 class='section-title'>🎯 你的專屬智能行程提案</h3>"
                "<p class='section-desc'>可直接揀其中一檔預算，一鍵同步到右邊基金目標。</p>"
                "</div>",
                unsafe_allow_html=True,
            )

            if st.session_state.last_ai_text:
                with st.container(border=True):
                    text_col, photo_col = st.columns([3, 2], gap="medium")
                    with text_col:
                        st.markdown(st.session_state.last_ai_text)
                    with photo_col:
                        render_ai_photo_gallery(st.session_state.last_ai_text)

            if st.session_state.last_tiers:
                st.markdown("##### 💎 三檔預算方案")
                cols = st.columns(3, gap="medium")
                for col, tier, style in zip(
                    cols, st.session_state.last_tiers[:3], TIER_STYLES
                ):
                    with col:
                        st.markdown(render_tier_card(tier, style), unsafe_allow_html=True)
                        total = int(tier.get("total", 0))
                        is_selected = st.session_state.selected_tier == style["key"]
                        label = (
                            f"✅ 已套用 HKD {total:,}"
                            if is_selected
                            else "🎯 選用此方案"
                        )
                        if st.button(
                            label,
                            key=f"select_tier_{style['key']}",
                            use_container_width=True,
                            disabled=is_selected,
                        ):
                            st.session_state.target_budget = total
                            st.session_state.selected_tier = style["key"]
                            st.rerun()

            st.divider()
            m1, m2, m3 = st.columns(3)
            m1.metric("AI 引擎", f"DeepSeek ({deepseek_model})")
            m2.metric("預算庫行程", f"{len(st.session_state.budget_data)} 條")
            m3.metric(
                "總預算",
                f"HKD {sum(f['price_hkd'] for f in st.session_state.budget_data):,}",
            )
            st.caption("_以上行程由 DeepSeek AI 根據你的預算庫即時生成，可隨時調整。_")


# ── RIGHT: Savings Pool ───────────────────────────────────────────────────────
with right_col:
    with st.container(border=True):
        st.markdown(
            "<div class='section-header'>"
            "<span class='section-chip'>Fund Setup</span>"
            "<h3 class='section-title'>🎯 旅遊目標基金設定</h3>"
            "<p class='section-desc'>設定今次旅程總目標金額，配合 AI 方案可一鍵套用。</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        target_budget = st.number_input(
            "目標總預算 (HKD)",
            min_value=0,
            max_value=500_000,
            step=500,
            key="target_budget",
            help="設定你哋團隊嘅旅遊目標金額（撳左側 AI 方案按鈕可一鍵套用）",
        )

    with st.container(border=True):
        st.markdown(
            "<div class='section-header'>"
            "<span class='section-chip'>Team Savings</span>"
            "<h3 class='section-title'>👥 旅行者儲蓄情況</h3>"
            "<p class='section-desc'>顯示同組所有隊友進度；一般模式只可修改自己金額。</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        travelers = []
        member_items = list(current_pool["members"].items())
        for i, (member_name, member_data) in enumerate(member_items):
            is_self = member_name == current_user["nickname"]
            can_edit_amount = current_user["is_treasurer"] or is_self
            with st.container(border=True):
                st.markdown(
                    f"<div class='traveler-card-head'>"
                    f"<span class='index-chip'>隊友 {i + 1}</span>"
                    f"<span class='tip'>"
                    f"{'可編輯金額' if can_edit_amount else '只讀（其他隊友）'}"
                    f"</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                col_avatar, col_name, col_amount, col_role = st.columns([1.5, 2.8, 2.1, 2.6], gap="small")
                with col_avatar:
                    avatar = member_data.get("avatar", "🧳")
                    st.markdown(f"### {avatar}")
                with col_name:
                    st.markdown(
                        f"**{member_name}**"
                        + (" _(你)_" if is_self else "")
                    )
                with col_amount:
                    saved = st.number_input(
                        f"已儲金額 {i + 1}",
                        min_value=0,
                        max_value=500_000,
                        value=int(member_data.get("saved", 0)),
                        step=100,
                        key=f"member_saved_{current_user['share_code']}_{member_name}",
                        disabled=not can_edit_amount,
                    )
                with col_role:
                    role = member_data.get("role", ROLE_OPTIONS[-1])
                    st.markdown(f"`{role}`")

                if can_edit_amount:
                    current_pool["members"][member_name]["saved"] = int(saved)
                else:
                    st.caption("🔒 只有你自己或財政大佬可以修改此金額。")

            nickname_clean = member_name.strip()
            display_name = (
                f"{avatar} {nickname_clean}"
                if nickname_clean
                else f"{avatar} 無名隊友"
            )
            travelers.append(
                {
                    "avatar": avatar,
                    "nickname": nickname_clean,
                    "name": display_name,
                    "saved": int(saved),
                    "role": role,
                    "active": bool(nickname_clean),
                }
            )

        if not member_items:
            st.info("目前未有隊友加入。分享邀請碼俾朋友即可同步儲蓄進度。")

    # ── Pool calculation ─────────────────────────────────────────────────────
    total_saved = sum(t["saved"] for t in travelers)
    pct = min(total_saved / target_budget, 1.0) if target_budget > 0 else 0.0
    pct_display = (total_saved / target_budget * 100) if target_budget > 0 else 0.0
    remaining = max(target_budget - total_saved, 0)

    with st.container(border=True):
        st.markdown(
            "<div class='section-header'>"
            "<span class='section-chip'>Fund Status</span>"
            "<h3 class='section-title'>📈 基金達成情況</h3>"
            "<p class='section-desc'>即時睇到團隊儲蓄進度、每人目標同財政大臣狀態。</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        s1, s2, s3 = st.columns(3, gap="small")
        s1.markdown(
            f'<div class="big-metric"><div class="lbl">已儲總額</div>'
            f'<div class="val">HKD {total_saved:,}</div>'
            f'<div class="sub">{len(travelers)} 人合計</div></div>',
            unsafe_allow_html=True,
        )
        s2.markdown(
            f'<div class="big-metric accent-blue"><div class="lbl">達成率</div>'
            f'<div class="val">{pct_display:.1f}%</div>'
            f'<div class="sub">目標 HKD {target_budget:,}</div></div>',
            unsafe_allow_html=True,
        )
        s3.markdown(
            f'<div class="big-metric accent-pink"><div class="lbl">仲差幾多</div>'
            f'<div class="val">HKD {remaining:,}</div>'
            f'<div class="sub">{"搞掂喇！ 🎉" if remaining == 0 else "繼續加油！"}</div></div>',
            unsafe_allow_html=True,
        )

        # ── Per-person auto-split ────────────────────────────────────────────
        active_travelers = [t for t in travelers if t["active"]]
        active_traveler_count = len(active_travelers)
        divisor = active_traveler_count if active_traveler_count > 0 else 1
        per_person_target = target_budget / divisor

        roster = " · ".join(t["name"] for t in active_travelers) or "尚未有活躍隊友"

        st.markdown(
            f'<div class="per-person-banner">'
            f'<div class="ppb-main">⚖️ <b>隊友平分預算：</b>每人平均需儲 '
            f'<span class="ppb-amount">HKD {per_person_target:,.0f}</span></div>'
            f'<div class="ppb-sub">👥 {roster}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Treasurer status ─────────────────────────────────────────────────
        treasurers = [t["name"] for t in travelers if t["role"] == TREASURER_ROLE]
        if treasurers:
            treasurer_names = "、".join(treasurers)
            st.markdown(
                f'<div class="treasurer-notice">💰 溫馨提示：本旅程基金目前正由 '
                f'<b>{treasurer_names}</b> 負責統籌與保管！</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="treasurer-notice unassigned">⚠️ '
                '<b>請指定一位朋友擔任財政大臣管理此 Pool！</b></div>',
                unsafe_allow_html=True,
            )

        # ── Fancy progress bar ───────────────────────────────────────────────
        st.markdown(
            f"""
<div class="progress-wrap">
  <div class="top">
    <div class="left">🚀 團隊基金進度</div>
    <div class="right">{pct_display:.1f}%</div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.progress(pct)

    # ── Per-traveler breakdown ───────────────────────────────────────────────
    with st.container(border=True):
        st.markdown(
            "<div class='section-header'>"
            "<span class='section-chip'>Team Detail</span>"
            "<h3 class='section-title'>🧾 隊友儲蓄明細</h3>"
            "<p class='section-desc'>逐位隊友查看個人進度，方便分工同追數。</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        with st.expander("👀 展開查看每人貢獻", expanded=False):
            for t in travelers:
                person_pct = (t["saved"] / target_budget * 100) if target_budget > 0 else 0
                st.markdown(
                    f"**{t['name']}** — {t['role']}　`HKD {t['saved']:,}`　"
                    f"({person_pct:.1f}% of target)"
                )
                st.progress(
                    min(t["saved"] / target_budget, 1.0) if target_budget > 0 else 0.0
                )

    # ── Celebration ──────────────────────────────────────────────────────────
    if total_saved >= target_budget and target_budget > 0:
        st.success("🎉 恭喜！基金已全數達標！即刻執包袱出發去旅行啦！")
        st.balloons()
    elif pct_display >= 75:
        st.info(f"🔥 正呀喂！已儲 {pct_display:.1f}%，差少少就搞掂！繼續 chur！")
    elif pct_display >= 50:
        st.info(f"💪 過咗一半喇！{pct_display:.1f}% 達成，平靚正繼續儲！")
