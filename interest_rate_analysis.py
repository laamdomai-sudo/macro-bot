import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Cấu hình trang
st.set_page_config(page_title="Macro FRED Live", layout="wide")
st.title("🏦 Phân Tích Vĩ Mô: USD vs JPY (Nguồn: FRED)")

# Hàm tải dữ liệu trực tiếp từ CSV của FRED để tránh lỗi thư viện
@st.cache_data(ttl=3600)
def fetch_fred_csv(series_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        data = pd.read_csv(url, index_col=0, parse_dates=True, na_values='.')
        return data
    except Exception as e:
        st.error(f"Không thể tải {series_id}: {e}")
        return pd.DataFrame()

try:
    with st.spinner('📡 Đang truy vấn trực tiếp máy chủ St. Louis Fed...'):
        # Tải riêng biệt từng chỉ số
        usd_10y = fetch_fred_csv("DGS10")        # Lãi suất 10Y Mỹ
        jpy_10y = fetch_fred_csv("IRLTLT01JPM156N") # Lãi suất 10Y Nhật
        us_cpi = fetch_fred_csv("CPIAUCSL")     # Chỉ số lạm phát Mỹ
        usdjpy = fetch_fred_csv("DEXJPUS")      # Tỷ giá USD/JPY

        # Kết hợp dữ liệu
        df = pd.concat([usd_10y, jpy_10y, us_cpi, usdjpy], axis=1)
        df.columns = ['USD_10Y', 'JPY_10Y', 'US_CPI', 'USDJPY']
        
        # Xử lý dữ liệu
        df = df.ffill().dropna().last('2Y') # Lấy 2 năm gần nhất
        df['US_Inflation'] = df['US_CPI'].pct_change(periods=12) * 100
        df = df.dropna()

    if not df.empty:
        curr = df.iloc[-1]
        prev = df.iloc[-2]

        # 2. Hiển thị Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("USD 10Y Yield", f"{curr['USD_10Y']:.2f}%", f"{curr['USD_10Y'] - prev['USD_10Y']:.2f}%")
        c2.metric("JPY 10Y Yield", f"{curr['JPY_10Y']:.3f}%")
        c3.metric("Lạm phát Mỹ", f"{curr['US_Inflation']:.1f}%")
        c4.metric("Tỷ giá USD/JPY", f"{curr['USDJPY']:.2f}")

        # 3. Biểu đồ chính
        st.subheader("📈 Tương Quan Lãi suất, Lạm phát & Tỷ giá")
        fig = go.Figure()
        
        # Trục trái: Lãi suất & Lạm phát
        fig.add_trace(go.Scatter(x=df.index, y=df['USD_10Y'], name="Lãi suất Mỹ (10Y)", line=dict(color='#FF4B4B', width=2)))
        fig.add_trace(go.Scatter(x=df.index, y=df['US_Inflation'], name="Lạm phát Mỹ (CPI)", line=dict(color='#00FF00', dash='dot')))
        fig.add_trace(go.Scatter(x=df.index, y=df['JPY_10Y'], name="Lãi suất Nhật (10Y)", line=dict(color='#1E88E5')))
        
        # Trục phải: Tỷ giá
        fig.add_trace(go.Scatter(x=df.index, y=df['USDJPY'], name="Tỷ giá USD/JPY (Phải)", 
                                 yaxis="y2", line=dict(color='white', width=1.5, opacity=0.6)))

        fig.update_layout(
            height=650, template="plotly_dark", hovermode="x unified",
            yaxis=dict(title="Lãi suất / Lạm phát (%)"),
            yaxis2=dict(title="USD/JPY Price", overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
            xaxis=dict(rangeslider=dict(visible=True))
        )
        st.plotly_chart(fig, use_container_width=True)

        # 4. Nhận định tự động
        st.divider()
        st.subheader("🤖 Nhận Định Vĩ Mô")
        spread = curr['USD_10Y'] - curr['JPY_10Y']
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Chênh lệch lãi suất (Spread): {spread:.2f}%**")
            st.write("Nếu lạm phát Mỹ vẫn duy trì trên 3%, FED sẽ khó hạ lãi suất, giữ cho Spread cao và tạo áp lực giảm giá lên JPY.")
        with col2:
            st.write("**Mối tương quan:**")
            st.caption("Hãy chú ý giai đoạn Lạm phát (Xanh lá) tăng vọt, Lãi suất Mỹ (Đỏ) thường tăng theo sau đó để kiềm chế, kéo theo USD/JPY tăng mạnh.")

    else:
        st.warning("⚠️ Đang chờ dữ liệu cập nhật từ FRED...")

except Exception as e:
    st.error(f"Lỗi vận hành: {e}")
