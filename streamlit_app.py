import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# 1. Cấu hình trang
st.set_page_config(page_title="Macro Gold Dashboard", layout="wide")
st.title("📊 Hệ Thống Giám Sát Tài Chính Toàn Cầu")

# 2. Hàm tải dữ liệu an toàn
@st.cache_data(ttl=3600)
def get_data():
    tickers = ['GC=F', 'SI=F', 'DX-Y.NYB']
    # Tải dữ liệu 2 năm gần nhất để biểu đồ mượt mà
    raw = yf.download(tickers, period="2y", auto_adjust=True)
    
    if raw.empty:
        return pd.DataFrame()

    df = pd.DataFrame(index=raw.index)
    
    # Xử lý bóc tách cột cho dù format Yahoo có thay đổi
    for t in tickers:
        try:
            # Thử lấy theo chuẩn mới (Multi-index)
            df[t] = raw['Close'][t]
        except:
            try:
                # Thử lấy theo chuẩn cũ
                df[t] = raw.xs(t, axis=1, level=1)['Close']
            except:
                continue

    df.columns = ['DXY', 'Gold', 'Silver'] # Đặt lại tên cột cho dễ dùng
    return df.dropna()

try:
    df = get_data()

    if not df.empty:
        # Tính toán tỷ lệ
        df['Ratio'] = df['Gold'] / df['Silver']
        last_date = df.index[-1].strftime('%d/%m/%Y')
        
        st.write(f"Cập nhật lần cuối: **{last_date}**")

        # 3. Hiển thị Chỉ số (Metrics)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Vàng (USD/oz)", f"${df['Gold'].iloc[-1]:,.2f}")
        c2.metric("Bạc (USD/oz)", f"${df['Silver'].iloc[-1]:,.2f}")
        c3.metric("Chỉ số DXY", f"{df['DXY'].iloc[-1]:.2f}")
        c4.metric("Tỷ lệ Vàng/Bạc", f"{df['Ratio'].iloc[-1]:.1f}")

        # 4. Vẽ biểu đồ tầng chuyên nghiệp
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.05,
            subplot_titles=("Xu hướng Vàng & Bạc", "Sức mạnh đồng USD (DXY)"),
            row_width=[0.4, 0.6]
        )

        # Tầng 1: Vàng & Bạc
        fig.add_trace(go.Scatter(x=df.index, y=df['Gold'], name="Vàng", line=dict(color='#FFD700', width=2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Silver'], name="Bạc", line=dict(color='#C0C0C0', width=1)), row=1, col=1)

        # Tầng 2: DXY
        fig.add_trace(go.Scatter(x=df.index, y=df['DXY'], name="DXY", fill='tozeroy', line=dict(color='#00CCFF')), row=2, col=1)

        fig.update_layout(height=800, template="plotly_dark", hovermode="x unified", legend=dict(orientation="h", y=1.05))
        st.plotly_chart(fig, use_container_width=True)

        # 5. Khu vực dữ liệu chi tiết
        with st.expander("Xem bảng dữ liệu chi tiết"):
            st.dataframe(df.sort_index(ascending=False), use_container_width=True)
            st.download_button("📥 Tải dữ liệu CSV", df.to_csv(), "macro_data.csv")
    else:
        st.error("Không thể tải dữ liệu. Hãy nhấn 'Reboot App' trong mục Manage App.")

except Exception as e:
    st.error(f"Lỗi hiển thị biểu đồ: {e}")
