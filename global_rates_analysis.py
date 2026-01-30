import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Cấu hình trang chuyên sâu
st.set_page_config(page_title="Intelligent Macro Hub", layout="wide")
st.title("🧠 Hệ Thống Phân Tích Vĩ Mô Thông Minh")

@st.cache_data(ttl=3600)
def fetch_fred_csv(series_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        data = pd.read_csv(url, index_col=0, parse_dates=True, na_values='.')
        return data if not data.empty else pd.DataFrame()
    except:
        return pd.DataFrame()

try:
    with st.spinner('🤖 Thuật toán đang quét dữ liệu thị trường...'):
        # Tải dữ liệu chính (Mỹ là đại diện dòng tiền thế giới)
        us_2y = fetch_fred_csv("DGS2")
        us_10y = fetch_fred_csv("DGS10")
        vix = fetch_fred_csv("VIXCLS") # Chỉ số đo lường trạng thái sợ hãi
        
        # Kết hợp dữ liệu
        df = pd.concat([us_2y, us_10y, vix], axis=1).ffill().dropna().last('3Y')
        df.columns = ['US2Y', 'US10Y', 'VIX']
        df['Gap'] = df['US10Y'] - df['US2Y']

    if not df.empty:
        curr = df.iloc[-1]
        
        # --- THUẬT TOÁN CHẤM ĐIỂM RỦI RO (MACRO RISK SCORE) ---
        risk_score = 0
        reasons = []
        
        # Kiểm tra Đảo ngược
        if curr['Gap'] < 0:
            risk_score += 40
            reasons.append("🚩 Đường cong lợi suất Đảo ngược (Cảnh báo suy thoái)")
        
        # Kiểm tra VIX (Sợ hãi)
        if curr['VIX'] > 30:
            risk_score += 40
            reasons.append("🚩 VIX trên 30: Thị trường đang hoảng loạn cực độ")
        elif curr['VIX'] > 20:
            risk_score += 20
            reasons.append("⚠️ VIX trên 20: Tâm lý bất an đang gia tăng")
            
        # Kiểm tra xu hướng ngắn hạn
        if curr['US2Y'] > df['US2Y'].iloc[-20]:
            risk_score += 20
            reasons.append("⚠️ Lãi suất ngắn hạn đang tăng: Áp lực thắt chặt tiền tệ")

        # --- HIỂN THỊ ĐIỂM RỦI RO ---
        st.subheader("📊 Đánh giá rủi ro hệ thống")
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.metric("Macro Risk Score", f"{risk_score}/100")
            if risk_score >= 60:
                st.error("CHẾ ĐỘ: PHÒNG THỦ CỰC ĐỘ")
            elif risk_score >= 30:
                st.warning("CHẾ ĐỘ: THẬN TRỌNG")
            else:
                st.success("CHẾ ĐỘ: TĂNG TRƯỞNG")
        
        with c2:
            st.write("**Các yếu tố ảnh hưởng hiện tại:**")
            for r in reasons:
                st.write(r)

        # --- BIỂU ĐỒ TƯƠNG QUAN THÔNG MINH ---
        st.divider()
        st.subheader("📈 Biểu đồ Tương quan: Lãi suất vs Tâm lý Sợ hãi")
        
        fig = go.Figure()
        
        # Vẽ vùng Đảo ngược
        fig.add_trace(go.Scatter(x=df.index, y=df['Gap'], name="10Y-2Y Spread", fill='tozeroy', line=dict(color='#00FFCC')))
        
        # Vẽ VIX lên trục phụ
        fig.add_trace(go.Scatter(x=df.index, y=df['VIX'], name="VIX Index (Tâm lý)", yaxis="y2", line=dict(color='#FFD700', dash='dot')))

        fig.update_layout(
            height=550, template="plotly_dark",
            yaxis=dict(title="Lãi suất Spread (%)"),
            yaxis2=dict(title="VIX Index", overlaying="y", side="right", showgrid=False),
            hovermode="x unified",
            xaxis=dict(rangeslider=dict(visible=True))
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- BẢNG THỐNG KÊ CHI TIẾT ---
        st.subheader("📝 Bảng dữ liệu vĩ mô gần đây")
        st.dataframe(df.tail(10).sort_index(ascending=False), use_container_width=True)

    else:
        st.warning("Đang chờ phản hồi từ máy chủ FRED...")

except Exception as e:
    st.error(f"Lỗi: {e}")
