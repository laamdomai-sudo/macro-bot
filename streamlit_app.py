import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Cấu hình trang web
st.set_page_config(page_title="Macro Dashboard", layout="wide")

st.title("📊 Hệ Thống Giám Sát Tài Chính Toàn Cầu")
st.markdown("Dữ liệu được cập nhật tự động từ Yahoo Finance")

# Thanh bên (Sidebar) để chọn khoảng thời gian
st.sidebar.header("Tùy chỉnh")
days = st.sidebar.slider("Chọn số ngày dữ liệu", 365, 365*50, 365*10)

@st.cache_data(ttl=3600) # Lưu bộ nhớ đệm 1 tiếng để tải nhanh hơn
def load_data():
    tickers = ['GC=F', 'SI=F', 'DX-Y.NYB']
    data = yf.download(tickers, period="max", auto_adjust=True)
    df = pd.DataFrame({
        'Gold': data['Close']['GC=F'],
        'Silver': data['Close']['SI=F'],
        'DXY': data['Close']['DX-Y.NYB']
    }).dropna()
    df['Ratio'] = df['Gold'] / df['Silver']
    return df

df_all = load_data()
df = df_all.tail(days)

# Hiển thị các chỉ số quan trọng (Metric)
col1, col2, col3 = st.columns(3)
col1.metric("Giá Vàng", f"${df['Gold'].iloc[-1]:,.2f}")
col2.metric("Chỉ số DXY", f"{df['DXY'].iloc[-1]:,.2f}")
col3.metric("Tỷ lệ Vàng/Bạc", f"{df['Ratio'].iloc[-1]:,.2f}")

# Vẽ biểu đồ Plotly
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                    subplot_titles=("Giá Vàng & Bạc", "Sức mạnh Đồng USD (DXY)"))

fig.add_trace(go.Scatter(x=df.index, y=df['Gold'], name="Vàng", line=dict(color='#FFD700')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['DXY'], name="DXY", fill='tozeroy'), row=2, col=1)

fig.update_layout(height=700, template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(df.tail(10)) # Hiển thị bảng dữ liệu 10 ngày gần nhất