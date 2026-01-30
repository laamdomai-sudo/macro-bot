import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# 1. Cấu hình duy nhất
st.set_page_config(page_title="Macro AI & MACD", layout="wide")
st.title("🧠 Hệ Thống Định Lượng: Gold - DXY - MACD")

@st.cache_data(ttl=3600)
def get_data():
    raw = yf.download(['GC=F', 'DX-Y.NYB'], period="max", auto_adjust=True)
    if raw.empty or len(raw) < 200: return pd.DataFrame()
    
    df = pd.DataFrame(index=raw.index)
    try:
        df['Gold'] = raw['Close']['GC=F']
        df['DXY'] = raw['Close']['DX-Y.NYB']
    except:
        df['Gold'] = raw.xs('GC=F', axis=1, level=1)['Close']
        df['DXY'] = raw.xs('DX-Y.NYB', axis=1, level=1)['Close']

    # --- TÍNH TOÁN CHỈ BÁO ---
    # MA200 & RSI
    df['MA200'] = df['Gold'].rolling(window=200).mean()
    delta = df['Gold'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))

    # MACD (12, 26, 9)
    exp1 = df['Gold'].ewm(span=12, adjust=False).mean()
    exp2 = df['Gold'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal_Line']

    return df.dropna()

try:
    df = get_data()
    if df.empty:
        st.error("Không tải được dữ liệu.")
    else:
        # --- SIDEBAR QUẢN LÝ ---
        st.sidebar.header("💰 Portfolio")
        entry = st.sidebar.number_input("Giá vốn (USD)", value=2000.0)
        
        # --- BIỂU ĐỒ TỔNG HỢP (Gồm thanh kéo thời gian) ---
        # Tạo 3 hàng: 1 cho giá & DXY, 1 cho MACD, 1 cho RSI
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.05, 
                            row_heights=[0.5, 0.25, 0.25],
                            specs=[[{"secondary_y": True}], [{}], [{}]])

        # Hàng 1: Gold, MA200 và DXY
        fig.add_trace(go.Scatter(x=df.index, y=df['Gold'], name="Vàng", line=dict(color='#FFD700')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MA200'], name="MA200", line=dict(color='#FF00FF', dash='dot')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['DXY'], name="DXY (Trục phải)", line=dict(color='#00CCFF', width=1)), row=1, col=1, secondary_y=True)
        fig.add_hline(y=entry, line_dash="dash", line_color="white", annotation_text="Giá vốn", row=1, col=1)

        # Hàng 2: MACD
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name="MACD", line=dict(color='cyan', width=1)), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Signal_Line'], name="Tín hiệu", line=dict(color='orange', width=1)), row=2, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name="Histogram", marker_color='gray', opacity=0.5), row=2, col=1)

        # Hàng 3: RSI
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='white', width=1)), row=3, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="green", row=3, col=1)

        # Cấu hình thanh kéo thời gian (Range Slider)
        fig.update_layout(
            height=800, template="plotly_dark",
            xaxis3_rangeslider_visible=True, # Thanh kéo nằm ở dưới cùng
            xaxis3_rangeslider_thickness=0.05,
            hovermode="x unified",
            margin=dict(l=50, r=50, t=30, b=50)
        )
        
        fig.update_yaxes(title_text="Giá Vàng", row=1, col=1)
        fig.update_yaxes(title_text="DXY", secondary_y=True, row=1, col=1)
        fig.update_yaxes(title_text="MACD", row=2, col=1)
        fig.update_yaxes(title_text="RSI", row=3, col=1)

        st.plotly_chart(fig, use_container_width=True)

        # --- ĐÁNH GIÁ NHANH ---
        curr = df.iloc[-1]
        st.subheader("📝 Phân tích kỹ thuật nhanh")
        k1, k2 = st.columns(2)
        with k1:
            macd_signal = "CẮT LÊN (MUA)" if curr['MACD'] > curr['Signal_Line'] else "CẮT XUỐNG (BÁN)"
            st.metric("Tín hiệu MACD", macd_signal)
        with k2:
            st.metric("Chỉ số RSI", f"{curr['RSI']:.2f}")

except Exception as e:
    st.error(f"Lỗi: {e}")
