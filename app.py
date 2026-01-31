import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np

# 1. Cấu hình giao diện
st.set_page_config(page_title="Macro Dashboard 2026", layout="wide")
st.title("📊 Hệ thống Theo dõi Vĩ mô & Quy luật 'Vật cực tất phản'")
st.markdown(f"**Cập nhật dữ liệu thực tế ngày:** {pd.Timestamp.now().strftime('%d/%m/%Y')}")

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

        # 5. Sidebar cấu hình
        st.sidebar.header("🕹️ Điều khiển Vĩ mô 2026")
        cpi = st.sidebar.slider("Lạm phát dự kiến (%)", 1.0, 20.0, 4.5)
        ir = st.sidebar.slider("Lãi suất huy động (%)", 1.0, 20.0, 7.5)
        premium_sjc = st.sidebar.number_input("Chênh lệch SJC (Tr/lượng)", value=4.0)
        real_ir = ir - cpi

        st.sidebar.divider()
        st.sidebar.header("🏆 Kịch bản Vàng 2026")
        
        # SỬA ĐỔI PHẦN KỊCH BẢN THEO YÊU CẦU
        scenario = st.sidebar.selectbox("Chọn trạng thái thị trường:", 
            ["Bình thường", "Vật cực (Sốt nóng)", "Tất phản (Điều chỉnh)", "Đi ngang (Sideway)", "Tự nhập con số"])
        
        reason = ""
        if scenario == "Bình thường":
            pct_change = 7.5  # Trung bình +5% đến +10%
            reason = "Kinh tế ổn định, lạm phát thấp."
        elif scenario == "Vật cực (Sốt nóng)":
            pct_change = 30.0 # Trung bình +20% đến +40%
            reason = "Chiến tranh, khủng hoảng kinh tế, hoặc lạm phát phi mã."
        elif scenario == "Tất phản (Điều chỉnh)":
            pct_change = -15.0 # Trung bình -10% đến -20%
            reason = "Ngân hàng Trung ương tăng lãi suất thực cao, vàng bị bán tháo."
        elif scenario == "Đi ngang (Sideway)":
            pct_change = 0.0   # Trung bình -5% đến +5%
            reason = "Thị trường chờ đợi tín hiệu mới, không có biến động lớn."
        else:
            pct_change = st.sidebar.number_input("Nhập % bạn dự đoán:", value=10.0)
            reason = "Kịch bản tùy chỉnh dựa trên phân tích cá nhân."

        st.sidebar.caption(f"**Giải thích:** {reason}")
        # 6. Hiển thị Dashboard chỉ số chính
        gold_sjc_converted = ((curr_gold_usd * 1.205) / 31.1035 * curr_exchange_rate) / 1000000 + premium_sjc
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Vàng SJC Dự báo (Tr/lượng)", f"{gold_sjc_converted:.2f}")
        m2.metric("Lãi Suất Thực (Real IR)", f"{real_ir:.1f}%", delta=f"{real_ir-2.0:.1f}%")
        m3.metric("S&P 500", f"{curr_stock:,.1f}")

        # 7. Vẽ biểu đồ tương quan Live & Dự báo
        st.subheader("📈 Diễn biến tương quan & Dự báo hướng đi")
        future_dates = pd.date_range(start=gold_series.index[-1], periods=30)
        gold_projection = [curr_gold_usd * (1 - (real_ir/1000))**i for i in range(30)]
        
        fig, ax1 = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor('#0E1117')
        ax1.set_facecolor('#0E1117')

        # Trục Vàng
        lns1 = ax1.plot(gold_series.index, gold_series, color='#D4AF37', lw=2, label="Vàng thực tế")
        lns2 = ax1.plot(future_dates, gold_projection, color='#D4AF37', ls='--', alpha=0.7, label="Dự báo (Real IR)")
        ax1.set_ylabel("Giá Vàng (USD)", color='#D4AF37', fontweight='bold')
        ax1.grid(True, alpha=0.1)

        # Trục S&P 500
        ax2 = ax1.twinx()
        lns3 = ax2.plot(stock_series.index, stock_series, color='#2E8B57', lw=1, label="S&P 500", alpha=0.5)
        ax2.set_ylabel("S&P 500", color='#2E8B57', fontweight='bold')

        # --- XỬ LÝ VÙNG HIGHLIGHT VÀ CHÚ THÍCH TRONG BOX ---
        import matplotlib.patches as mpatches # Cần thêm thư viện này

        if real_ir > 0:
            color_zone = 'cyan'
            label_zone = "Vùng hút tiền về Bank"
        else:
            color_zone = 'orange'
            label_zone = "Vùng trú ẩn (Vàng ưu thế)"

        # Vẽ vùng highlight
        ax1.axvspan(gold_series.index[-1], future_dates[-1], color=color_zone, alpha=0.15)
        
        # Tạo một Patch để đưa vào Legend
        zone_patch = mpatches.Patch(color=color_zone, alpha=0.3, label=label_zone)
        # --------------------------------------------------

        # Gộp tất cả các đường và vùng màu vào chú thích
        lns = lns1 + lns2 + lns3 + [zone_patch]
        labs = [l.get_label() for l in lns]
        ax1.legend(lns, labs, loc='upper left', facecolor='#1E1E1E', edgecolor='white', fontsize='small')

        plt.title(f"Mô phỏng Lãi suất thực: {real_ir:.1f}%", color='white', pad=20)
        st.pyplot(fig)

        # 8. Tham chiếu lịch sử & Phân tích
        st.divider()
        col_hist1, col_hist2 = st.columns([2, 1])

        with col_hist1:
            st.subheader("📚 Lịch sử Lạm phát Việt Nam")
            fig_h, ax_h = plt.subplots(figsize=(10, 4))
            fig_h.patch.set_facecolor('#0E1117')
            ax_h.set_facecolor('#0E1117')
            ax_h.bar(df_hist["Năm"].astype(str), df_hist["Lạm phát (%)"], color='tomato', alpha=0.7)
            ax_h.axhline(cpi, color='cyan', ls='--', label=f"Dự báo 2026 ({cpi}%)")
            ax_h.set_ylabel("Lạm phát (%)", color='white')
            ax_h.tick_params(colors='white')
            ax_h.legend(facecolor='#1E1E1E', edgecolor='white')
            st.pyplot(fig_h)

        with col_hist2:
            st.write("**Bảng dữ liệu chi tiết**")
            st.dataframe(df_hist, hide_index=True)

        # 9. Nhận định tự động
        st.subheader("💡 Nhận định từ Hệ thống")
        if real_ir < 0:
            st.warning("⚠️ **VẬT CỰC:** Lãi suất thực âm. Dòng tiền có xu hướng tháo chạy khỏi ngân hàng để tìm đến Vàng/Bất động sản.")
        elif real_ir > 4:
            st.success("🏦 **TẤT PHẢN:** Lãi suất thực đang rất hấp dẫn. Gửi tiết kiệm là kênh trú ẩn an toàn và hiệu quả nhất lúc này.")
        else:
            st.info("⚖️ **TRUNG TÍNH:** Thị trường đang cân bằng. Hãy quan sát thêm các tín hiệu từ tỷ giá.")

        # 10. Máy tính lợi nhuận đầu tư
        st.divider()
        st.subheader("🧮 Máy tính Lợi nhuận Đầu tư")
        von = st.number_input("Nhập số vốn đầu tư (VNĐ):", value=1000000000, step=10000000)
        
        c_gold, c_bank = st.columns(2)
        with c_gold:
            loi_nhuan_vang = von * (pct_change / 100)
            st.info(f"Kịch bản Vàng ({scenario} {pct_change}%):\n\n**{loi_nhuan_vang:,.0f} VNĐ**")
        with c_bank:
            loi_nhuan_bank = von * (ir / 100)
            st.success(f"Gửi tiết kiệm (Lãi suất {ir}%):\n\n**{loi_nhuan_bank:,.0f} VNĐ**")

except Exception as error:
    st.error(f"Đang chờ dữ liệu từ thị trường... (Lỗi: {error})")
