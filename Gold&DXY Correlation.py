import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# 1. Cấu hình trang
st.set_page_config(page_title="Gold Portfolio VND", layout="wide")
st.title("🧠 Quản Lý Danh Mục Vàng & Vĩ Mô (VNĐ)")

@st.cache_data(ttl=3600)
def get_data():
    # Tải Vàng, DXY và Tỷ giá USDVND
    raw = yf.download(['GC=F', 'DX-Y.NYB', 'VND=X'], period="max", auto_adjust=True)
    if raw.empty: return pd.DataFrame()

    df = pd.DataFrame(index=raw.index)
    try:
        df['Gold'] = raw['Close']['GC=F']
        df['DXY'] = raw['Close']['DX-Y.NYB']
        df['USDVND'] = raw['Close']['VND=X']
    except:
        df['Gold'] = raw.xs('GC=F', axis=1, level=1)['Close']
        df['DXY'] = raw.xs('DX-Y.NYB', axis=1, level=1)['Close']
        df['USDVND'] = raw.xs('VND=X', axis=1, level=1)['Close']
    
    # Chỉ báo
    df['MA200'] = df['Gold'].rolling(window=200).mean()
    delta = df['Gold'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    
    return df.ffill().dropna()

try:
    df = get_data()
    curr = df.iloc[-1]
    
    # --- PHẦN 1: QUẢN LÝ DANH MỤC (SIDEBAR) ---
    st.sidebar.header("🇻🇳 Danh Mục (VNĐ)")
    with st.sidebar:
        holdings = st.number_input("Số lượng nắm giữ (oz)", min_value=0.0, value=1.0)
        entry_usd = st.number_input("Giá vốn (USD/oz)", min_value=0.0, value=2000.0)
        
        # Tính toán quy đổi
        rate = curr['USDVND']
        curr_price_usd = curr['Gold']
        
        total_value_usd = holdings * curr_price_usd
        total_value_vnd = total_value_usd * rate
        
        profit_usd = (curr_price_usd - entry_usd) * holdings
        profit_vnd = profit_usd * rate
        pnl_pct = ((curr_price_usd - entry_usd) / entry_usd * 100) if entry_usd > 0 else 0

        st.divider()
        st.metric("Tỷ giá USD/VND", f"{rate:,.0f}đ")
        st.metric("Tổng giá trị (VNĐ)", f"{total_value_vnd:,.0f}đ")
        st.metric("Lời / Lỗ", f"{profit_vnd:,.0f}đ", f"{pnl_pct:.2f}%")

    # --- PHẦN 2: BIỂU ĐỒ TỔNG HỢP ---
    # SỬA LỖI TẠI ĐÂY: Đảm bảo đóng đủ ngoặc và tham số
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.08, 
        row_heights=[0.7, 0.3],
        specs=[[{"secondary_y": True}], [{}]]
    )

    # Hàng 1: Vàng & DXY
    fig.add_trace(go.Scatter(x=df.index, y=df['Gold'], name="Vàng (USD)", line=dict(color='#FFD700')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA200'], name="MA200", line=dict(color='#FF00FF', dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['DXY'], name="DXY", line=dict(color='#00CCFF', width=1)), row=1, col=1, secondary_y=True)

    # Hàng 2: RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='white')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)

    # Thanh kéo thời gian & Layout
    fig.update_layout(
        height=700, template="plotly_dark", hovermode="x unified",
        xaxis2_rangeslider_visible=True, 
        xaxis2_rangeslider_thickness=0.04,
        legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center")
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- PHẦN 3: NHẬT KÝ GIAO DỊCH ---
    st.divider()
    st.subheader("📝 Nhật ký & Ghi chú chiến lược")
    note = st.text_area("Nhập kế hoạch giao dịch của bạn tại
