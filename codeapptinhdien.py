import streamlit as st
import pandas as pd
from sklearn.linear_model import LinearRegression
import requests
import base64
import re

# --- 1. HÀM ĐỌC ẢNH NỀN ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_png_as_page_bg(bin_file):
    bin_str = get_base64_of_bin_file(bin_file)
    page_bg_img = f'''
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

# --- 2. CẤU HÌNH TRANG ---
st.set_page_config(page_title="Dự toán điện MWH", layout="wide")

# Thử set nền, nếu chưa có file ảnh thì sẽ không báo lỗi
try:
    set_png_as_page_bg('phongnen.png')
except:
    st.warning("Bạn ơi, nhớ để file phongnen.jpg vào cùng thư mục để giao diện lung linh nhé!")

# --- 3. CSS "CHẤT LỪ" (Y CHANG HÌNH) ---
st.markdown("""
    <style>
    /* Tiêu đề Gradient */
    .main-title {
        background: linear-gradient(to right, #ff758c, #ff7eb3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 40px;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Các ô nhập liệu màu đen (Dark Mode inputs) */
    div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: #121214 !important;
        border-radius: 15px !important;
        border: 1px solid #333 !important;
    }
    
    input { color: white !important; }
    label { color: #555 !important; font-weight: 600 !important; margin-bottom: 5px !important; }

    /* Card chứa nội dung */
    .glass-card {
        background: rgba(255, 255, 255, 0.4);
        backdrop-filter: blur(10px);
        border-radius: 30px;
        padding: 30px;
        border: 1px solid rgba(255, 255, 255, 0.6);
    }

    /* Thanh kết quả màu tím gradient ở dưới cùng */
    .result-container {
        background: linear-gradient(95deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        padding: 30px;
        border-radius: 30px;
        text-align: center;
        margin-top: 50px;
        box-shadow: 0 10px 30px rgba(79, 70, 229, 0.4);
    }
    
    .result-val { font-size: 50px; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LOGIC AI & WEATHER ---
@st.cache_resource
def train_ai():
    # Hệ số giả định nếu không có file CSV (Số người, Máy lạnh, Quạt, Giờ dùng, Diện tích)
    coef = [35000, 480000, 25000, 7500, 1500]
    intercept = 50000
    return coef, intercept

coef, intercept = train_ai()

def get_weather():
    try:
        res = requests.get('https://api.open-meteo.com/v1/forecast?latitude=10.823&longitude=106.6296&current_weather=true').json()
        return res['current_weather']['temperature'], res['current_weather']['weathercode'] >= 50
    except:
        return 28.5, False

temp, is_rainy = get_weather()

# --- 5. GIAO DIỆN CHÍNH ---
st.markdown('<h1 class="main-title">✨ DỰ TOÁN ĐIỆN PHÒNG TRỌ MWH ✨</h1>', unsafe_allow_html=True)

col_input, col_weather = st.columns([3, 2], gap="large")

with col_input:
    st.markdown("<h3 style='color: black;'>🔌 Nhập thiết bị nè</h3>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    n = c1.number_input("👥 Số lượng người", 0, 10, 2)
    ml = c2.number_input("❄️ Máy lạnh (cái)", 0, 5, 1)
    q = c1.number_input("🌬️ Số lượng quạt", 0, 10, 2)
    tl = c2.selectbox("🧊 Tủ lạnh?", ["Không có", "Có tủ lạnh"])
    g = c1.number_input("⏰ Giờ dùng máy lạnh/ngày", 0, 24, 8)
    d = c2.number_input("📏 Diện tích (m²)", 0, 100, 20)

with col_weather:
    st.markdown("<h3 style='color: black;'> 🌦️ Thời tiết hiện tại",unsafe_allow_html=True)
    status_icon = "🌧️" if is_rainy else "☀️"
    status_text = "Trời mưa" if is_rainy else "Trời nắng"
    
    st.write(f"### {status_icon} {status_text}")
    st.markdown(f"<h1 style='color:#ff758c; font-size: 80px;'>{temp}°C</h1>", unsafe_allow_html=True)
    
    if is_rainy:
        st.info("AI: Đã tự động giảm 15% tiền điện do trời mát.")

# --- 6. TÍNH TOÁN ---
tl_val = 80000 if tl == "Có tủ lạnh" else 0
prediction = intercept + (n*coef[0]) + (ml*coef[1]) + (q*coef[2]) + (g*coef[3]) + (d*coef[4]) + tl_val

if is_rainy:
    prediction *= 0.85

# --- 7. HIỂN THỊ KẾT QUẢ DƯỚI CÙNG ---
st.markdown(f"""
    <div class="result-container">
        <p style="margin:0; font-weight:600; opacity:0.9;">💸 DỰ BÁO TIỀN ĐIỆN THÁNG NÀY 💸</p>
        <div class="result-val">{int(prediction):,} <span style="font-size:25px;">VND</span></div>
    </div>
    """, unsafe_allow_html=True)

# Thêm hiệu ứng cho "chất"
if prediction > 1000000:
    st.snow()
else:
    st.balloons()
