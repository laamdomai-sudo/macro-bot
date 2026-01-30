import streamlit as st
import pandas as pd
import pandas_datareader.data as web
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. Cấu hình trang
st.set_page_config(page_title="USD vs JPY Analysis", layout="wide")
st.title("🏦 Phân Tích Tương Quan Lãi Suất USD - JPY")
st.markdown("---")

@st.cache_data(ttl=3600)
def get_fred_data():
    end = datetime.now()
    start = end - timedelta(days=365 * 2) # Lấy dữ liệu 2 năm gần nhất
    
    # DGS10: Lợi suất 10 năm Mỹ (USD)
    # JPNCB10Y: Lợi suất 10 năm Nhật (JPY) - Nguồn từ FRED
    # DEXJPUS: Tỷ giá USD/JPY
    symbols = {
        'DGS10': 'USD_10Y',
        'IRLTLT01JPM156N': 'JPY_10Y',
        'DEXJPUS': 'USDJPY'
    }
    
    try:
        df = web.DataReader(list(symbols.keys()), 'fred', start, end)
        df.rename(columns=symbols, inplace=True)
        return df.ffill().dropna()
    except Exception as e:
        st.error(f"Lỗi kết nối máy chủ FRED: {e}")
        return pd.DataFrame()

try:
    with st.spinner('📡 Đang kết nối máy chủ FRED (St. Louis Fed)...'):
        df = get_fred_data()

    if not df.empty:
        # Tính toán chênh lệch lãi suất (Spread)
        df['Spread'] = df['USD_10Y'] - df['JPY_10Y']
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]

        # 2. Hiển thị Metrics chính
        c1, c2, c3 = st.columns(3)
        c1.metric("Lãi suất Mỹ (US10Y)", f"{curr['USD_10Y']:.2f}%", f"{curr['USD_10Y'] - prev['USD_10Y']:.2f}%")
        c2.metric("Lãi suất Nhật (JP10Y)", f"{curr['JPY_10Y']:.3f}%", f"{curr['JPY_10Y'] - prev['JPY_10Y']:.3f}%")
        c3.metric("Tỷ giá USD/JPY", f"{curr['USDJPY']:.2f}", f"{curr['USDJPY'] - prev['USDJPY']:.2f}")

        # --- 🤖 3. HỆ THỐNG PHÂN TÍCH TỰ ĐỘNG ---
        st.subheader("🤖 Phân Tích Tương Quan Liên Thị Trường")
        col_text, col_spread = st.columns([1, 1.5])
        
        with col_text:
            spread_val = curr['Spread']
            st.markdown(f"#### Chênh lệch lãi suất: `{spread_val:.2f}%`")
            
            if spread_val > 3.5:
                st.error("🚨 **Carry Trade cực thịnh:** Khoảng cách lãi suất rất lớn. Nhà đầu tư có xu hướng vay JPY để mua USD, khiến đồng Yên chịu áp lực giảm giá nặng nề.")
            elif spread_val < 2.5:
                st.success("🟢 **Thu hẹp khoảng cách:** Áp lực lên đồng Yên đang giảm bớt. Đây là tín hiệu JPY có thể hồi phục mạnh mẽ.")
            else:
                st.info("🔄 **Trạng thái cân bằng:** Chênh lệch đang duy trì ở mức trung bình.")
            
            st.caption("Lưu ý: Khi đường Spread (Vùng xanh dưới biểu đồ) đi lên, tỷ giá USD/JPY thường tăng theo.")

        with col_spread:
            # Biểu đồ vùng cho Spread
            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(x=df.index, y=df['Spread'], fill='tozeroy', name="Chênh lệch (Spread)", line=dict(color='#00FFCC')))
            fig_s.update_layout(height=250, template="plotly_dark", margin=dict(t=0, b=0), showlegend=False, 
                                title="Lịch sử Chênh lệch Lãi suất (US - JP)")
            st.plotly_chart(fig_s, use_container_width=True)

        # --- 4. BIỂU ĐỒ TƯƠNG QUAN CHÍNH ---
        st.subheader("📈 So sánh Lãi suất & Tỷ giá thực tế")
        fig = go.Figure()
        
        # Lãi suất (Trục trái)
        fig.add_trace(go.Scatter(x=df.index, y=df['USD_10Y'], name="Lãi suất USD (10Y)", line=dict(color='#FF4B4B', width=2.5)))
        fig.add_trace(go.Scatter(x=df.index, y=df['JPY_10Y'], name="Lãi suất JPY (10Y)", line=dict(color='#1E88E5', width=2)))
        
        # Tỷ giá (Trục phải)
        fig.add_trace(go.Scatter(x=df.index, y=df['USDJPY'], name="Tỷ giá USD/JPY (Trục phải)", 
                                 yaxis="y2", line=dict(color='#FFFFFF', width=1.5, dash='dot')))

        fig.update_layout(
            height=600, template="plotly_dark", hovermode="x unified",
            yaxis=dict(title="Lãi suất (%)", tickformat=".2f"),
            yaxis2=dict(title="USD/JPY Price", overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
            xaxis=dict(rangeslider=dict(visible=True))
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("❌ Không thể lấy dữ liệu từ FRED. Hãy kiểm tra lại kết nối internet.")

except Exception as e:
    st.error(f"Lỗi hệ thống: {e}")
