import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np

# 0. Khởi tạo Trạng thái Giao diện (Session State)
if 'theme' not in st.session_state:
    st.session_state.theme = 'Light'

# Tạo nút chuyển đổi ở Sidebar
st.sidebar.subheader("🌓 Tùy chỉnh giao diện")
if st.sidebar.button("Chuyển đổi Light/Dark"):
    st.session_state.theme = 'Dark' if st.session_state.theme == 'Light' else 'Light'

# Thiết lập màu sắc dựa trên lựa chọn
if st.session_state.theme == 'Dark':
    bg_color = '#0E1117'
    text_color = 'white'
    plt.style.use('dark_background')
else:
    bg_color = 'white'
    text_color = 'black'
    plt.style.use('default')
    
# 1. Cấu hình trang
st.set_page_config(page_title="Macro Dashboard 2026", layout="wide")
st.title(f"📊 Macro-Bot ({st.session_state.theme} Mode)")
st.markdown(f"**Dữ liệu thực tế ngày:** {pd.Timestamp.now().strftime('%d/%m/%Y')}")

# 2. Dữ liệu lịch sử lạm phát 
vn_inflation_hist = {
    "Năm": [2008, 2011, 2012, 2015, 2020, 2022, 2023, 2024, 2025],
    "Lạm phát (%)": [19.8, 18.1, 9.2, 0.6, 3.2, 3.1, 3.2, 3.5, 4.0],
    "Sự kiện": ["Khủng hoảng TG", "Vật cực - Lạm phát đỉnh", "Tất phản - Thắt chặt", "Thấp kỷ lục", "Đại dịch", "Hồi phục", "Ổn định", "Tăng nhẹ", "Tiền 2026"]
}
df_hist = pd.DataFrame(vn_inflation_hist)

# 3. Hàm lấy dữ liệu (Sử dụng Cache để tăng tốc)
@st.cache_data(ttl=3600)
def load_data():
    # Lấy Vàng thế giới và S&P 500 làm tham chiếu
    tickers = ["GC=F", "^GSPC"]
    data = yf.download(tickers, start="2023-01-01")['Close']
    return data

# 4. Luồng xử lý chính
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

        # 5. Thanh điều hướng cấu hình giả định (Sidebar)
        st.sidebar.header("Dự báo Kinh tế 2026")
        cpi = st.sidebar.slider("Lạm phát dự kiến (%)", 1.0, 15.0, 4.5)
        ir = st.sidebar.slider("Lãi suất huy động (%)", 1.0, 15.0, 7.5)
        real_ir = ir - cpi

        # 6. Hiển thị thông số nhanh
        c1, c2, c3 = st.columns(3)
        c1.metric("Vàng (USD/oz)", f"{curr_gold:,.1f}")
        c2.metric("Lãi Suất Thực", f"{real_ir:.1f}%", delta=f"{real_ir-2.0:.1f}%")
        c3.metric("S&P 500", f"{curr_stock:,.1f}")

        # 7. Vẽ biểu đồ tương quan Live & Dự báo
        st.subheader("Diễn biến tương quan & Dự báo biến động")
        
        # Tạo dữ liệu dự báo ngắn hạn (30 ngày tới) dựa trên Lãi suất thực
        future_dates = pd.date_range(start=gold_series.index[-1], periods=30)
        # Mô phỏng: Nếu lãi suất thực tăng -> Vàng có xu hướng giảm nhẹ và ngược lại
        gold_projection = [curr_gold * (1 - (real_ir/1000))**i for i in range(30)]
        
        fig, ax1 = plt.subplots(figsize=(10, 5))

        # Đường Vàng thực tế & Dự báo
        ax1.plot(gold_series.index, gold_series, color='#D4AF37', lw=2, label="Vàng thực tế")
        ax1.plot(future_dates, gold_projection, color='#D4AF37', ls='--', alpha=0.7, label="Dự báo hướng đi (Theo Real IR)")
        
        ax1.set_ylabel("Giá Vàng (USD)", color='#D4AF37', fontweight='bold')
        ax1.tick_params(axis='y', labelcolor='#D4AF37')
        ax1.grid(True, alpha=0.2)

        # Đường Chứng khoán
        ax2 = ax1.twinx()
        ax2.plot(stock_series.index, stock_series, color='#2E8B57', lw=2, label="S&P 500", alpha=0.6)
        ax2.set_ylabel("S&P 500", color='#2E8B57', fontweight='bold')
        ax2.tick_params(axis='y', labelcolor='#2E8B57')
        
        # Chỉ báo vùng nhạy cảm lãi suất
        if real_ir > 0:
            ax1.axvspan(gold_series.index[-1], future_dates[-1], color='blue', alpha=0.1, label="Vùng hút tiền (Tiết kiệm ưu thế)")
        else:
            ax1.axvspan(gold_series.index[-1], future_dates[-1], color='orange', alpha=0.1, label="Vùng trú ẩn (Vàng ưu thế)")

        plt.title(f"Tương quan thực tế & Tác động của Lãi suất thực ({real_ir:.1f}%)")
        ax1.legend(loc='upper left', fontsize='small')
        st.pyplot(fig)

        # 8. Tham chiếu Lịch sử Lạm phát Việt Nam
        st.divider()
        st.subheader("📚 Tham chiếu Lịch sử Lạm phát Việt Nam")
        st.write("Dựa vào dữ liệu quá khứ để xác định điểm 'Vật cực' của chu kỳ hiện tại.")
        
        col_hist1, col_hist2 = st.columns([2, 1])
        with col_hist1:
            fig_hist, ax_hist = plt.subplots(figsize=(10, 4))
            ax_hist.bar(df_hist["Năm"].astype(str), df_hist["Lạm phát (%)"], color='tomato', alpha=0.7)
            # Đường ngang thể hiện mức dự báo hiện tại của người dùng
            ax_hist.axhline(cpi, color='blue', ls='--', label=f"Dự báo 2026 của bạn ({cpi}%)")
            ax_hist.set_ylabel("Lạm phát (%)")
            ax_hist.legend()
            st.pyplot(fig_hist)
        with col_hist2:
            st.dataframe(df_hist, hide_index=True)

        # 9. Phân tích logic "Vật cực tất phản"
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

        # 10. Tính toán lợi nhuận thực tế
        st.divider()
        st.subheader("🧮 Máy tính So sánh Đầu tư")
        
        # Nhập vốn đầu tư
        von_dau_tu = st.number_input("Nhập số vốn đầu tư của bạn (VNĐ):", min_value=0, value=1000000000, step=10000000)
        
        col_calc1, col_calc2 = st.columns(2)
        with col_calc1:
            st.write("**Kênh Vàng SJC:**")
            tang_truong_vang = st.number_input("Dự báo Vàng tăng/giảm (%)", value=10.0, key="gold_proj_input")
            loi_nhuan_vang = von_dau_tu * (tang_truong_vang / 100)
            st.info(f"Lợi nhuận dự kiến từ vàng: **{loi_nhuan_vang:,.0f} VNĐ**")

        with col_calc2:
            st.write("**Kênh Tiết kiệm:**")
            # Lợi nhuận ngân hàng tính trên lãi suất danh nghĩa đã chọn ở sidebar
            loi_nhuan_bank = von_dau_tu * (ir / 100)
            st.success(f"Lợi nhuận chắc chắn từ Tiết kiệm: **{loi_nhuan_bank:,.0f} VNĐ**")

        # Lời khuyên dựa trên kết quả tính toán
        if loi_nhuan_bank > loi_nhuan_vang:
            st.error(f"👉 **TẤT PHẢN:** Gửi tiết kiệm hiệu quả hơn Vàng {loi_nhuan_bank - loi_nhuan_vang:,.0f} VNĐ mà không rủi ro.")
        else:
            st.warning(f"👉 **VẬT CỰC:** Vàng hấp dẫn hơn, nhưng hãy thoát hàng khi Lãi suất thực (Real IR) tiến gần 4-5%.")

except Exception as error:
    st.error(f"Lỗi vận hành: {error}")
