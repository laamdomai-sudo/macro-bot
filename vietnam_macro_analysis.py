import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Cấu hình trang
st.set_page_config(page_title="VN Money Supply & Credit", layout="wide")
st.title("🇻🇳 Vĩ Mô Việt Nam: Cung Tiền (M2) & Tăng Trưởng Tín Dụng")

# Dữ liệu vĩ mô Việt Nam (Dựa trên số liệu World Bank & IMF)
# Vì API FRED không có M2 VN dài hạn, ta sử dụng dữ liệu mô phỏng từ các báo cáo thống kê chính thức
@st.cache_data
def get_vn_macro_data():
    # Trong thực tế, bạn có thể thay thế bằng file CSV tải từ World Bank
    years = list(range(1995, 2026))
    # Dữ liệu mô phỏng sát với thực tế tăng trưởng tín dụng VN
    credit_growth = [
        25, 30, 22, 18, 15, 38, 40, 35, 30, 25, 28, 32, 53, 39, 37, # 1995-2009
        29, 14, 12, 12, 14, 17, 18, 18, 14, 13, 12, 13, 14, 12, 11, 12 # 2010-2025
    ]
    # M2 tăng trưởng tương ứng
    m2_growth = [val * 0.9 for val in credit_growth] 
    
    df = pd.DataFrame({
        'Year': pd.to_datetime([f"{y}-01-01" for y in years]),
        'Tăng trưởng Tín dụng (%)': credit_growth,
        'Tăng trưởng Cung tiền M2 (%)': m2_growth
    }).set_index('Year')
    return df

try:
    df_vn = get_vn_macro_data()

    # --- SECTION 1: METRICS ---
    c1, c2 = st.columns(2)
    latest_credit = df_vn['Tăng trưởng Tín dụng (%)'].iloc[-1]
    latest_m2 = df_vn['Tăng trưởng Cung tiền M2 (%)'].iloc[-1]
    
    c1.metric("Tăng trưởng Tín dụng (2025 Est)", f"{latest_credit}%", f"{latest_credit - df_vn['Tăng trưởng Tín dụng (%)'].iloc[-2]:.1f}%")
    c2.metric("Tăng trưởng Cung tiền M2", f"{latest_m2}%", f"{latest_m2 - df_vn['Tăng trưởng Cung tiền M2 (%)'].iloc[-2]:.1f}%")

    # --- SECTION 2: BIỂU ĐỒ ---
    st.subheader("📈 Lịch sử Bơm Tiền & Tín Dụng (30 Năm)")
    
    fig = go.Figure()
    
    # Vẽ Tín dụng
    fig.add_trace(go.Scatter(
        x=df_vn.index, y=df_vn['Tăng trưởng Tín dụng (%)'],
        name="Tăng trưởng Tín dụng",
        line=dict(color='#FF4B4B', width=3),
        fill='tozeroy'
    ))
    
    # Vẽ M2
    fig.add_trace(go.Scatter(
        x=df_vn.index, y=df_vn['Tăng trưởng Cung tiền M2 (%)'],
        name="Tăng trưởng M2",
        line=dict(color='#00FFCC', width=2, dash='dash')
    ))

    # Đánh dấu các mốc quan trọng
    milestones = [
        {"year": "2007-01-01", "label": "Gia nhập WTO (Bùng nổ tín dụng)"},
        {"year": "2011-01-01", "label": "Thắt chặt tiền tệ (Kiềm chế lạm phát)"},
        {"year": "2020-01-01", "label": "Hỗ trợ thanh khoản COVID-19"}
    ]
    
    for m in milestones:
        fig.add_vline(x=m["year"], line_width=1, line_dash="dot", line_color="white")
        fig.add_annotation(x=m["year"], y=50, text=m["label"], showarrow=False, font=dict(size=10))

    fig.update_layout(
        height=600, template="plotly_dark",
        yaxis=dict(title="Tỷ lệ tăng trưởng (%)", suffix="%"),
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # --- SECTION 3: NHẬN ĐỊNH THÔNG MINH ---
    st.divider()
    st.subheader("🤖 Nhận Định Hệ Thống")
    
    if latest_credit > 15:
        st.warning("⚠️ Tín dụng đang tăng trưởng nóng. Cần quan sát rủi ro nợ xấu và lạm phát.")
    elif latest_credit < 10:
        st.info("🔄 Tín dụng tăng trưởng chậm. Kinh tế có dấu hiệu hấp thụ vốn kém, Ngân hàng Trung ương có thể cân nhắc hạ lãi suất.")
    else:
        st.success("✅ Tín dụng ở mức mục tiêu (12-14%). Đây là trạng thái ổn định lý tưởng cho tăng trưởng bền vững.")

except Exception as e:
    st.error(f"Lỗi tải dữ liệu VN: {e}")
