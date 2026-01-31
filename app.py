import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np

# Cấu hình trang
st.set_page_config(page_title="Macro Dashboard 2026", layout="wide")

st.title("📊 Hệ thống Theo dõi Vĩ mô & Quy luật 'Vật cực tất phản'")
st.markdown(f"**Ngày hiện tại:** {pd.Timestamp.now().strftime('%d/%m/%Y')}")

# 1. Hàm lấy dữ liệu từ Yahoo Finance
@st.cache_data(ttl=3600)
def load_data():
    # Lấy dữ liệu Vàng (GC=F) và S&P 500 (^GSPC) làm đại diện thị trường rủi ro
    # Bạn có thể đổi ^GSPC thành E1VFVN30.HM để xem VN30
    tickers = ["GC=F", "^GSPC"]
    data = yf.download(tickers, start="2023-01-01")['Close']
    return data

# 2. Xử lý dữ liệu
try:
    raw_data = load_data()
    
    # Kiểm tra nếu dữ liệu bị trống
    if raw_data.empty:
        st.error("Không thể lấy dữ liệu từ Yahoo Finance. Vui lòng kiểm tra lại kết nối.")
    else:
        # Xử lý dữ liệu để lấy đúng cột
        gold = raw_data["GC=F"].dropna()
        stock = raw_data["^GSPC"].dropna()

        # Lấy giá trị cuối cùng an toàn
        current_gold = gold.iloc[-1]
        current_stock = stock.iloc[-1]

        # 3. Sidebar điều chỉnh giả định 2026
        st.sidebar.header("Dự báo Kinh tế 2026")
        cpi = st.sidebar.slider("Lạm phát dự kiến (%)", 1.0, 15.0, 4.5)
        interest_rate = st.sidebar.slider("Lãi suất huy động (%)", 1.0, 15.0, 7.5)
        real_rate = interest_rate - cpi

        # 4. Hiển thị Widget chỉ số
        col1, col2, col3 = st.columns(3)
        col1.metric("Giá Vàng (USD/oz)", f"{current_gold:,.2f}")
        col2.metric("Lãi Suất Thực (%)", f"{real_rate:.1f}%", delta=f"{real_rate - 2.0:.1f}% từ mốc cơ sở")
        col3.metric("Chỉ số Chứng khoán", f"{current_stock:,.2f}")

        # 5. Vẽ biểu đồ tương quan
        st.subheader("Biến động Tài sản thực tế (Dữ liệu Live)")
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # Trục bên trái cho Vàng
        ax1.plot(gold.index, gold, color='gold', linewidth=2, label="Giá Vàng")
        ax1.set_ylabel("Vàng (USD/oz)", color='gold', fontsize=12, fontweight='bold')
        ax1.tick_params(axis='y', labelcolor='gold')
        ax1.grid(True, alpha=0.2)

        # Trục bên phải cho Chứng khoán
        ax2 = ax1.twinx()
        ax2.plot(stock.index, stock, color='seagreen', linewidth=2, label="Chứng khoán", alpha=0.7)
        ax2.set_ylabel("Chứng khoán (Index)", color='seagreen', fontsize=12, fontweight='bold')
        ax2.tick_params(axis='y', labelcolor='seagreen')

        plt.title("Tương quan Vàng & Chứng khoán trong chu kỳ 2024 - 2026")
        st.pyplot(fig)

        # 6. Đánh giá Quy luật Vật cực tất phản
        st.divider()
        st.subheader("💡 Đánh giá từ hệ thống")
