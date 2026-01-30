import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# 1. Cấu hình
st.set_page_config(page_title="FX & Rates Fast Load", layout="wide")
st.title("🏦 Tương Quan Lãi Suất & Tỷ Giá (Tối ưu tốc độ)")

# Sidebar để cấu hình dự phòng
with st.sidebar:
    st.header("⚙️ Cấu hình dự phòng")
    st.info("Nếu dữ liệu VND từ máy chủ bị chậm, hệ thống sẽ tự động dùng giá trị này.")
    manual_vnd_rate = st.number_input("Lãi suất VND 10Y (%)", value=2.7, step=0.1)
    manual_vnd_fx = st.number_input("Tỷ giá USD/VND dự phòng", value=25400, step=10)

@st.cache_data(ttl=600) # Giảm cache xuống 10 phút để cập nhật nhanh hơn
def get_fast_data():
    # Nhóm 1: Các mã chính (Cực kỳ ổn định)
    main_tickers = ['^TNX', 'JG10.V', 'USDJPY=X', 'USDVND=X']
    df_main = yf.download(main_tickers, period="1y", interval="1d", group_by='ticker', timeout=10)
    
    df = pd.DataFrame(index=df_main.index)
    
    # Trích xuất dữ liệu an toàn
    try:
        df['USD_10Y'] = df_main['^TNX']['Close']
        df['JPY_10Y'] = df_main['JG10.V']['Close']
        df['USDJPY'] = df_main['USDJPY=X']['Close']
        df['USDVND'] = df_main['USDVND=X']['Close']
    except Exception:
        # Fallback nếu cấu trúc dataframe khác (Multi-index)
        df['USD_10Y'] = df_main.xs('^TNX', axis=1, level=0)['Close']
        df['JPY_10Y'] = df_main.xs('JG10.V', axis=1, level=0)['Close']
        df['USDJPY'] = df_main.xs('USDJPY=X', axis=1, level=0)['Close']
        df['USDVND'] = df_main.xs('USDVND=X', axis=1, level=0)['Close']

    # Nhóm 2: Thử tải VND Bond (Thường gây chậm)
    try:
        vn_bond = yf.download('VND10Y=RR', period="1y", timeout=5)['Close']
        if not vn_bond.empty:
            df['VND_10Y'] = vn_bond
        else:
            df['VND_10Y'] = manual_vnd_rate
    except:
        df['VND_10Y'] = manual_vnd_rate
        
    return df.ffill().fillna(method='bfill')

try:
    with st.spinner('🚀 Đang kết nối máy chủ tài chính...'):
        df = get_fast_data()
    
    if not df.empty and 'USDVND' in df.columns:
        curr = df.iloc[-1]
        prev = df.iloc[-2]

        # 2. Hiển thị Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("USD/VND", f"{curr['USDVND']:,.0f}", f"{curr['USDVND'] - prev['USDVND']:,.0f}")
        m2.metric("USD/JPY", f"{curr['USDJPY']:.2f}", f"{curr['USDJPY'] - prev['USDJPY']:.2f}")
        m3.metric("Lãi suất Mỹ", f"{curr['USD_10Y']:.2f}%")
        m4.metric("Lãi suất Nhật", f"{curr['JPY_10Y']:.3f}%")

        # 3. Biểu đồ Lãi suất
        fig_rates = go.Figure()
        fig_rates.add_trace(go.Scatter(x=df.index, y=df['USD_10Y'], name="US 10Y", line=dict(color='#FF4B4B')))
        fig_rates.add_trace(go.Scatter(x=df.index, y=df['VND_10Y'], name="VN 10Y", line=dict(color='#FBC02D')))
        fig_rates.add_trace(go.Scatter(x=df.index, y=df['JPY_10Y'], name="JP 10Y (Trục phải)", yaxis="y2", line=dict(color='#1E88E5')))
        
        fig_rates.update_layout(height=350, template="plotly_dark", title="Mặt bằng Lãi suất",
                                yaxis2=dict(overlaying="y", side="right", showgrid=False), margin=dict(t=30, b=0))
        st.plotly_chart(fig_rates, use_container_width=True)

        # 4. Biểu đồ Tỷ giá
        fig_fx = go.Figure()
        fig_fx.add_trace(go.Scatter(x=df.index, y=df['USDVND'], name="USD/VND", line=dict(color='#00C853')))
        fig_fx.add_trace(go.Scatter(x=df.index, y=df['USDJPY'], name="USD/JPY (Trục phải)", yaxis="y2", line=dict(color='#AA00FF')))
        
        fig_fx.update_layout(height=350, template="plotly_dark", title="Biến động Tỷ giá",
                             yaxis2=dict(overlaying="y", side="right", showgrid=False), margin=dict(t=30, b=0))
        st.plotly_chart(fig_fx, use_container_width=True)

        # 5. Phân tích nhanh
        st.info(f"💡 **Nhận định:** Chênh lệch lãi suất Mỹ - Việt Nam đang là **{(curr['USD_10Y'] - curr['VND_10Y']):.2f}%**. "
                "Nếu con số này dương và tiếp tục tăng, tỷ giá USD/VND sẽ chịu áp lực tăng giá.")

    else:
        st.error("❌ Không thể lấy dữ liệu. Hãy nhấn F5 hoặc kiểm tra lại Sidebar.")

except Exception as e:
    st.error(f"Lỗi: {e}")
