import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# 1. Cấu hình
st.set_page_config(page_title="Macro AI & Portfolio", layout="wide")
st.title("🧠 Hệ Thống Dự Báo Định Lượng & Quản Lý Danh Mục")

@st.cache_data(ttl=3600)
def get_advanced_data():
    # Tải dữ liệu
    raw = yf.download(['GC=F', 'DX-Y.NYB'], period="max", auto_adjust=True)
    df = pd.DataFrame(index=raw.index)
    
    # Xử lý MultiIndex của yfinance (phiên bản mới)
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
    
    # --- MỚI: Tính Tương quan (Correlation) trong 30 phiên ---
    # Giá trị từ -1 (Nghịch đảo hoàn toàn) đến 1 (Đồng pha hoàn toàn)
    df['Correlation'] = df['Gold'].rolling(window=30).corr(df['DXY'])
    
    # Biến động sau 10 phiên cho Backtest
    df['Return_10d'] = df['Gold'].shift(-10) / df['Gold'] - 1
    
    return df.ffill().dropna()

try:
    df = get_advanced_data()
    curr_price = df['Gold'].iloc[-1]

    # --- SECTION 1: QUẢN LÝ DANH MỤC (PORTFOLIO) ---
    st.sidebar.header("💰 Danh Mục Của Bạn")
    with st.sidebar:
        holdings = st.number_input("Số lượng nắm giữ (oz)", min_value=0.0, value=1.0, step=0.1)
        entry_price = st.number_input("Giá vốn (USD/oz)", min_value=0.0, value=2000.0, step=10.0)
        
        current_value = holdings * curr_price
        total_cost = holdings * entry_price
        pnl = current_value - total_cost
        pnl_pct = (pnl / total_cost * 100) if total_cost > 0 else 0

        st.divider()
        st.subheader("Báo cáo nhanh")
        st.metric("Tổng giá trị", f"${current_value:,.2f}")
        st.metric("Lời / Lỗ", f"${pnl:,.2f}", f"{pnl_pct:.2f}%")

    # --- SECTION 2: DỰ BÁO HIỆN TẠI ---
    st.subheader("🔮 Dự Báo Vị Thế Hiện Tại")
    c1, c2, c3 = st.columns(3)
    
    rsi_val = df['RSI'].iloc[-1]
    with c1:
        st.markdown(f"**Nhiệt độ RSI: {rsi_val:.1f}**")
        if rsi_val > 70: st.error("Trạng thái: QUÁ MUA (Rủi ro)")
        elif rsi_val < 30: st.success("Trạng thái: QUÁ BÁN (Cơ hội)")
        else: st.info("Trạng thái: TRUNG TÍNH")

    with c2:
        dist = ((curr_price - df['MA200'].iloc[-1]) / df['MA200'].iloc[-1]) * 100
        st.markdown(f"**Lệch MA200: {dist:.1f}%**")
        st.write("Vùng an toàn" if abs(dist) < 12 else "⚠️ Cẩn thận đảo chiều")

    with c3:
        # Lấy giá trị tương quan mới nhất
        curr_corr = df['Correlation'].iloc[-1]
        st.markdown(f"**Tương quan Vàng/DXY: {curr_corr:.2f}**")
        if curr_corr < -0.5:
            st.write("✅ Nghịch đảo chuẩn (DXY tăng -> Vàng giảm)")
        elif curr_corr > 0.5:
            st.write("⚠️ Bất thường (Cùng tăng/giảm)")
        else:
            st.write("⚖️ Không rõ ràng")

    # --- SECTION 3: BIỂU ĐỒ TỔNG HỢP ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Gold'], name="Giá Vàng", line=dict(color='#FFD700')))
    fig.add_trace(go.Scatter(x=df.index, y=df['MA200'], name="MA200", line=dict(color='#FF00FF', dash='dash')))
    fig.add_trace(go.Scatter(x=df.index, y=df['DXY'], name="DXY", yaxis="y2", line=dict(color='#00CCFF', width=1)))

    # Điểm mua của bạn trên biểu đồ
    fig.add_hline(y=entry_price, line_dash="dot", line_color="white", annotation_text="Giá vốn của bạn")

    fig.update_layout(
        height=500, template="plotly_dark", hovermode="x unified",
        xaxis=dict(rangeslider=dict(visible=True)),
        yaxis2=dict(overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
        margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- SECTION 4: BẢNG DỮ LIỆU CHI TIẾT (MỚI) ---
    st.divider()
    st.subheader("📋 Dữ Liệu Chi Tiết & Tương Quan (Gold vs DXY)")
    
    with st.expander("Xem bảng dữ liệu chi tiết", expanded=True):
        # Chuẩn bị dữ liệu hiển thị, đảo ngược để xem ngày mới nhất trước
        display_df = df[['Gold', 'DXY', 'RSI', 'Correlation']].sort_index(ascending=False)
        
        # Sử dụng column_config để hiển thị đẹp hơn
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400,
            column_config={
                "Gold": st.column_config.NumberColumn(
                    "Giá Vàng ($)", format="$%.2f"
                ),
                "DXY": st.column_config.NumberColumn(
                    "DXY Index", format="%.2f"
                ),
                "RSI": st.column_config.ProgressColumn(
                    "RSI (Sức mạnh)", format="%.1f", min_value=0, max_value=100
                ),
                "Correlation": st.column_config.NumberColumn(
                    "Tương quan (30p)", format="%.2f"
                )
            }
        )
        st.caption("*Tương quan (Correlation): Gần -1 là ngược chiều nhau, gần 1 là cùng chiều.*")

    # --- SECTION 5: KẾT QUẢ BACKTEST ---
    with st.expander("📊 Xem Dữ Liệu Kiểm Chứng RSI (50 Năm)"):
        overbought_events = df[df['RSI'] > 70].copy()
        win_rate = (overbought_events['Return_10d'] < 0).sum() / len(overbought_events) * 100
        avg_ret = overbought_events['Return_10d'].mean() * 100
        
        b1, b2, b3 = st.columns(3)
        b1.metric("Số lần RSI > 70", f"{len(overbought_events)}")
        b2.metric("Xác suất giảm sau đó", f"{win_rate:.1f}%")
        b3.metric("Biến động TB", f"{avg_ret:.2f}%")

except Exception as e:
    st.error(f"Lỗi hệ thống hoặc đường truyền dữ liệu: {str(e)}")
