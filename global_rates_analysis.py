import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Cấu hình trang
st.set_page_config(page_title="Custom Global Rates", layout="wide")
st.title("🌍 Dashboard Lãi Suất Toàn Cầu & Phân Tích Spread")

# Hàm tải dữ liệu từ FRED
@st.cache_data(ttl=3600)
def fetch_fred_csv(series_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        data = pd.read_csv(url, index_col=0, parse_dates=True, na_values='.')
        return data
    except:
        return pd.DataFrame()

# 2. Khởi tạo danh mục các đồng tiền
symbols = {
    "USD (Mỹ)": "DGS10",
    "EUR (Châu Âu)": "IRLTLT01EZM156N",
    "JPY (Nhật Bản)": "IRLTLT01JPM156N",
    "GBP (Anh)": "IRLTLT01GBM156N",
    "CNY (Trung Quốc)": "CHNRYLD2Y"
}

try:
    with st.spinner('📡 Đang đồng bộ dữ liệu vĩ mô...'):
        data_frames = []
        for name, sid in symbols.items():
            df_temp = fetch_fred_csv(sid)
            if not df_temp.empty:
                df_temp.columns = [name]
                data_frames.append(df_temp)
        
        df_final = pd.concat(data_frames, axis=1).ffill().dropna().last('5Y')

    # --- SIDEBAR: ĐIỀU KHIỂN ---
    st.sidebar.header("🎯 Tùy chọn hiển thị")
    
    # Tính năng 1: Chọn đồng tiền hiển thị
    selected_currencies = st.sidebar.multiselect(
        "Chọn các đồng tiền muốn xem:",
        options=list(symbols.keys()),
        default=list(symbols.keys())[:3] # Mặc định hiện 3 cái đầu
    )

    # Tính năng 2: Chọn cặp so sánh Spread
    st.sidebar.divider()
    st.sidebar.header("⚖️ So sánh Chênh lệch (Spread)")
    base_cur = st.sidebar.selectbox("Đồng tiền cơ sở (A):", options=list(symbols.keys()), index=0)
    target_cur = st.sidebar.selectbox("Đồng tiền so sánh (B):", options=list(symbols.keys()), index=2)

    if not df_final.empty:
        # --- SECTION 1: BIỂU ĐỒ CHÍNH ---
        st.subheader("📊 Diễn biến Lãi suất 10 Năm")
        if selected_currencies:
            fig = go.Figure()
            for col in selected_currencies:
                fig.add_trace(go.Scatter(x=df_final.index, y=df_final[col], name=col, line=dict(width=2)))
            
            fig.update_layout(
                height=500, template="plotly_dark", hovermode="x unified",
                yaxis=dict(title="Lãi suất (%)", gridcolor='rgba(255,255,255,0.1)'),
                xaxis=dict(rangeslider=dict(visible=True)),
                legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Vui lòng chọn ít nhất một đồng tiền để hiển thị biểu đồ.")

        # --- SECTION 2: BIỂU ĐỒ SPREAD ---
        st.divider()
        st.subheader(f"⚖️ Chênh lệch Lãi suất: {base_cur} - {target_cur}")
        
        spread_data = df_final[base_cur] - df_final[target_cur]
        curr_spread = spread_data.iloc[-1]
        
        c1, c2 = st.columns([1, 3])
        with c1:
            st.metric(f"Spread Hiện Tại", f"{curr_spread:.2f}%", f"{curr_spread - spread_data.iloc[-10]:.2f}% (10 phiên)")
            st.write(f"Ý nghĩa: Khi đường này tăng, đồng `{base_cur}` có xu hướng mạnh lên so với `{target_cur}`.")
            
        with c2:
            fig_spread = go.Figure()
            fig_spread.add_trace(go.Scatter(
                x=spread_data.index, y=spread_data, 
                fill='tozeroy', name="Spread",
                line=dict(color='#00FFCC')
            ))
            fig_spread.update_layout(
                height=300, template="plotly_dark",
                yaxis=dict(title="Chênh lệch (%)", gridcolor='rgba(255,255,255,0.1)'),
                margin=dict(t=10, b=10)
            )
            st.plotly_chart(fig_spread, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi vận hành: {e}")
