import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# 1. Cấu hình
st.set_page_config(page_title="Macro AI & Backtest", layout="wide")
st.title("🧠 Hệ Thống Dự Báo Định Lượng & Kiểm Chứng Lịch Sử (Backtest)")

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
    
    # Chỉ báo kỹ thuật
    df['MA200'] = df['Gold'].rolling(window=200).mean()
    
    # RSI
    delta = df['Gold'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Tính biến động sau 10 phiên để Backtest
    df['Return_10d'] = df['Gold'].shift(-10) / df['Gold'] - 1
    
    return df.ffill().dropna()

try:
    df = get_advanced_data()
    curr = df.iloc[-1]
    
    # --- SECTION 1: DỰ BÁO HIỆN TẠI ---
    st.subheader("🔮 Dự Báo Vị Thế Hiện Tại")
    c1, c2, c3 = st.columns(3)
    
    rsi_val = curr['RSI']
    with c1:
        st.markdown(f"**Nhiệt độ RSI: {rsi_val:.1f}**")
        if rsi_val > 70: st.error("Trạng thái: QUÁ MUA")
        elif rsi_val < 30: st.success("Trạng thái: QUÁ BÁN")
        else: st.info("Trạng thái: TRUNG TÍNH")

    with c2:
        dist = ((curr['Gold'] - curr['MA200']) / curr['MA200']) * 100
        st.markdown(f"**Lệch MA200: {dist:.1f}%**")
        st.write("Giá đang bám sát xu hướng dài hạn." if abs(dist) < 10 else "Giá đang quá xa vùng cân bằng.")

    with c3:
        dxy_trend = df['DXY'].iloc[-1] - df['DXY'].iloc[-10]
        st.markdown("**Xu Hướng DXY (10 phiên)**")
        st.write("📈 USD Mạnh (Áp lực Vàng)" if dxy_trend > 0 else "📉 USD Yếu (Hỗ trợ Vàng)")

    # --- SECTION 2: BACKTEST (KIỂM CHỨNG LỊCH SỬ) ---
    st.divider()
    st.subheader("📊 Kết Quả Backtest: Khi RSI > 70 trong 50 năm qua")
    
    # Lọc các điểm Quá mua trong lịch sử
    overbought_events = df[df['RSI'] > 70].copy()
    avg_return = overbought_events['Return_10d'].mean() * 100
    win_rate = (overbought_events['Return_10d'] < 0).sum() / len(overbought_events) * 100 # Tỷ lệ giá giảm sau khi quá mua

    b1, b2, b3 = st.columns(3)
    b1.metric("Số lần Quá mua", f"{len(overbought_events)} lần")
    b2.metric("Xác suất giảm sau 10 ngày", f"{win_rate:.1f}%")
    b3.metric("Biến động TB sau 10 ngày", f"{avg_return:.2f}%")

    st.caption("💡 *Giải thích: Trong quá khứ, khi RSI > 70, có đến " + f"{win_rate:.1f}%" + " trường hợp giá Vàng sẽ giảm hoặc đi ngang trong 10 ngày tiếp theo.*")

    # --- SECTION 3: BIỂU ĐỒ TỔNG HỢP ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Gold'], name="Giá Vàng", line=dict(color='#FFD700')))
    fig.add_trace(go.Scatter(x=df.index, y=df['MA200'], name="MA200", line=dict(color='#FF00FF', dash='dash')))
    fig.add_trace(go.Scatter(x=df.index, y=df['DXY'], name="DXY", yaxis="y2", line=dict(color='#00CCFF', width=1)))

    fig.update_layout(
        height=600, template="plotly_dark", hovermode="x unified",
        xaxis=dict(rangeslider=dict(visible=True)),
        yaxis2=dict(overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
    )
    st.plotly_chart(fig, use_container_width=True)

    # Biểu đồ RSI
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='white', width=1)))
    fig_rsi.add_hline(y=70, line_dash="dot", line_color="red", annotation_text="QUÁ MUA")
    fig_rsi.add_hline(y=30, line_dash="dot", line_color="green", annotation_text="QUÁ BÁN")
    fig_rsi.update_layout(height=250, template="plotly_dark", margin=dict(t=0, b=0))
    st.plotly_chart(fig_rsi, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi: {str(e)}")
