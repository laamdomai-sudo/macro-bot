import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# 1. Cấu hình (CHỈ GỌI 1 LẦN DUY NHẤT Ở ĐẦU)
st.set_page_config(page_title="Macro AI Predictor", layout="wide")
st.title("🧠 Hệ Thống Dự Báo & Quản Lý Danh Mục Vàng - DXY")

@st.cache_data(ttl=3600)
def get_advanced_data():
    # Tải dữ liệu
    raw = yf.download(['GC=F', 'DX-Y.NYB'], period="max", auto_adjust=True)
    
    if raw.empty or len(raw) < 200:
        return pd.DataFrame()

    df = pd.DataFrame(index=raw.index)
    
    # Xử lý MultiIndex của yfinance
    try:
        df['Gold'] = raw['Close']['GC=F']
        df['DXY'] = raw['Close']['DX-Y.NYB']
    except:
        df['Gold'] = raw.xs('GC=F', axis=1, level=1)['Close']
        df['DXY'] = raw.xs('DX-Y.NYB', axis=1, level=1)['Close']
    
    # Tính toán chỉ báo
    df['MA200'] = df['Gold'].rolling(window=200).mean()
    
    # RSI
    delta = df['Gold'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Các chỉ số bổ sung
    df['Dist_MA200'] = ((df['Gold'] - df['MA200']) / df['MA200']) * 100
    df['Return_10d'] = df['Gold'].shift(-10) / df['Gold'] - 1
    
    # Chỉ dropna sau khi đã tính xong MA200 để đảm bảo có đủ dữ liệu
    return df.dropna()

# Thực thi chính
try:
    df = get_advanced_data()
    
    if df.empty or len(df) < 2:
        st.error("Không đủ dữ liệu để phân tích. Vui lòng thử lại sau hoặc kiểm tra kết nối mạng.")
    else:
        # Lấy dữ liệu dòng cuối và dòng kế cuối an toàn
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        curr_price = curr['Gold']

        # --- PHẦN 1: SIDEBAR QUẢN LÝ DANH MỤC ---
        st.sidebar.header("💰 Danh Mục Của Bạn")
        holdings = st.sidebar.number_input("Số lượng nắm giữ (oz)", min_value=0.0, value=1.0, step=0.1)
        entry_price = st.sidebar.number_input("Giá vốn (USD/oz)", min_value=0.0, value=2000.0, step=10.0)
        
        current_value = holdings * curr_price
        total_cost = holdings * entry_price
        pnl = current_value - total_cost
        pnl_pct = (pnl / total_cost * 100) if total_cost > 0 else 0

        st.sidebar.divider()
        st.sidebar.subheader("Báo cáo nhanh")
        st.sidebar.metric("Tổng giá trị", f"${current_value:,.2f}")
        st.sidebar.metric("Lời / Lỗ", f"${pnl:,.2f}", f"{pnl_pct:.2f}%")

        # --- PHẦN 2: TRẠM DỰ BÁO ---
        st.subheader("🔮 Hệ Thống Dự Báo & Đánh Giá Vị Thế")
        c1, c2, c3 = st.columns(3)

        with c1:
            rsi_val = curr['RSI']
            st.markdown(f"#### 🌡️ RSI: {rsi_val:.1f}")
            if rsi_val > 70: st.error("QUÁ MUA: Rủi ro điều chỉnh cao.")
            elif rsi_val < 30: st.success("QUÁ BÁN: Cơ hội hồi phục.")
            else: st.info("TRUNG TÍNH: Xu hướng ổn định.")

        with c2:
            dist = curr['Dist_MA200']
            st.markdown(f"#### 📏 Lệch MA200: {dist:.1f}%")
            if abs(dist) > 15: st.warning("CẢNH BÁO: Giá đang quá xa đường trung bình.")
            else: st.success("VÙNG AN TOÀN: Bám sát xu hướng dài hạn.")

        with c3:
            dxy_trend = df['DXY'].iloc[-1] - df['DXY'].iloc[-10]
            st.markdown("#### 🎯 Xu Hướng DXY")
            if dxy_trend > 0: st.error("📉 DỰ BÁO GIẢM: DXY mạnh gây áp lực lên Vàng.")
            else: st.success("📈 DỰ BÁO TĂNG: DXY yếu ủng hộ giá Vàng.")

        # --- PHẦN 3: BIỂU ĐỒ ---
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Gold'], name="Giá Vàng", line=dict(color='#FFD700')))
        fig.add_trace(go.Scatter(x=df.index, y=df['MA200'], name="MA200", line=dict(color='#FF00FF', dash='dash')))
        fig.add_trace(go.Scatter(x=df.index, y=df['DXY'], name="DXY", yaxis="y2", line=dict(color='#00CCFF', width=1)))
        
        # Đường giá vốn
        fig.add_hline(y=entry_price, line_dash="dot", line_color="white", annotation_text="Giá vốn")

        fig.update_layout(
            height=500, template="plotly_dark", hovermode="x unified",
            yaxis2=dict(overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- PHẦN 4: BACKTEST ---
        with st.expander("📊 Xem Dữ Liệu Kiểm Chứng RSI"):
            overbought = df[df['RSI'] > 70].copy()
            if not overbought.empty:
                win_rate = (overbought['Return_10d'] < 0).sum() / len(overbought) * 100
                st.metric("Xác suất giảm sau khi Quá Mua (>70)", f"{win_rate:.1f}%")
            else:
                st.write("Chưa có dữ liệu quá mua trong tập dữ liệu này.")

except Exception as e:
    st.error(f"Đã xảy ra lỗi hệ thống: {e}")
