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
        c2.metric("Lãi Suất Thực", f"{real_ir:.1f}%", delta=f"{real_ir-2.0:.1f}%")
        c3.metric("S&P 500", f"{curr_stock:,.1f}")

        # 6. Vẽ biểu đồ tương quan Live & Dự báo
        st.subheader("Diễn biến tương quan & Dự báo biến động")
        
        # Tạo dữ liệu dự báo ngắn hạn (30 ngày tới) dựa trên Lãi suất thực
        future_dates = pd.date_range(start=gold_series.index[-1], periods=30)
        # Nếu lãi suất thực tăng -> Vàng có xu hướng giảm nhẹ trong dự báo và ngược lại
        gold_projection = [curr_gold * (1 - (real_ir/500))**i for i in range(30)]
        
        fig, ax1 = plt.subplots(figsize=(10, 5))

        # Đường Vàng thực tế & Dự báo
        ax1.plot(gold_series.index, gold_series, color='#D4AF37', lw=2, label="Vàng thực tế")
        ax1.plot(future_dates, gold_projection, color='#D4AF37', ls='--', alpha=0.7, label="Dự báo hướng đi")
        
        ax1.set_ylabel("Giá Vàng (USD)", color='#D4AF37', fontweight='bold')
        ax1.tick_params(axis='y', labelcolor='#D4AF37')
        ax1.grid(True, alpha=0.2)

        # Đường Chứng khoán
        ax2 = ax1.twinx()
        ax2.plot(stock_series.index, stock_series, color='#2E8B57', lw=2, label="S&P 500", alpha=0.6)
        
        # Chỉ báo vùng nhạy cảm lãi suất
        if real_ir > 0:
            ax1.axvspan(gold_series.index[-1], future_dates[-1], color='blue', alpha=0.1, label="Vùng hút tiền")
        else:
            ax1.axvspan(gold_series.index[-1], future_dates[-1], color='orange', alpha=0.1, label="Vùng trú ẩn")

        plt.title(f"Tương quan thực tế & Tác động của Lãi suất thực ({real_ir:.1f}%)")
        ax1.legend(loc='upper left', fontsize='small')
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

        # 8. Tính toán lợi nhuận thực tế
        st.divider()
        st.subheader("🧮 Máy tính So sánh Đầu tư")
        
        # Cho phép người dùng nhập vốn
        von_dau_tu = st.number_input("Nhập số vốn đầu tư của bạn (VNĐ):", min_value=0, value=1000000000, step=10000000)
        
        col_calc1, col_calc2 = st.columns(2)
        with col_calc1:
            st.write("**Kênh Vàng SJC:**")
            tang_truong_vang = st.number_input("Dự báo Vàng tăng/giảm (%)", value=10.0)
            loi_nhuan_vang = von_dau_tu * (tang_truong_vang / 100)
            st.info(f"Lợi nhuận dự kiến từ vàng: **{loi_nhuan_vang:,.0f} VNĐ**")

        with col_calc2:
            st.write("**Kênh Tiết kiệm:**")
            loi_nhuan_bank = von_dau_tu * (ir / 100)
            st.success(f"Lợi nhuận chắc chắn từ Tiết kiệm: **{loi_nhuan_bank:,.0f} VNĐ**")

        # Lời khuyên
        if loi_nhuan_bank > loi_nhuan_vang:
            st.error(f"👉 **TẤT PHẢN:** Gửi tiết kiệm đang hiệu quả hơn Vàng {loi_nhuan_bank - loi_nhuan_vang:,.0f} VNĐ mà không rủi ro.")
        else:
            st.warning(f"👉 **VẬT CỰC:** Vàng vẫn hấp dẫn hơn, nhưng hãy thoát hàng ngay khi Lãi suất thực tiến gần mức 4-5%.")

except Exception as error:
    st.error(f"Lỗi vận hành: {error}")
