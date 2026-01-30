import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# 1. Cấu hình trang (Phải đặt đầu tiên)
st.set_page_config(page_title="Gold Portfolio VND", layout="wide")
st.title("🧠 Quản Lý Danh Mục Vàng & Vĩ Mô (VNĐ)")

@st.cache_data(ttl=3600)
def get_data():
    # Tải dữ liệu: Vàng, DXY, Tỷ giá USD/VND
    # Thêm biến 'tickers' để code rõ ràng hơn
    tickers = ['GC=F', 'DX-Y.NYB', 'VND=X']
    raw = yf.download(tickers, period="max", auto_adjust=True)
    
    if raw.empty: return pd.DataFrame()

    df = pd.DataFrame(index=raw.index)
    
    # Xử lý dữ liệu MultiIndex từ yfinance
    try:
        # Trường hợp 1: Dữ liệu trả về dạng chuẩn
        df['Gold'] = raw['Close']['GC=F']
        df['DXY'] = raw['Close']['DX-Y.NYB']
        df['USDVND'] = raw['Close']['VND=X']
    except KeyError:
        # Trường hợp 2: Dữ liệu trả về dạng MultiLevel (thường gặp)
        try:
            df['Gold'] = raw.xs('GC=F', axis=1, level=1)['Close']
            df['DXY'] = raw.xs('DX-Y.NYB', axis=1, level=1)['Close']
            df['USDVND'] = raw.xs('VND=X', axis=1, level=1)['Close']
        except:
            # Fallback nếu cấu trúc khác
            return pd.DataFrame()
    
    # --- TÍNH TOÁN CHỈ BÁO ---
    # 1. Đường trung bình động 200 ngày (MA200)
    df['MA200'] = df['Gold'].rolling(window=200).mean()
    
    # 2. RSI (14 ngày)
    delta = df['Gold'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    # Tránh chia cho 0
    loss = loss.replace(0, 1e-10) 
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    
    return df.ffill().dropna()

try:
    df = get_data()
    
    if df.empty or len(df) < 200:
        st.error("Chưa tải được dữ liệu hoặc dữ liệu không đủ. Vui lòng thử lại sau.")
    else:
        curr = df.iloc[-1]
        
        # --- PHẦN 1: SIDEBAR QUẢN LÝ TÀI SẢN ---
        st.sidebar.header("🇻🇳 Danh Mục (VNĐ)")
        with st.sidebar:
            holdings = st.number_input("Số lượng (oz)", min_value=0.0, value=1.0, step=0.1)
            entry_usd = st.number_input("Giá vốn (USD/oz)", min_value=0.0, value=2000.0, step=10.0)
            
            # Tính toán
            rate = curr['USDVND']
            curr_price_usd = curr['Gold']
            
            total_value_usd = holdings * curr_price_usd
            total_value_vnd = total_value_usd * rate
            
            profit_usd = (curr_price_usd - entry_usd) * holdings
            profit_vnd = profit_usd * rate
            
            if entry_usd > 0:
                pnl_pct = ((curr_price_usd - entry_usd) / entry_usd) * 100
            else:
                pnl_pct = 0

            st.divider()
            st.metric("Tỷ giá USD/VND", f"{rate:,.0f}đ")
            st.metric("Tổng giá trị", f"{total_value_vnd:,.0f}đ")
            st.metric("Lời / Lỗ", f"{profit_vnd:,.0f}đ", f"{pnl_pct:.2f}%")

        # --- PHẦN 2: BIỂU ĐỒ CHÍNH ---
        # Tạo khung biểu đồ 2 dòng
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.08, 
            row_heights=[0.7, 0.3],
            specs=[[{"secondary_y": True}], [{}]]
        )

        # Hàng 1: Giá Vàng & DXY
        fig.add_trace(go.Scatter(x=df.index, y=df['Gold'], name="Vàng (USD)", line=dict(color='#FFD700')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MA200'], name="MA200", line=dict(color='#FF00FF', dash='dash')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['DXY'], name="DXY", line=dict(color='#00CCFF', width=1)), row=1, col=1, secondary_y=True)

        # Hàng 2: RSI
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='white')), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)

        # Cấu hình giao diện & Thanh kéo thời gian
        fig.update_layout(
            height=700, 
            template="plotly_dark", 
            hovermode="x unified",
            xaxis2_rangeslider_visible=True,  # Thanh kéo nằm ở biểu đồ dưới cùng
            xaxis2_rangeslider_thickness=0.05,
            legend=dict(orientation="h", y=1.05, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- PHẦN 3: PHÂN TÍCH NHANH ---
        st.subheader("📊 Thông số kỹ thuật hiện tại")
        c1, c2, c3 = st.columns(3)
        
        # Chỉ số RSI
        rsi_state = "QUÁ MUA (Nóng)" if curr['RSI'] > 70 else "QUÁ BÁN (Lạnh)" if curr['RSI'] < 30 else "Trung tính"
        c1.metric("RSI (Sức mạnh)", f"{curr['RSI']:.1f}", rsi_state)
        
        # Độ lệch MA200
        dist_ma = ((curr['Gold'] - curr['MA200']) / curr['MA200']) * 100
        c2.metric("Khoảng cách MA200", f"{dist_ma:.1f}%", "Cao hơn TB" if dist_ma > 0 else "Thấp hơn TB")
        
        # Xu hướng DXY ngắn hạn
        dxy_change = curr['DXY'] - df['DXY'].iloc[-22] # So với 1 tháng trước (khoảng 22 phiên)
        c3.metric("DXY (1 tháng qua)", f"{curr['DXY']:.2f}", f"{dxy_change:.2f} điểm")

        # --- PHẦN 4: NHẬT KÝ GIAO DỊCH (Đã sửa lỗi String) ---
        st.divider()
        st.subheader("📝 Nhật ký & Ghi chú")
        # Dòng dưới đây đã được viết gọn trên 1 dòng để tránh lỗi SyntaxError
        note = st.text_area("Ghi chú kế hoạch giao dịch (Ví dụ: Mua khi RSI < 30)...")
        
        if st.button("Lưu ghi chú"):
            st.success("Đã lưu ghi chú tạm thời!")

except Exception as e:
    st.error(f"Lỗi hệ thống: {str(e)}")
