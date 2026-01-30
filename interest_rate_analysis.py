import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# 1. Cấu hình trang
st.set_page_config(page_title="Global Interest Rate Correlation", layout="wide")
st.title("🏦 Phân Tích Tương Quan Lãi Suất: USD - JPY - VND")
st.markdown("""
Biểu đồ sử dụng **Lợi suất trái phiếu Chính phủ 10 năm** làm chỉ số đại diện cho mặt bằng lãi suất.
* **US10Y**: Lợi suất trái phiếu Mỹ (Đại diện lãi suất USD)
* **JP10Y**: Lợi suất trái phiếu Nhật (Đại diện lãi suất JPY)
* **VN10Y**: Lợi suất trái phiếu Việt Nam (Dữ liệu từ Investing/TradingView - ở đây dùng mã mô phỏng hoặc dữ liệu có sẵn trên YF nếu khả dụng)
""")

@st.cache_data(ttl=3600)
def get_rate_data():
    # Tickers: US 10Y (^TNX), Japan 10Y (JG10.V), VN 10Y (VND10Y=RR)
    # Lưu ý: Dữ liệu VN10Y trên Yahoo Finance đôi khi bị gián đoạn
    tickers = ['^TNX', 'JG10.V', 'VND10Y=RR']
    raw = yf.download(tickers, period="5y", auto_adjust=True)
    
    df = pd.DataFrame(index=raw.index)
    try:
        df['USD_10Y'] = raw['Close']['^TNX']
        df['JPY_10Y'] = raw['Close']['JG10.V']
        df['VND_10Y'] = raw['Close']['VND10Y=RR']
    except:
        df['USD_10Y'] = raw.xs('^TNX', axis=1, level=1)['Close']
        df['JPY_10Y'] = raw.xs('JG10.V', axis=1, level=1)['Close']
        df['VND_10Y'] = raw.xs('VND10Y=RR', axis=1, level=1)['Close']
    
    return df.ffill().dropna()

try:
    df = get_rate_data()
    
    # 2. Hiển thị thông số hiện tại
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Lãi suất USD (10Y)", f"{curr['USD_10Y']:.2f}%", f"{curr['USD_10Y'] - prev['USD_10Y']:.2f}%")
    c2.metric("Lãi suất JPY (10Y)", f"{curr['JPY_10Y']:.3f}%", f"{curr['JPY_10Y'] - prev['JPY_10Y']:.3f}%")
    c3.metric("Lãi suất VND (10Y)", f"{curr['VND_10Y']:.2f}%", f"{curr['VND_10Y'] - prev['VND_10Y']:.2f}%")

    # 3. Phân tích chênh lệch lãi suất (Interest Rate Differential)
    st.subheader("🤖 Phân Tích Tương Quan & Carry Trade")
    diff_us_jp = curr['USD_10Y'] - curr['JPY_10Y']
    diff_us_vn = curr['USD_10Y'] - curr['VND_10Y']
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Chênh lệch USD - JPY: {diff_us_jp:.2f}%**")
        if diff_us_jp > 3:
            st.warning("⚠️ Chênh lệch quá lớn: Áp lực mất giá cực mạnh lên đồng Yên (JPY) và thúc đẩy chiến lược Carry Trade.")
    with col2:
        st.info(f"**Chênh lệch USD - VND: {diff_us_vn:.2f}%**")
        if diff_us_vn > 0:
            st.warning("📉 USD Yield cao hơn VND: Gây áp lực lên tỷ giá USD/VND và dự trữ ngoại hối của Ngân hàng Nhà nước.")
        else:
            st.success("✅ VND Yield cao hơn USD: Hỗ trợ ổn định tỷ giá nội tệ.")

    # 4. Vẽ biểu đồ tương quan
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(x=df.index, y=df['USD_10Y'], name="Lãi suất Mỹ (USD)", line=dict(color='#FF4B4B', width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=df['VND_10Y'], name="Lãi suất VN (VND)", line=dict(color='#FBC02D', width=2)))
    
    # JPY thường rất thấp, cho sang trục phụ để thấy biến động
    fig.add_trace(go.Scatter(x=df.index, y=df['JPY_10Y'], name="Lãi suất Nhật (JPY - Trục Phải)", 
                             yaxis="y2", line=dict(color='#1E88E5', width=2)))

    fig.update_layout(
        height=600, template="plotly_dark", hovermode="x unified",
        title="Biến Động Lãi suất Trái phiếu Chính phủ 10 Năm",
        xaxis=dict(rangeslider=dict(visible=True)),
        yaxis=dict(title="Lãi suất (%)", side="left"),
        yaxis2=dict(title="Lãi suất JPY (%)", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
    )
    
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi tải dữ liệu: {e}")
    st.info("Lưu ý: Dữ liệu lãi suất VND trên Yahoo Finance thường bị trễ hoặc thiếu. Bạn có thể cần nhập thủ công nếu muốn độ chính xác tuyệt đối.")
