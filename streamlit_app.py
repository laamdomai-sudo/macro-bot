import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# 1. Cấu hình giao diện
st.set_page_config(page_title="Macro Gold Dashboard", layout="wide")

st.title("📊 Hệ Thống Giám Sát Kim Loại Quý & DXY")
st.markdown("---")

# 2. Hàm tải dữ liệu (Sửa lỗi Multi-index)
@st.cache_data(ttl=3600)
def get_clean_data():
    tickers = ['GC=F', 'SI=F', 'DX-Y.NYB']
    # Tải dữ liệu
    raw_data = yf.download(tickers, period="max", auto_adjust=True)
    
    # Ép dữ liệu về bảng phẳng để tránh lỗi Column Name
    df = pd.DataFrame()
    try:
        df['Gold'] = raw_data['Close']['GC=F']
        df['Silver'] = raw_data['Close']['SI=F']
        df['DXY'] = raw_data['Close']['DX-Y.NYB']
    except KeyError:
        # Cách dự phòng nếu yfinance trả về format khác
        df['Gold'] = raw_data.xs('GC=F', axis=1, level=1)['Close']
        df['Silver'] = raw_data.xs('SI=F', axis=1, level=1)['Close']
        df['DXY'] = raw_data.xs('DX-Y.NYB', axis=1, level=1)['Close']
        
    df = df.dropna()
    df['Ratio'] = df['Gold'] / df['Silver']
    return df

try:
    data_all = get_clean_data()
    
    # 3. Sidebar tùy chỉnh
    st.sidebar.header("Cài đặt biểu đồ")
    window = st.sidebar.selectbox("Khoảng thời gian", 
                                 ["5 năm", "10 năm", "20 năm", "Toàn bộ"], index=1)
    
    mapping = {"5 năm": 365*5, "10 năm": 365*10, "20 năm": 365*20, "Toàn bộ": len(data_all)}
    df = data_all.tail(mapping[window])

    # 4. Hiển thị Chỉ số (Metrics)
    c1, c2, c3 = st.columns(3)
    c1.metric("Vàng (USD/oz)", f"${df['Gold'].iloc[-1]:,.2f}")
    c2.metric("Chỉ số DXY", f"{df['DXY'].iloc[-1]:.2f}")
    c3.metric("Tỷ giá Vàng/Bạc", f"{df['Ratio'].iloc[-1]:.1f}")

    # 5. Vẽ biểu đồ 2 tầng
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                        subplot_titles=("Xu hướng Vàng & Bạc", "Sức mạnh đồng USD (DXY)"))

    fig.add_trace(go.Scatter(x=df.index, y=df['Gold'], name="Vàng", line=dict(color='#FFD700')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['DXY'], name="DXY", fill='tozeroy', line=dict(color='#00CCFF')), row=2, col=1)

    fig.update_layout(height=800, template="plotly_dark", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    # 6. Nút tải dữ liệu
    st.download_button("📥 Tải dữ liệu (.csv)", df.to_csv(), "macro_data.csv", "text/csv")

except Exception as e:
    st.error(f"Đã xảy ra sự cố: {e}")
    st.info("Mẹo: Hãy kiểm tra file requirements.txt đã có yfinance chưa.")
