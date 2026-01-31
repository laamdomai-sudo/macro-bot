import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Real-time Macro Dashboard", layout="wide")

st.title("📈 Bảng Điều Khiển Tài Chính Thực Tế 2026")
st.markdown("Dữ liệu được lấy trực tiếp từ **Yahoo Finance** và kết hợp dự báo vĩ mô.")

# 1. Lấy dữ liệu thực tế từ Yahoo Finance
@st.cache_data(ttl=3600) # Lưu bộ nhớ đệm 1 giờ
def load_real_data():
    # GC=F là Vàng, ^VNINDEX là chỉ số chứng khoán VN (nếu Yahoo có update) 
    # Hoặc dùng ^GSPC (S&P 500) để thay thế cho xu hướng toàn cầu
    gold = yf.download("GC=F", start="2024-01-01", end="2026-12-31")['Close']
    vni = yf.download("^GSPC", start="2024-01-01", end="2026-12-31")['Close'] # Demo bằng S&P500
    return gold, vni

try:
    gold_data, vni_data = load_real_data()

    # 2.Sidebar cấu hình Lạm phát & Lãi suất (Vì không có API thực thời gian thực cho CPI VN)
    st.sidebar.header("Thông số Vĩ mô Dự báo (2026)")
    cpi_val = st.sidebar.slider("Tỷ lệ Lạm phát dự kiến (%)", 2.0, 10.0, 4.5)
    ir_val = st.sidebar.slider("Lãi suất huy động (%)", 3.0, 12.0, 7.0)
    
    real_rate = ir_val - cpi_val

    # 3. Tính toán tương quan
    col1, col2, col3 = st.columns(3)
    current_gold = gold_data.iloc[-1]
    col1.metric("Giá Vàng Hiện Tại", f"{current_gold:,.2f} USD/oz")
    col2.metric("Lãi Suất Thực", f"{real_rate:.2f} %", delta_color="inverse")
    col3.metric("Xu Hướng Chứng Khoán", f"{vni_data.iloc[-1]:,.2f} pts")

    # 4. Vẽ biểu đồ dữ liệu thực
    fig, ax1 = plt.subplots(figsize=(10, 5))

    # Trục Vàng
    ax1.set_ylabel("Giá Vàng (USD)", color="gold", fontweight="bold")
    ax1.plot(gold_data.index, gold_data, color="gold", label="Giá Vàng thực tế")
    ax1.tick_params(axis='y', labelcolor="gold")

    # Trục Chứng khoán
    ax2 = ax1.twinx()
    ax2.set_ylabel("Chỉ số Chứng khoán", color="seagreen", fontweight="bold")
    ax2.plot(vni_data.index, vni_data, color="seagreen", alpha=0.6, label="Chứng khoán")
    ax2.tick_params(axis='y', labelcolor="seagreen")

    plt.title("Biến động Vàng & Chứng khoán (Dữ liệu Yahoo Finance)")
    st.pyplot(fig)

    # 5. Phân tích Quy luật
    st.subheader("🧐 Đánh giá 'Vật cực tất phản'")
    if current_gold > 2800 and real_rate < 1:
        st.warning("⚠️ **VẬT CỰC:** Giá vàng đang ở vùng đỉnh lịch sử trong khi lãi suất thực quá thấp. Rủi ro bong bóng rất cao!")
    elif real_rate > 4:
        st.info("🔄 **TẤT PHẢN:** Lãi suất thực đang tăng cao. Dòng tiền có xu hướng rời bỏ Vàng để quay lại Ngân hàng và Chứng khoán giá rẻ.")

except Exception as e:
    st.error(f"Lỗi khi lấy dữ liệu: {e}")
    st.info("Gợi ý: Kiểm tra kết nối internet hoặc giới hạn API của Yahoo Finance.")
