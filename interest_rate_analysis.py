import streamlit as st
import pandas as pd
import pandas_datareader.data as web
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. Cấu hình trang
st.set_page_config(page_title="USD vs JPY Macro", layout="wide")
st.title("🏦 Phân Tích Vĩ Mô: Lãi Suất & Lạm Phát USD - JPY")

@st.cache_data(ttl=3600)
def get_macro_data():
    end = datetime.now()
    start = end - timedelta(days=365 * 5) # Lấy 5 năm để thấy rõ chu kỳ
    
    # DGS10: Lãi suất 10Y Mỹ, IRLTLT01JPM156N: 10Y Nhật
    # DEXJPUS: Tỷ giá USD/JPY, CPIAUCSL: Lạm phát Mỹ
    symbols = {
        'DGS10': 'USD_10Y',
        'IRLTLT01JPM156N': 'JPY_10Y',
        'DEXJPUS': 'USDJPY',
        'CPIAUCSL': 'US_CPI'
    }
    
    try:
        df = web.DataReader(list(symbols.keys()), 'fred', start, end)
        df.rename(columns=symbols, inplace=True)
        # Tính lạm phát theo năm (%) từ chỉ số CPI
        df['US_Inflation'] = df['US_CPI'].pct_change(periods=12) * 100
        return df.ffill().dropna()
    except Exception as e:
        st.error(f"Lỗi kết nối FRED: {e}")
        return pd.DataFrame()

try:
    with st.spinner('📡 Đang tải dữ liệu từ FRED (St. Louis Fed)...'):
        df = get_macro_data()

    if not df.empty:
        curr = df.iloc[-1]
        prev = df.iloc[-2]

        # 2. Metrics Vĩ Mô
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("USD 10Y Yield", f"{curr['USD_10Y']:.2f}%", f"{curr['USD_10Y'] - prev['USD_10Y']:.2f}%")
        c2.metric("JPY 10Y Yield", f"{curr['JPY_10Y']:.3f}%")
        c3.metric("Lạm phát Mỹ (CPI)", f"{curr['US_Inflation']:.1f}%")
        c4.metric("Tỷ giá USD/JPY", f"{curr['USDJPY']:.2f}")

        # --- 🤖 3. HỆ THỐNG DỰ BÁO LÃI SUẤT ---
        st.subheader("🔮 Phân Tích & Dự Báo Chính Sách")
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("#### 🎯 Áp lực lên FED (Mỹ)")
            inf_val = curr['US_Inflation']
            if inf_val > 3.0:
                st.error(f"⚠️ **Lạm phát cao ({inf_val:.1f}%):** FED khó có thể giảm lãi suất sớm. USD sẽ tiếp tục duy trì sức mạnh.")
            elif inf_val < 2.5:
                st.success(f"✅ **Lạm phát hạ nhiệt ({inf_val:.1f}%):** Mở đường cho chu kỳ giảm lãi suất. USD có thể suy yếu.")
            else:
                st.info("🔄 **Vùng ổn định:** FED sẽ duy trì trạng thái quan sát.")

        with col_b:
            st.markdown("#### 💴 Áp lực lên BOJ (Nhật Bản)")
            spread = curr['USD_10Y'] - curr['JPY_10Y']
            if spread > 4.0:
                st.error(f"🚨 **Carry Trade Quá Nhiệt:** Chênh lệch lãi suất {spread:.2f}% là cực lớn. JPY sẽ bị bán tháo mạnh.")
            else:
                st.success(f"🟢 **Áp lực giảm:** Chênh lệch {spread:.2f}% đang thu hẹp, hỗ trợ JPY hồi phục.")

        # --- 4. BIỂU ĐỒ TỔNG HỢP ---
        st.subheader("📈 Biểu đồ Tương quan Lãi suất & Lạm phát")
        fig = go.Figure()
        
        # Đường Lãi suất & Lạm phát
        fig.add_trace(go.Scatter(x=df.index, y=df['USD_10Y'], name="Lãi suất Mỹ", line=dict(color='#FF4B4B', width=2)))
        fig.add_trace(go.Scatter(x=df.index, y=df['US_Inflation'], name="Lạm phát Mỹ (CPI)", line=dict(color='#00FF00', dash='dot')))
        fig.add_trace(go.Scatter(x=df.index, y=df['JPY_10Y'], name="Lãi suất Nhật", line=dict(color='#1E88E5')))
        
        # Tỷ giá (Trục phải)
        fig.add_trace(go.Scatter(x=df.index, y=df['USDJPY'], name="USD/JPY (Phải)", yaxis="y2", line=dict(color='white', width=1, opacity=0.5)))

        fig.update_layout(
            height=600, template="plotly_dark", hovermode="x unified",
            yaxis=dict(title="Lãi suất / Lạm phát (%)"),
            yaxis2=dict(overlaying="y", side="right", showgrid=False, title="USD/JPY Price"),
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
            xaxis=dict(rangeslider=dict(visible=True))
        )
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi: {e}")
