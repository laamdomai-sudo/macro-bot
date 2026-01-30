import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Cấu hình trang
st.set_page_config(page_title="Macro Inversion Alert", layout="wide")
st.title("🚨 Cảnh Báo Đảo Ngược Đường Cong Lợi Suất")

@st.cache_data(ttl=3600)
def fetch_fred_csv(series_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        data = pd.read_csv(url, index_col=0, parse_dates=True, na_values='.')
        return data if not data.empty else pd.DataFrame()
    except:
        return pd.DataFrame()

# Danh mục mã 2Y và 10Y để so sánh
macro_pairs = {
    "Mỹ (USD)": {"2Y": "DGS2", "10Y": "DGS10"},
    "Châu Âu (EUR)": {"2Y": "IRT3TR01EZM156N", "10Y": "IRLTLT01EZM156N"},
    "Nhật Bản (JPY)": {"2Y": "IR3TIB01JPM156N", "10Y": "IRLTLT01JPM156N"},
    "Anh (GBP)": {"2Y": "IRT3TR01GBM156N", "10Y": "IRLTLT01GBM156N"}
}

try:
    with st.spinner('📡 Đang quét tín hiệu đảo ngược từ FRED...'):
        all_data = {}
        for country, codes in macro_pairs.items():
            df_2y = fetch_fred_csv(codes["2Y"])
            df_10y = fetch_fred_csv(codes["10Y"])
            if not df_2y.empty and not df_10y.empty:
                combined = pd.concat([df_2y, df_10y], axis=1).ffill().dropna()
                combined.columns = ['2Y', '10Y']
                combined['Gap'] = combined['10Y'] - combined['2Y']
                all_data[country] = combined.last('2Y')

    # --- SECTION 1: BẢNG ĐIỀU KHIỂN CẢNH BÁO ---
    st.subheader("⚠️ Trạng thái đường cong lợi suất hiện tại")
    cols = st.columns(len(all_data))
    
    for i, (country, df) in enumerate(all_data.items()):
        latest_gap = df['Gap'].iloc[-1]
        with cols[i]:
            if latest_gap < 0:
                st.error(f"**{country}**")
                st.metric("10Y - 2Y Gap", f"{latest_gap:.2f}%", "ĐẢO NGƯỢC")
            else:
                st.success(f"**{country}**")
                st.metric("10Y - 2Y Gap", f"{latest_gap:.2f}%", "BÌNH THƯỜNG")

    # --- SECTION 2: BIỂU ĐỒ CHI TIẾT ---
    st.divider()
    target_country = st.selectbox("Chọn quốc gia để soi chi tiết lịch sử đảo ngược:", options=list(all_data.keys()))
    
    plot_df = all_data[target_country]
    
    fig = go.Figure()
    # Vẽ vùng 0 để dễ quan sát
    fig.add_hline(y=0, line_dash="solid", line_color="white", line_width=1)
    
    # Vẽ đường Gap (10Y - 2Y)
    fig.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df['Gap'],
        name="10Y-2Y Spread",
        fill='tozeroy',
        line=dict(color='#FF3366' if plot_df['Gap'].iloc[-1] < 0 else '#00FFCC')
    ))

    fig.update_layout(
        height=450, template="plotly_dark",
        title=f"Lịch sử chênh lệch 10Y-2Y tại {target_country}",
        yaxis=dict(title="Chênh lệch (%)"),
        xaxis=dict(rangeslider=dict(visible=True))
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- KIẾN THỨC CHIẾN THUẬT ---
    st.info("""
    **Chiến thuật quan sát:** 1. Khi đường Spread rơi xuống dưới 0 (vùng đỏ): Thị trường đang kỳ vọng suy thoái.
    2. Khi đường Spread bắt đầu "ngoi lên" lại từ vùng âm (Un-inverting): Đây thường là lúc suy thoái thực sự bắt đầu xảy ra trên diện rộng.
    """)

except Exception as e:
    st.error(f"Lỗi: {e}")
