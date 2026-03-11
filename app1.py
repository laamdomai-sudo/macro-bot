import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Macro History Dashboard", layout="wide")
st.title("🏛️ Global Macro History: 1971 - Present")
st.markdown("---")

# --- THANH SIDEBAR ---
st.sidebar.header("🛠️ Tùy chỉnh Timeline")

# 1. Slider chọn khoảng năm
year_range = st.sidebar.slider(
    "Chọn khoảng thời gian quan sát:",
    min_value=1971,
    max_value=datetime.now().year,
    value=(1971, datetime.now().year)
)

ma_period = st.sidebar.slider("Chu kỳ MA (Dành cho Ratio)", 50, 500, 200)

@st.cache_data
def load_macro_data():
    # Tải từ 1971. Lưu ý: Dữ liệu Gold Futures (GC=F) trên Yahoo thường bắt đầu từ ~1974.
    # Để có 1971, ta lấy dữ liệu Dow Jones trước, Gold sẽ bắt đầu ngay khi có data.
    tickers = {
        "Dow Jones": "^DJI",
        "S&P 500": "^GSPC",
        "Nasdaq 100": "^NDX",
        "Gold": "GC=F",
        "Bitcoin": "BTC-USD"
    }
    df = yf.download(list(tickers.values()), start="1971-01-01")['Close']
    df.columns = list(tickers.keys())
    return df.ffill() # Điền đầy dữ liệu trống

# --- XỬ LÝ DỮ LIỆU ---
with st.spinner('Đang truy xuất dữ liệu lịch sử...'):
    raw_data = load_macro_data()

# Lọc dữ liệu theo Slider Timeline
filtered_data = raw_data[(raw_data.index.year >= year_range[0]) & (raw_data.index.year <= year_range[1])]

# Tính toán các chỉ số
filtered_data['Dow_Gold'] = filtered_data['Dow Jones'] / filtered_data['Gold']
filtered_data['MA_Ratio'] = filtered_data['Dow_Gold'].rolling(window=ma_period).mean()

# --- GIAO DIỆN BIỂU ĐỒ ---
st.subheader(f"📊 Phân tích chu kỳ từ {year_range[0]} đến {year_range[1]}")

# Biểu đồ 1: Dow Jones & Gold (Thang đo Log để so sánh lịch sử dài)
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=filtered_data.index, y=filtered_data['Dow Jones'], name="Dow Jones", line=dict(color='#2980b9')))
fig1.add_trace(go.Scatter(x=filtered_data.index, y=filtered_data['Gold'], name="Vàng (USD/oz)", line=dict(color='#f1c40f')))

fig1.update_layout(
    title="So sánh Dow Jones & Vàng (Thang đo Logarithm)",
    yaxis_type="log",
    height=500,
    template="plotly_white",
    xaxis=dict(rangeslider=dict(visible=True), type="date") # Thanh kéo Timeline trực tiếp
)
st.plotly_chart(fig1, use_container_width=True)

# Biểu đồ 2: Sức mua thực tế (Dow/Gold Ratio)
st.markdown("---")
st.subheader("⚖️ Sức mua thực tế: Cần bao nhiêu Ounce Vàng để mua chỉ số Dow Jones?")

fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=filtered_data.index, y=filtered_data['Dow_Gold'], name="Dow/Gold Ratio", fill='tozeroy', line=dict(color='#d35400')))
fig2.add_trace(go.Scatter(x=filtered_data.index, y=filtered_data['MA_Ratio'], name=f"MA{ma_period}", line=dict(color='black', dash='dot')))

fig2.update_layout(
    title="Dow/Gold Ratio (Tăng = Chứng khoán mạnh, Giảm = Vàng mạnh)",
    height=500,
    template="plotly_white",
    xaxis=dict(rangeslider=dict(visible=True), type="date") # Thanh kéo Timeline trực tiếp
)
st.plotly_chart(fig2, use_container_width=True)

# --- THÔNG TIN THÊM ---
st.info(f"💡 **Ghi chú:** Năm 1971 đánh dấu sự sụp đổ của hệ thống Bretton Woods. "
        f"Việc quan sát Dow/Gold Ratio từ thời điểm này giúp bạn thấy rõ tác động của việc in tiền lên giá trị tài sản thực.")
