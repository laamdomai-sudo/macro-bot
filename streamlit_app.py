import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# 1. Cấu hình
st.set_page_config(page_title="Macro AI Predictor", layout="wide")
st.title("🧠 Hệ Thống Dự Báo & Phân Tích Định Lượng Vàng - DXY")

@st.cache_data(ttl=3600)
def get_advanced_data():
    raw = yf.download(['GC=F', 'DX-Y.NYB'], period="max", auto_adjust=True)
    df = pd.DataFrame(index=raw.index)
    try:
        df['Gold'] = raw['Close']['GC=F']
        df['DXY'] = raw['Close']['DX-Y.NYB']
    except:
        df['Gold'] = raw.xs('GC=F', axis=1, level=1)['Close']
        df['DXY'] = raw.xs('DX-Y.NYB', axis=1, level=1)['Close']
    
    # Tính toán chỉ báo kỹ thuật
    df['MA200'] = df['Gold'].rolling(window=200).mean()
    
    # Tính RSI (14 ngày)
    delta = df['Gold'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Tính độ lệch khỏi MA200 (%)
    df['Dist_MA200'] = ((df['Gold'] - df['MA200']) / df['MA200']) * 100
    
    return df.ffill().dropna()

try:
    df = get_advanced_data()
    curr = df.iloc[-1]
    prev = df.iloc[-2]

    # --- 🤖 TRẠM DỰ BÁO TỰ ĐỘNG ---
    st.subheader("🔮 Hệ Thống Dự Báo & Đánh Giá Vị Thế")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("#### 🌡️ Sức nóng thị trường (RSI)")
        rsi_val = curr['RSI']
        if rsi_val > 70:
            st.error(f"**QUÁ MUA ({rsi_val:.1f})**: Vàng đang rất nóng. Rủi ro điều chỉnh giảm trong ngắn hạn là cực cao.")
        elif rsi_val < 30:
            st.success(f"**QUÁ BÁN ({rsi_val:.1f})**: Lực bán đã cạn kiệt. Cơ hội hồi phục kỹ thuật đang đến gần.")
        else:
            st.info(f"**TRUNG TÍNH ({rsi_val:.1f})**: Giá đang vận động ổn định, chưa có dấu hiệu cực đoan.")

    with c2:
        st.markdown("#### 📏 Khoảng cách MA200")
        dist = curr['Dist_MA200']
        if dist > 15:
            st.warning(f"**CẢNH BÁO BONG BÓNG**: Giá cao hơn MA200 {dist:.1f}%. Lịch sử cho thấy giá có xu hướng bị hút ngược về MA200.")
        elif dist < -10:
            st.success(f"**VÙNG GIÁ RẺ**: Giá thấp hơn MA200 {abs(dist):.1f}%. Đây thường là vùng gom hàng dài hạn.")
        else:
            st.info(f"**BÁM SÁT XU HƯỚNG**: Giá đang ở mức hợp lý so với trung bình 200 ngày.")

    with c3:
        st.markdown("#### 🎯 Dự báo dựa trên DXY")
        dxy_trend = df['DXY'].iloc[-1] - df['DXY'].iloc[-10] # Xu hướng 10 ngày
        if dxy_trend > 0:
            st.error("📉 **DỰ BÁO GIẢM**: DXY đang trong đà tăng ngắn hạn. Áp lực lên Vàng sẽ còn tiếp diễn.")
        else:
            st.success("📈 **DỰ BÁO TĂNG**: DXY đang suy yếu. Vàng có dư địa để bứt phá lên các mốc cao hơn.")

    # --- 📈 BIỂU ĐỒ TRỰC QUAN ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Gold'], name="Giá Vàng", line=dict(color='#FFD700', width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=df['MA200'], name="MA200 (Dài hạn)", line=dict(color='#FF00FF', dash='dash')))
    fig.add_trace(go.Scatter(x=df.index, y=df['DXY'], name="DXY (Trục Phải)", yaxis="y2", line=dict(color='#00CCFF', width=1)))

    fig.update_layout(
        height=650, template="plotly_dark", hovermode="x unified",
        xaxis=dict(rangeslider=dict(visible=True), type="date"),
        yaxis=dict(title="Vàng (USD)"),
        yaxis2=dict(overlaying="y", side="right", showgrid=False, title="DXY"),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- 📉 BIỂU ĐỒ PHỤ: CHỈ BÁO RSI ---
    st.caption("Chỉ báo RSI: >70 là Quá mua (Đỏ), <30 là Quá bán (Xanh)")
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI (14)", line=dict(color='white', width=1)))
    fig_rsi.add_hline(y=70, line_dash="dot", line_color="red")
    fig_rsi.add_hline(y=30, line_dash="dot", line_color="green")
    fig_rsi.update_layout(height=250, template="plotly_dark", margin=dict(t=0, b=0))
    st.plotly_chart(fig_rsi, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi: {str(e)}")
