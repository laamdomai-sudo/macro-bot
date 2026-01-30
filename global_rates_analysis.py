import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Cấu hình trang
st.set_page_config(page_title="Global Rates Dashboard", layout="wide")
st.title("🌍 Biểu Đồ Lãi Suất Các Đồng Tiền Chủ Chốt (Real-time)")
st.markdown("So sánh lợi suất trái phiếu Chính phủ 10 năm (Benchmark Rates)")

# Hàm tải dữ liệu trực tiếp từ CSV của FRED
@st.cache_data(ttl=3600)
def fetch_fred_csv(series_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        data = pd.read_csv(url, index_col=0, parse_dates=True, na_values='.')
        return data
    except Exception as e:
        return pd.DataFrame()

try:
    with st.spinner('📡 Đang trích xuất dữ liệu vĩ mô toàn cầu...'):
        # Định nghĩa các mã Series ID trên FRED
        symbols = {
            "DGS10": "USD (Mỹ)",
            "IRLTLT01EZM156N": "EUR (Khu vực Euro)",
            "IRLTLT01JPM156N": "JPY (Nhật Bản)",
            "IRLTLT01GBM156N": "GBP (Anh)",
            "CHNRYLD2Y": "CNY (Trung Quốc - 2Y)*" # CNY thường dùng kỳ hạn ngắn hơn để theo dõi
        }
        
        data_frames = []
        for sid, name in symbols.items():
            df_temp = fetch_fred_csv(sid)
            if not df_temp.empty:
                df_temp.columns = [name]
                data_frames.append(df_temp)
        
        # Kết hợp và xử lý dữ liệu
        df_final = pd.concat(data_frames, axis=1)
        df_final = df_final.ffill().dropna().last('5Y') # Lấy 5 năm gần nhất

    if not df_final.empty:
        # 2. Hiển thị Metrics hiện tại
        curr = df_final.iloc[-1]
        cols = st.columns(len(symbols))
        for i, (name, val) in enumerate(curr.items()):
            cols[i].metric(name, f"{val:.2f}%")

        # 3. Vẽ biểu đồ Plotly
        st.subheader("📈 Biến Động Lãi Suất Toàn Cầu (2021 - 2026)")
        fig = go.Figure()
        
        colors = ['#FF4B4B', '#1E88E5', '#00C853', '#AA00FF', '#FFD700']
        
        for i, col in enumerate(df_final.columns):
            fig.add_trace(go.Scatter(
                x=df_final.index, 
                y=df_final[col], 
                name=col,
                line=dict(width=2, color=colors[i % len(colors)])
            ))

        fig.update_layout(
            height=600,
            template="plotly_dark",
            hovermode="x unified",
            yaxis=dict(title="Lãi suất (%)", gridcolor='rgba(255,255,255,0.1)'),
            xaxis=dict(title="Thời gian", rangeslider=dict(visible=True), gridcolor='rgba(255,255,255,0.1)'),
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # 4. Phân tích tương quan
        st.divider()
        st.subheader("💡 Nhận Định Vĩ Mô")
        
        max_rate = curr.idxmax()
        min_rate = curr.idxmin()
        
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"🚀 **Đồng tiền có lãi suất cao nhất:** `{max_rate}` ({curr[max_rate]:.2f}%)")
            st.write("Dòng vốn thường có xu hướng chảy về các đồng tiền có lãi suất thực cao để tìm kiếm lợi nhuận.")
        with c2:
            st.write(f"📉 **Đồng tiền có lãi suất thấp nhất:** `{min_rate}` ({curr[min_rate]:.2f}%)")
            st.write("Các đồng tiền lãi suất thấp thường được dùng làm 'Funding Currency' trong các chiến lược Carry Trade.")

    else:
        st.error("⚠️ Không thể tải dữ liệu. Vui lòng thử lại sau.")

except Exception as e:
    st.error(f"Lỗi hệ thống: {e}")
