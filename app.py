import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np

# 1. Cấu hình giao diện
st.set_page_config(page_title="Macro Dashboard 2026", layout="wide")

st.title("📊 Hệ thống Theo dõi Vĩ mô & Quy luật 'Vật cực tất phản'")
st.markdown(f"**Cập nhật dữ liệu ngày:** {pd.Timestamp.now().strftime('%d/%m/%Y')}")

# 2. Dữ liệu lịch sử lạm phát 
vn_inflation_hist = {
    "Năm": [2008, 2011, 2012, 2015, 2020, 2022, 2023, 2024, 2025],
    "Lạm phát (%)": [19.8, 18.1, 9.2, 0.6, 3.2, 3.1, 3.2, 3.5, 4.0],
    "Sự kiện": ["Khủng hoảng TG", "Vật cực - Lạm phát đỉnh", "Tất phản - Thắt chặt", "Thấp kỷ lục", "Đại dịch", "Hồi phục", "Ổn định", "Tăng nhẹ", "Tiền 2026"]
}
df_hist = pd.DataFrame(vn_inflation_hist)

# 3. Hàm lấy dữ liệu
@st.cache_data(ttl=3600)
def load_data():
    # Thêm VND=X để lấy tỷ giá USD/VND
    tickers = ["GC=F", "^GSPC", "VND=X"]
    data = yf.download(tickers, start="2023-01-01")['Close']
    return data

# 4. Luồng xử lý chính
try:
    df_raw = load_data()
    if not df_raw.empty:
        # Tách dữ liệu
        gold_series = df_raw["GC=F"].dropna()
        stock_series = df_raw["^GSPC"].dropna()
        usdvnd_series = df_raw["VND=X"].dropna()
        
        curr_gold_usd = float(gold_series.iloc[-1])
        curr_stock = float(stock_series.iloc[-1])
        curr_exchange_rate = float(usdvnd_series.iloc[-1])

        # 5. Sidebar cấu hình (Chỉ khai báo 1 lần duy nhất)
        st.sidebar.header("🕹️ Điều khiển Vĩ mô 2026")
        cpi = st.sidebar.slider("Lạm phát dự kiến (%)", 1.0, 20.0, 4.5)
        ir = st.sidebar.slider("Lãi suất huy động (%)", 1.0, 20.0, 7.5)
        premium_sjc = st.sidebar.number_input("Chênh lệch SJC (Tr/lượng)", value=4.0)
        real_ir = ir - cpi

        st.sidebar.divider()
        st.sidebar.header("🏆 Kịch bản Vàng 2026")
        scenario = st.sidebar.selectbox("Chọn kịch bản thị trường:", 
            ["Tăng trưởng ổn định", "Sốt nóng (Vật cực)", "Sụp đổ (Tất phản)", "Tự nhập con số"])
        
        if scenario == "Tăng trưởng ổn định":
            pct_change = 8.0
        elif scenario == "Sốt nóng (Vật cực)":
            pct_change = 35.0
        elif scenario == "Sụp đổ (Tất phản)":
            pct_change = -15.0
        else:
            pct_change = st.sidebar.number_input("Nhập % bạn dự đoán:", value=10.0)

        # 6. Hiển thị Dashboard chỉ số chính
        gold_sjc_converted = ((curr_gold_usd * 1.205) / 31.1035 * curr_exchange_rate) / 1000000 + premium_sjc
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Vàng SJC Dự kiến (Tr/lượng)", f"{gold_sjc_converted:.2f}")
        m2.metric("Lãi Suất Thực", f"{real_ir:.1f}%", delta=f"{real_ir-2.0:.1f}%")
        m3.metric("S&P 500", f"{curr_stock:,.1f}")

        # 7. Vẽ biểu đồ tương quan Live & Dự báo
        st.subheader("Diễn biến tương quan & Dự báo hướng đi")
        future_dates = pd.date_range(start=gold_series.index[-1], periods=30)
        # Dự báo dựa trên Real IR
        gold_projection = [curr_gold_usd * (1 - (real_ir/1000))**i for i in range(30)]
        
        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax1.plot(gold_series.index, gold_series, color='#D4AF37', lw=2, label="Vàng thực tế")
        ax1.plot(future_dates, gold_projection, color='#D4AF37', ls='--', alpha=0.7, label="Dự báo (Real IR)")
        ax1.set_ylabel("Giá Vàng (USD)", color='#D4AF37', fontweight='bold')
        ax1.grid(True, alpha=0.2)

        ax2 = ax1.twinx()
        ax2.plot(stock_series.index, stock_series, color='#2E8B57', lw=2, label="S&P 500", alpha=0.4)
        ax2.set_ylabel("S&P 500", color='#2E8B57', fontweight='bold')
        
        if real_ir > 0:
            ax1.axvspan(gold_series.index[-1], future_dates[-1], color='blue', alpha=0.1)
        else:
            ax1.axvspan(gold_series.index[-1], future_dates[-1], color='orange', alpha=0.1)

        plt.title(f"Tác động của Lãi suất thực đến Giá Vàng")
        ax1.legend(loc='upper left')
        st.pyplot(fig)

        # 8. Tham chiếu lịch sử & Phân tích
        st.divider()
        col_hist1, col_hist2 = st.columns([2, 1])
        with col_hist1
