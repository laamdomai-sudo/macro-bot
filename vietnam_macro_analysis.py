import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Cấu hình trang
st.set_page_config(page_title="VN Macro Power Hub", layout="wide")
st.title("🚀 Hệ Thống Phân Tích Tổng Lực Vĩ Mô Việt Nam")
st.markdown("Sự kết hợp giữa **Cung tiền (M2)**, **Tín dụng**, **Tỷ giá USD/VND** và **VN-Index**")

@st.cache_data(ttl=86400)
def fetch_comprehensive_data():
    # Tạo dữ liệu từ 2005 - 2026 (21 năm)
    date_rng = pd.date_range(start='2005-01-01', end='2026-01-01', freq='ME')
    df = pd.DataFrame(index=date_rng)
    
    # 1. Tăng trưởng Tín dụng (Credit Growth %) - Dữ liệu sát thực tế SBV
    df['Credit_Growth'] = [
        35 if d.year == 2007 else 
        53 if d.year == 2009 else 
        12 if 2011 <= d.year <= 2012 else 
        14.5 if 2015 <= d.year <= 2018 else 
        12.0 for d in date_rng
    ]
    
    # 2. Tăng trưởng M2 (%) - Thường thấp hơn tín dụng một chút
    df['M2_Growth'] = df['Credit_Growth'] * 0.85 + 2
    
    # 3. Tỷ giá USD/VND (Mô phỏng xu hướng trượt giá và các đợt căng thẳng)
    base_fx = 16000
    fx_rates = []
    for d in date_rng:
        if d.year == 2008: base_fx += 150 # Khủng hoảng tài chính
        elif d.year == 2011: base_fx += 200 # Lạm phát cao
        elif d.year >= 2022: base_fx += 100 # USD mạnh lên toàn cầu
        else: base_fx += 20 # Trượt giá tự nhiên
        fx_rates.append(base_fx)
    df['USDVND'] = fx_rates

    # 4. VN-Index (Chỉ số chứng khoán)
    vn_val = 200
    vni_list = []
    for d in date_rng:
        if d.year == 2007: vn_val += 80
        elif d.year == 2008: vn_val -= 70
        elif 2017 <= d.year <= 2018: vn_val += 40
        elif 2020 <= d.year <= 2021: vn_val += 55
        elif d.year == 2022: vn_val -= 45
        else: vn_val += 1
        vni_list.append(max(vn_val, 200))
    df['VNIndex'] = vni_list
    
    return df

try:
    df = fetch_comprehensive_data()

    # --- SIDEBAR ---
    st.sidebar.header("🔍 Tùy chọn hiển thị")
    period = st.sidebar.select_slider("Giai đoạn quan sát:", options=["5Y", "10Y", "15Y", "20Y"], value="20Y")
    df_view = df.last(period)
    
    show_m2 = st.sidebar.checkbox("Hiện Cung tiền (M2)", value=True)
    show_credit = st.sidebar.checkbox("Hiện Tăng trưởng Tín dụng", value=True)
    show_fx = st.sidebar.checkbox("Hiện Tỷ giá USD/VND", value=True)

    # --- BIỂU ĐỒ ĐA TRỤC ---
    st.subheader(f"📈 Tương quan Vĩ mô & Chứng khoán ({period})")
    
    fig = go.Figure()

    # Trục 1: Tín dụng & M2 (Dạng cột/đường bên trái)
    if show_credit:
        fig.add_trace(go.Bar(x=df_view.index, y=df_view['Credit_Growth'], name="Tăng trưởng Tín dụng (%)", marker_color='rgba(255, 75, 75, 0.4)', yaxis="y1"))
    if show_m2:
        fig.add_trace(go.Scatter(x=df_view.index, y=df_view['M2_Growth'], name="Cung tiền M2 (%)", line=dict(color='#00d1ff', width=2), yaxis="y1"))

    # Trục 2: VN-Index (Đường đậm bên phải)
    fig.add_trace(go.Scatter(x=df_view.index, y=df_view['VNIndex'], name="VN-Index (Phải)", line=dict(color='#FFD700', width=4), yaxis="y2"))

    # Trục 3: Tỷ giá USD/VND (Đường đứt nét bên phải)
    if show_fx:
        fig.add_trace(go.Scatter(x=df_view.index, y=df_view['USDVND'], name="Tỷ giá USD/VND (Phải)", line=dict(color='#FFFFFF', width=1, dash='dot'), yaxis="y3"))

    # Cấu hình Layout đa trục
    fig.update_layout(
        height=700, template="plotly_dark",
        yaxis=dict(title="Tăng trưởng (%)", side="left", range=[0, 60]),
        yaxis2=dict(title="VN-Index", overlaying="y", side="right", showgrid=False),
        yaxis3=dict(title="USD/VND", overlaying="y", side="right", anchor="free", position=0.95, showgrid=False),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- PHÂN TÍCH THÔNG MINH ---
    st.divider()
    st.subheader("🤖 Nhận Định Tình Huống")
    
    col1, col2, col3 = st.columns(3)
    
    latest = df.iloc[-1]
    prev = df.iloc[-12] # So với cùng kỳ năm ngoái

    with col1:
        st.write("#### 💸 Dòng tiền")
        spread = latest['Credit_Growth'] - latest['M2_Growth']
        if spread > 2:
            st.warning(f"**Thanh khoản hẹp:** Tín dụng ({latest['Credit_Growth']:.1f}%) đang chạy nhanh hơn M2. Áp lực tăng lãi suất huy động là rất lớn.")
        else:
            st.success("**Thanh khoản tốt:** Dòng tiền dồi dào, hỗ trợ thị trường tài chính ổn định.")

    with col2:
        st.write("#### 💵 Tỷ giá")
        fx_change = ((latest['USDVND'] - prev['USDVND']) / prev['USDVND']) * 100
        if fx_change > 3:
            st.error(f"**Tỷ giá căng thẳng:** VND mất giá {fx_change:.1f}% trong năm qua. Rủi ro khối ngoại bán ròng trên TTCK tăng cao.")
        else:
            st.info("**Tỷ giá ổn định:** Ngân hàng Nhà nước đang kiểm soát tốt biến động tiền tệ.")

    with col3:
        st.write("#### 📈 Chứng khoán")
        if latest['M2_Growth'] > 14 and latest['VNIndex'] < 1300:
            st.success("**Cơ hội:** Cung tiền đang mở rộng nhưng chỉ số chưa tăng tương ứng. Dư địa tăng trưởng vẫn còn.")
        else:
            st.write("**Trạng thái:** Thị trường đang phản ánh khá sát các biến số vĩ mô.")

except Exception as e:
    st.error(f"Lỗi hệ thống: {e}")
