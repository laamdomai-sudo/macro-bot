import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# 1. Cấu hình trang
st.set_page_config(page_title="FX & Rates Correlation", layout="wide")
st.title("🏦 Tương Quan Lãi Suất & Tỷ Giá Hối Đoái")

# Nhập liệu thủ công cho VND nếu dữ liệu Yahoo lỗi
with st.sidebar:
    st.header("⚙️ Cấu hình dữ liệu")
    manual_vnd_rate = st.number_input("Lãi suất VND 10Y hiện tại (%):", value=2.7, step=0.1)
    st.info("Dữ liệu tỷ giá USD/VND và USD/JPY được lấy trực tiếp từ Yahoo Finance.")

@st.cache_data(ttl=3600)
def get_full_data():
    # Tickers lãi suất: US10Y (^TNX), JP10Y (JG10.V)
    # Tickers tỷ giá: USDVND=X, USDJPY=X
    tickers = ['^TNX', 'JG10.V', 'USDVND=X', 'USDJPY=X']
    raw = yf.download(tickers, period="2y", auto_adjust=True)
    
    df = pd.DataFrame(index=raw.index)
    try:
        df['USD_10Y'] = raw['Close']['^TNX']
        df['JPY_10Y'] = raw['Close']['JG10.V']
        df['USDVND'] = raw['Close']['USDVND=X']
        df['USDJPY'] = raw['Close']['USDJPY=X']
        
        # Lấy dữ liệu VND 10Y (nếu có)
        vn_bond = yf.download('VND10Y=RR', period="2y")['Close']
        if not vn_bond.empty:
            df['VND_10Y'] = vn_bond
        else:
            df['VND_10Y'] = manual_vnd_rate
    except:
        df['VND_10Y'] = manual_vnd_rate
        
    return df.ffill().dropna()

try:
    df = get_full_data()
    
    if not df.empty:
        curr = df.iloc[-1]
        prev = df.iloc[-2]

        # 2. Hiển thị Metrics chính
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("USD/VND", f"{curr['USDVND']:,.0f}", f"{curr['USDVND'] - prev['USDVND']:,.0f}")
        m2.metric("USD/JPY", f"{curr['USDJPY']:.2f}", f"{curr['USDJPY'] - prev['USDJPY']:.2f}")
        m3.metric("Lãi suất Mỹ (10Y)", f"{curr['USD_10Y']:.2f}%")
        m4.metric("Chênh lệch US-VN", f"{curr['USD_10Y'] - curr['VND_10Y']:.2f}%")

        # 3. BIỂU ĐỒ 1: SO SÁNH LÃI SUẤT
        st.subheader("📈 1. Biến Động Lãi Suất Trái Phiếu (Thủ phạm gây áp lực)")
        fig_rates = go.Figure()
        fig_rates.add_trace(go.Scatter(x=df.index, y=df['USD_10Y'], name="Lãi suất USD", line=dict(color='#FF4B4B', width=2)))
        fig_rates.add_trace(go.Scatter(x=df.index, y=df['VND_10Y'], name="Lãi suất VND", line=dict(color='#FBC02D', width=2)))
        fig_rates.add_trace(go.Scatter(x=df.index, y=df['JPY_10Y'], name="Lãi suất JPY (Phải)", yaxis="y2", line=dict(color='#1E88E5', width=1)))
        
        fig_rates.update_layout(
            height=400, template="plotly_dark", hovermode="x unified",
            yaxis=dict(title="Lãi suất (%)"),
            yaxis2=dict(overlaying="y", side="right", showgrid=False),
            margin=dict(t=20, b=20)
        )
        st.plotly_chart(fig_rates, use_container_width=True)

        # 4. BIỂU ĐỒ 2: BIẾN ĐỘNG TỶ GIÁ
        st.subheader("💱 2. Biến Động Tỷ Giá Hối Đoái (Hệ quả thực tế)")
        fig_fx = go.Figure()
        fig_fx.add_trace(go.Scatter(x=df.index, y=df['USDVND'], name="Tỷ giá USD/VND", line=dict(color='#00C853', width=2)))
        fig_fx.add_trace(go.Scatter(x=df.index, y=df['USDJPY'], name="Tỷ giá USD/JPY (Phải)", yaxis="y2", line=dict(color='#AA00FF', width=2)))
        
        fig_fx.update_layout(
            height=400, template="plotly_dark", hovermode="x unified",
            yaxis=dict(title="USD/VND (VNĐ)"),
            yaxis2=dict(overlaying="y", side="right", showgrid=False, title="USD/JPY (Yên)"),
            xaxis=dict(rangeslider=dict(visible=True)),
            margin=dict(t=20, b=20)
        )
        st.plotly_chart(fig_fx, use_container_width=True)

        # 5. PHÂN TÍCH TỰ ĐỘNG
        st.divider()
        st.subheader("🤖 Nhận Định Liên Thị Trường")
        col_a, col_b = st.columns(2)
        
        with col_a:
            spread_vn = curr['USD_10Y'] - curr['VND_10Y']
            if spread_vn > 0.5:
                st.error(f"🔴 **Cảnh báo USD/VND:** Chênh lệch lãi suất đang ở mức cao ({spread_vn:.2f}%). Áp lực mất giá lên VND sẽ còn tiếp diễn nếu NHNN không can thiệp lãi suất.")
            else:
                st.success("🟢 **Ổn định USD/VND:** Chênh lệch lãi suất đang ở mức an toàn, hỗ trợ tỷ giá ổn định.")

        with col_b:
            spread_jp = curr['USD_10Y'] - curr['JPY_10Y']
            if spread_jp > 3.0:
                st.warning(f"⚠️ **Cảnh báo USD/JPY:** Khoảng cách lãi suất US-JP cực lớn ({spread_jp:.2f}%). Đồng Yên sẽ tiếp tục yếu đi so với USD cho đến khi BOJ thắt chặt chính sách.")
            else:
                st.info("🔵 **USD/JPY:** Chênh lệch lãi suất đang thu hẹp, đồng Yên có cơ hội hồi phục.")

    else:
        st.warning("Đang chờ dữ liệu từ máy chủ...")

except Exception as e:
    st.error(f"Lỗi: {e}")
