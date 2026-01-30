import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# 1. Cấu hình trang web
st.set_page_config(page_title="Macro AI Dashboard", layout="wide")
st.title("📊 Hệ Thống Giám Sát & Phân Tích Tương Quan")
st.markdown("---")

# 2. Hàm tải dữ liệu
@st.cache_data(ttl=3600)
def get_data():
    tickers = ['GC=F', 'SI=F', 'DX-Y.NYB']
    raw = yf.download(tickers, period="2y", auto_adjust=True)
    if raw.empty: return pd.DataFrame()
    df = pd.DataFrame(index=raw.index)
    try:
        df['Gold'] = raw['Close']['GC=F']
        df['Silver'] = raw['Close']['SI=F']
        df['DXY'] = raw['Close']['DX-Y.NYB']
    except:
        df['Gold'] = raw.xs('GC=F', axis=1, level=1)['Close']
        df['Silver'] = raw.xs('SI=F', axis=1, level=1)['Close']
        df['DXY'] = raw.xs('DX-Y.NYB', axis=1, level=1)['Close']
    return df.ffill().dropna()

try:
    df = get_data()
    if not df.empty:
        # Tính toán các chỉ số
        df['Ratio'] = df['Gold'] / df['Silver']
        last_gold, prev_gold = df['Gold'].iloc[-1], df['Gold'].iloc[-2]
        last_dxy, prev_dxy = df['DXY'].iloc[-1], df['DXY'].iloc[-2]
        last_ratio = df['Ratio'].iloc[-1]
        last_date = df.index[-1].strftime('%d/%m/%Y')

        st.write(f"Dữ liệu cập nhật ngày: **{last_date}**")

        # 3. Hiển thị Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Vàng (USD/oz)", f"${last_gold:,.2f}", f"{last_gold - prev_gold:,.2f}")
        c2.metric("Chỉ số DXY", f"{last_dxy:.2f}", f"{last_dxy - prev_dxy:.2f}")
        c3.metric("Tỷ lệ Vàng/Bạc", f"{last_ratio:.1f}")

        # 4. VẼ BIỂU ĐỒ TƯƠNG QUAN (ĐÃ SỬA LỖI SYNTAX)
        fig = go.Figure()

        # Thêm Vàng (Trục trái)
        fig.add_trace(go.Scatter(x=df.index, y=df['Gold'], name="Vàng",
                                 line=dict(color='#FFD700', width=2.5)))

        # Thêm Bạc (Trục trái)
        fig.add_trace(go.Scatter(x=df.index, y=df['Silver'], name="Bạc",
                                 line=dict(color='#C0C0C0', width=1.5)))

        # Thêm DXY (Trục phải)
        fig.add_trace(go.Scatter(x=df.index, y=df['DXY'],
