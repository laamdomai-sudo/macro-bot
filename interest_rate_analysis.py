import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Cấu hình trang
st.set_page_config(page_title="Macro FRED Live", layout="wide")
st.title("🏦 Phân Tích Vĩ Mô: USD vs JPY (Dữ liệu FRED)")

# Hàm tải dữ liệu trực tiếp từ CSV của FRED
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
        # Tải dữ liệu
        usd_10y = fetch_fred_csv("DGS10")        
        jpy_10y = fetch_fred_csv("IRLTLT01JPM156N") 
        us_cpi = fetch_fred_csv("CPIAUCSL")     
        usdjpy = fetch_fred_csv("DEXJPUS")      

        # Kết hợp dữ liệu
        df = pd.concat([usd_10y, jpy_10y, us_cpi, usdjpy], axis=1)
        df.columns = ['USD_10Y', 'JPY_10Y', 'US_CPI', 'USDJPY']
        
        # Xử lý dữ liệu
        df = df.ffill().dropna().last('3Y') 
        df['US_Inflation'] = df['US_CPI'].pct_change(periods=12) * 100
        df = df.dropna()

    if not df.empty:
        curr = df.iloc[-1]
        prev = df.iloc[-2]

        # 2. Metrics - Đã sửa lỗi f-string
        c1, c2, c3, c4 = st.columns(4)
        
        val_usd = f"{curr['USD_10Y']:.2f}%"
        delta_usd = f"{curr['USD_10Y'] - prev['USD_10Y']:.2f}%"
        c1.metric("USD 10Y Yield", val_usd, delta_usd)
        
        c2.metric("JPY 10Y Yield", f"{curr['JPY_10Y']:.3f}%")
        c3.metric("Lạm phát Mỹ", f"{curr['US_Inflation']:.1f}%")
        c4.metric("Tỷ giá USD/JPY", f"{curr['USDJPY']:.2f}")

        # 3. Biểu đồ chính
        st.subheader("📈 Tương Quan Lãi suất, Lạm phát & Tỷ giá")
        fig = go.Figure()
        
        # Đường Lãi suất & Lạm phát (Trục trái)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['USD_10Y'], 
            name="Lãi suất Mỹ (10Y)", 
            line=dict(color='#FF4B4B', width=2.5)
        ))
        
        fig.add_trace(go.Scatter(
            x=df.index, y=df['US_Inflation'], 
            name="Lạm phát Mỹ (CPI)", 
            line=dict(color='#00FF00', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=df.index, y=df['JPY_10Y'], 
            name="Lãi suất Nhật (10Y)", 
            line=dict(color='#1E88E5')
        ))
        
        # Đường Mục tiêu Lạm phát 2%
        fig.add_hline(y=2.0, line_dash="dash", line_color="#FFD700", annotation_text="Mục tiêu FED (2%)")
        
        # Tỷ giá (Trục phải)
        fig.add_trace(go.Scatter(
            x=df.index, 
            y=df['USDJPY'], 
            name="Tỷ giá USD/JPY (Phải)", 
            yaxis="y2", 
            line=dict(color='rgba(255, 255, 255, 0.5)', width=1.5)
        ))

        fig.update_layout(
            height=650, 
            template="plotly_dark", 
            hovermode="x unified",
            yaxis=dict(title="Lãi suất / Lạm phát (%)", gridcolor='rgba(255,255,255,0.1)'),
            yaxis2=dict(title="USD/JPY Price", overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
            xaxis=dict(rangeslider=dict(visible=True), gridcolor='rgba(255,255,255,0.1)')
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # 4. Phân tích tự động
        st.divider()
        st.subheader("🤖 Phân Tích Dòng Tiền")
        spread = curr['USD_10Y'] - curr['JPY_10Y']
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Chênh lệch lãi suất (Spread): {spread:.2f}%**")
            st.write("Khi đường lạm phát (Xanh lá) giảm sâu dưới lãi suất Mỹ (Đỏ), FED thường có xu hướng hạ lãi suất để cân bằng, điều này có thể làm giảm tỷ giá USD/JPY.")
        
        with col2:
            st.write("**Tình trạng lạm phát hiện tại:**")
            if curr['US_Inflation'] > 2.5:
                st.error(f"Lạm phát {curr['US_Inflation']:.1f}% vẫn đang 'nóng'. USD có khả năng duy trì sức mạnh.")
            else:
                st.success("Lạm phát đang tiến về vùng mục tiêu 2%.")

    else:
        st.warning("⚠️ Không thể trích xuất dữ liệu.")

except Exception as e:
    st.error(f"Lỗi vận hành: {e}")
