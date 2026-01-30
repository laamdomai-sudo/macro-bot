import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Cấu hình trang
st.set_page_config(page_title="VN Macro Intelligence", layout="wide")
st.title("🇻🇳 Hệ Thống Giám Sát Cung Tiền & Tín Dụng Việt Nam")

# Hàm mô phỏng việc lấy dữ liệu thực tế từ SBV/World Bank
# (Trong thực tế, bạn có thể dùng requests để lấy file Excel từ sbv.gov.vn)
@st.cache_data(ttl=86400) # Lưu bộ nhớ đệm 24h
def fetch_vn_monetary_data():
    # Giả lập dữ liệu được cấu trúc lại từ các báo cáo thống kê của SBV
    data = {
        'Date': pd.date_range(start='1995-01-01', periods=31, freq='YS'),
        'M2_Growth': [22.5, 24.1, 25.0, 23.5, 21.0, 35.2, 36.8, 30.1, 28.5, 24.2, 26.1, 29.5, 46.1, 35.2, 28.0, 
                      25.3, 12.1, 15.2, 16.5, 17.8, 14.5, 16.2, 15.0, 12.5, 13.6, 14.5, 10.5, 11.2, 12.5, 10.8, 12.1],
        'Credit_Growth': [25.0, 28.2, 22.0, 18.5, 16.0, 38.1, 40.2, 35.5, 30.2, 25.1, 28.5, 32.1, 53.8, 39.5, 37.2, 
                         29.1, 14.2, 12.5, 12.8, 14.2, 17.1, 18.5, 18.2, 13.9, 13.5, 12.1, 13.2, 14.5, 12.2, 11.5, 13.8]
    }
    df = pd.DataFrame(data).set_index('Date')
    return df

try:
    df_vn = fetch_vn_monetary_data()
    
    # --- THANH ĐIỀU KHIỂN ---
    st.sidebar.header("🔍 Bộ Lọc Phân Tích")
    view_period = st.sidebar.slider("Số năm quan sát:", 5, 30, 30)
    df_view = df_vn.last(f'{view_period}Y')

    # --- CHỈ SỐ THÔNG MINH ---
    latest_m2 = df_view['M2_Growth'].iloc[-1]
    latest_credit = df_view['Credit_Growth'].iloc[-1]
    
    # Tính toán "Chỉ số bơm tiền thực" (Gap giữa Tín dụng và M2)
    # Nếu Tín dụng > M2 quá nhiều: Hệ thống ngân hàng đang căng thẳng thanh khoản
    liquidity_gap = latest_credit - latest_m2

    c1, c2, c3 = st.columns(3)
    c1.metric("Tăng trưởng M2", f"{latest_m2:.1f}%")
    c2.metric("Tăng trưởng Tín dụng", f"{latest_credit:.1f}%")
    c3.metric("Chênh lệch Thanh khoản", f"{liquidity_gap:.1f}%", delta_color="inverse")

    # --- BIỂU ĐỒ TRỰC QUAN ---
    st.subheader(f"📊 Diễn biến Cung tiền & Tín dụng ({view_period} năm)")
    
    fig = go.Figure()
    
    # Vẽ M2
    fig.add_trace(go.Scatter(
        x=df_view.index, y=df_view['M2_Growth'],
        name="Tăng trưởng M2 (Nguồn cung)",
        line=dict(color='#00d1ff', width=2),
        fill='tozeroy'
    ))
    
    # Vẽ Tín dụng
    fig.add_trace(go.Scatter(
        x=df_view.index, y=df_view['Credit_Growth'],
        name="Tăng trưởng Tín dụng (Hấp thụ)",
        line=dict(color='#ff4b4b', width=2, dash='dot')
    ))

    fig.update_layout(
        height=500, template="plotly_dark",
        yaxis=dict(title="Tỷ lệ %", gridcolor='rgba(255,255,255,0.1)'),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- PHÂN TÍCH THÔNG MINH ---
    st.divider()
    st.subheader("🤖 Nhận Định Chuyên Gia (AI Insights)")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.write("### 📌 Trạng thái Chu kỳ")
        if latest_credit > 20:
            st.error("🚨 **CẢNH BÁO TĂNG TRƯỞNG NÓNG:** Tín dụng đang ở mức rủi ro cao. Lịch sử cho thấy đây là tiền đề của lạm phát và bong bóng tài sản (giống giai đoạn 2007).")
        elif latest_credit > 14:
            st.warning("⚠️ **GIAI ĐOẠN MỞ RỘNG:** Nền kinh tế đang được bơm vốn mạnh mẽ. Tốt cho chứng khoán nhưng cần chú ý kiểm soát chất lượng nợ.")
        else:
            st.success("✅ **KIỂM SOÁT ỔN ĐỊNH:** Mức tăng trưởng hiện tại nằm trong khung mục tiêu của Chính phủ (12-14%), hỗ trợ tăng trưởng bền vững.")

    with col_b:
        st.write("### 🏦 Phân tích Thanh khoản")
        if liquidity_gap > 3:
            st.warning("⚠️ **THANH KHOẢN HẸP:** Tín dụng tăng nhanh hơn huy động vốn (M2). Lãi suất ngân hàng có xu hướng chịu áp lực tăng để hút tiền gửi.")
        else:
            st.info("ℹ️ **THANH KHOẢN DỒI DÀO:** Hệ thống ngân hàng có đủ dư địa để giải ngân vốn mà không gây áp lực lớn lên lãi suất huy động.")

except Exception as e:
    st.error(f"Lỗi hệ thống: {e}")
