import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Thiết lập giao diện Streamlit
st.set_page_config(page_title="Economic Dashboard 2026", layout="wide")
st.title("📊 Mô phỏng Quy luật 'Vật cực tất phản' - Kinh tế 2026")
st.markdown("""
Ứng dụng này minh họa sự luân chuyển dòng tiền giữa **Vàng**, **Chứng khoán** và **Tiết kiệm** dựa trên biến động của **Lãi suất thực**.
""")

# Thanh điều hướng bên trái (Sidebar) để thay đổi thông số
st.sidebar.header("Cấu hình giả định 2026")
peak_inflation = st.sidebar.slider("Lạm phát đỉnh điểm (%)", 4.0, 15.0, 6.0)
max_interest_rate = st.sidebar.slider("Lãi suất ngân hàng tối đa (%)", 5.0, 15.0, 10.0)

# 1. Giả lập dữ liệu
months = ["Tháng " + str(i) for i in range(1, 13)]
cpi = np.array([4.0, 4.5, 5.2, peak_inflation, peak_inflation-0.5, peak_inflation-1.5, 4.0, 3.5, 3.2, 3.0, 2.8, 2.5])
nominal_rate = np.linspace(6.0, max_interest_rate, 6).tolist() + np.linspace(max_interest_rate, 7.0, 6).tolist()
real_rate = np.array(nominal_rate) - cpi

# Giả lập giá Vàng và VN-Index dựa trên logic kinh tế
gold_price = 2000 + (cpi * 150) - (real_rate * 50)
vni_index = 1300 - (nominal_rate * 20) + (np.cumsum(real_rate) * 5)

df = pd.DataFrame({
    "Tháng": months,
    "Giá Vàng": gold_price,
    "VN-Index": vni_index,
    "Lãi suất thực": real_rate
})

# 2. Hiển thị chỉ số tổng quan
col1, col2, col3 = st.columns(3)
col1.metric("Giá Vàng cao nhất", f"{int(max(gold_price))} USD")
col2.metric("Lãi suất thực cao nhất", f"{round(max(real_rate), 2)} %")
col3.metric("Đáy VN-Index", f"{int(min(vni_index))} pts")

# 3. Vẽ biểu đồ với Matplotlib
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

# Vàng
ax1.plot(months, gold_price, color='gold', marker='o', linewidth=3)
ax1.set_ylabel("Vàng (USD)")
ax1.set_title("1. Tài sản trú ẩn (Vàng)")
ax1.grid(alpha=0.3)

# Lãi suất thực
ax2.plot(months, real_rate, color='blue', linestyle='--', marker='s')
ax2.axhline(0, color='black', lw=1)
ax2.fill_between(months, 0, real_rate, where=(real_rate > 0), color='blue', alpha=0.1)
ax2.set_ylabel("Lãi suất thực (%)")
ax2.set_title("2. Cái van điều tiết (Lãi suất thực)")

# VN-Index
ax3.plot(months, vni_index, color='seagreen', marker='^', linewidth=3)
ax3.set_ylabel("VN-Index")
ax3.set_title("3. Tài sản tăng trưởng (Chứng khoán)")
ax3.grid(alpha=0.3)

st.pyplot(fig)

# 4. Bảng dữ liệu chi tiết
if st.checkbox("Hiển thị bảng dữ liệu chi tiết"):
    st.table(df)
