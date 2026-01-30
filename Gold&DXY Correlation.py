import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# 1. Cấu hình trang
st.set_page_config(page_title="Gold Portfolio VND", layout="wide")
st.title("🧠 Quản Lý Danh Mục Vàng & Vĩ Mô (USD/VND)")

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
        st.caption(f"Tương đương: ${profit_usd:,.2f}")

    # --- PHẦN 2: BIỂU ĐỒ TỔNG HỢP ---
    fig = make_subplots(rows=2, cols=
