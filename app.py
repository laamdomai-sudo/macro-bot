import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np

# 1. Cấu hình giao diện
st.set_page_config(page_title="Macro Dashboard 2026", layout="wide")

st.title("📊 Hệ thống Theo dõi Vĩ mô & Quy luật 'Vật cực tất phản'")
st.markdown(f"**Cập nhật dữ liệu ngày:** {pd.Timestamp.now().strftime('%d/%m/%Y')}")

# 2. Hàm lấy dữ liệu (Sử dụng Cache để tăng tốc)
@st.cache_data(ttl=3600)
def load_data():
    # Lấy Vàng thế giới và S&P 500 làm tham chiếu
    tickers = ["GC=F", "^GSPC"]
    data = yf.download(tickers, start="2023-01-01")['Close']
    return data

# 3. Luồng xử lý chính
try:
    df_raw = load_data()
    
    if df_raw.empty:
        st.error("Dữ liệu trống. Vui lòng kiểm tra kết nối Yahoo Finance.")
    else:
        # Tách dữ liệu an toàn
        gold_series = df_raw["GC=F"].dropna()
        stock_series = df_raw["^GSPC"].dropna()

        # Lấy giá trị hiện tại
        curr_gold = float(gold_series.iloc[-1])
        curr_stock = float(stock_series.iloc[-1])

        # 4. Thanh điều hướng cấu hình giả định
        st.sidebar.header("Dự báo Kinh tế 2026")
        cpi = st.sidebar.slider("Lạm phát dự kiến (%)", 1.0, 15.0, 4.5)
        ir = st.sidebar.slider("Lãi suất huy động (%)", 1.0, 15.0, 7.5)
        real_ir = ir - cpi

        # 5. Hiển thị thông số nhanh
        c1, c2, c3 = st.columns(3)
        c1.metric("Vàng (USD/oz)", f"{curr_gold:,.1f}")
        c2.metric("Lãi Suất Thực", f"{real_ir:.1f}%")
        c3.metric("S&P 500", f"{curr_stock:,.1f}")

        # 6. Vẽ biểu đồ
        st.subheader("Diễn biến tương quan Live")
        fig, ax1 = plt.subplots(figsize=(10, 5))

        # Đường Vàng
        ax1.plot(gold_series.index, gold_series, color='#D4AF37', lw=2, label="Vàng")
        ax1.set_ylabel("Giá Vàng (USD)", color='#D4AF37', fontweight='bold')
        ax1.tick_params(axis='y', labelcolor='#D4AF37')
        ax1.grid(True, alpha=0.2)

        # Đường Chứng khoán
        ax2 = ax1.twinx()
        ax2.plot(stock_series.index, stock_series, color='#2E8B57', lw=2, label="S&P 500", alpha=0.6)
        ax2.set_ylabel("Chứng khoán", color='#2E8B57', fontweight='bold')
        ax2.tick_params(axis='y', labelcolor='#2E8B57')

        plt.title("Biểu đồ Vàng & Chứng khoán (2023-2026)")
        st.pyplot(fig)

        # 7. Phân tích logic "Vật cực tất phản"
        st.divider()
        st.subheader("💡 Nhận định hệ thống")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if real_ir < 0:
                st.warning("⚠️ **VẬT CỰC:** Lãi suất thực âm. Vàng đang được hỗ trợ cực mạnh.")
            elif real_ir > 4:
                st.success("🏦 **TẤT PHẢN:** Lãi suất thực cao. Tiền đang có xu hướng rời vàng về Bank.")
            else:
                st.info("Thị trường đang ở vùng trung tính.")

        with col_b:
            if curr_gold > 2800 and real_ir > 3:
                st.error("‼️ **ĐIỂM GÃY:** Rủi ro bong bóng vàng cực lớn khi lãi suất thực bắt đầu dương cao.")
            else:
                st.write("Dòng tiền vẫn đang vận hành theo kỳ vọng lạm phát.")

except Exception as error:
    st.error(f"Lỗi vận hành: {error}")
