import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# 1. Cấu hình trang web
st.set_page_config(page_title="Macro Gold Dashboard", layout="wide")
st.title("📊 Hệ Thống Giám Sát Tài Chính Toàn Cầu")
st.markdown("---")

# 2. Hàm tải và xử lý dữ liệu (Đã sửa lỗi lệch cột)
@st.cache_data(ttl=3600)
def get_data():
    # Danh sách mã: Vàng, Bạc, Chỉ số DXY
    tickers = ['GC=F', 'SI=F', 'DX-Y.NYB']
    
    # Tải dữ liệu 2 năm gần nhất
    raw = yf.download(tickers, period="2y", auto_adjust=True)
    
    if raw.empty:
        return pd.DataFrame()

    # Tạo DataFrame mới và bóc tách từng mã để tránh lệch cột
    df = pd.DataFrame(index=raw.index)
    
    # Bóc tách chính xác từng cột Close (Đóng cửa)
    try:
        df['Gold'] = raw['Close']['GC=F']
        df['Silver'] = raw['Close']['SI=F']
        df['DXY'] = raw['Close']['DX-Y.NYB']
    except:
        # Cách dự phòng nếu cấu hình Yahoo Finance thay đổi
        df['Gold'] = raw.xs('GC=F', axis=1, level=1)['Close']
        df['Silver'] = raw.xs('SI=F', axis=1, level=1)['Close']
        df['DXY'] = raw.xs('DX-Y.NYB', axis=1, level=1)['Close']

    return df.dropna()

try:
    df = get_data()

    if not df.empty:
        # Tính toán tỷ lệ Vàng/Bạc
        df['Ratio'] = df['Gold'] / df['Silver']
        
        # Lấy giá trị mới nhất
        last_gold = df['Gold'].iloc[-1]
        last_silver = df['Silver'].iloc[-1]
        last_dxy = df['DXY'].iloc[-1]
        last_ratio = df['Ratio'].iloc[-1]
        last_date = df.index[-1].strftime('%d/%m/%Y')

        st.write(f"Dữ liệu cập nhật ngày: **{last_date}**")

        # 3. Hiển thị các chỉ số chính (Metrics)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Vàng (USD/oz)", f"${last_gold:,.2f}")
        c2.metric("Bạc (USD/oz)", f"${last_silver:,.2f}")
        c3.metric("Chỉ số DXY", f"{last_dxy:.2f}")
        c4.metric("Tỷ lệ Vàng/Bạc", f"{last_ratio:.1f}")

        # 4. Vẽ biểu đồ chuyên sâu
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.07,
            subplot_titles=("Xu hướng Vàng & Bạc", "Sức mạnh đồng USD (DXY)"),
            row_width=[0.4, 0.6]
        )

        # Biểu đồ Vàng & Bạc (Tầng 1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Gold'], name="Vàng", line=dict(color='#FFD700', width=2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Silver'], name="Bạc", line=dict(color='#C0C0C0', width=1.5)), row=1, col=1)

        # Biểu đồ DXY (Tầng 2)
        fig.add_trace(go.Scatter(x=df.index, y=df['DXY'], name="DXY", fill='tozeroy', line=dict(color='#00CCFF')), row=2, col=1)

        # Tinh chỉnh giao diện biểu đồ
        fig.update_layout(
            height=800, 
            template="plotly_dark", 
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

        # 5. Khu vực bảng dữ liệu và tải về
        with st.expander("Xem chi tiết bảng số liệu"):
            # Sắp xếp ngày mới nhất lên đầu
            st.dataframe(df.sort_index(ascending=False), use_container_width=True)
            st.download_button(
                label="📥 Tải dữ liệu CSV về máy",
                data=df.to_csv(),
                file_name=f"macro_data_{last_date}.csv",
                mime="text/csv"
            )
    else:
        st.error("Không thể tải dữ liệu. Hãy thử nhấn 'Reboot App' trong mục Manage App.")

except Exception as e:
    st.error(f"Đã xảy ra lỗi hệ thống: {e}")
