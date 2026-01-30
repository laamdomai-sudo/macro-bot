import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# 1. Cấu hình trang web
st.set_page_config(page_title="Macro AI Dashboard", layout="wide")
st.title("📊 Hệ Thống Giám Sát & Phân Tích Tài Chính Tự Động")
st.markdown("---")

# 2. Hàm tải và xử lý dữ liệu chuẩn
@st.cache_data(ttl=3600)
def get_data():
    tickers = ['GC=F', 'SI=F', 'DX-Y.NYB']
    raw = yf.download(tickers, period="2y", auto_adjust=True)
    if raw.empty: return pd.DataFrame()

    df = pd.DataFrame(index=raw.index)
    try:
        df['Gold'] = raw['Close']['GC=F']
        df['Silver'] = raw['Close']['SI=F']
        df['DXY'] = raw['Close']['DX-Y.NYB']
    except:
        df['Gold'] = raw.xs('GC=F', axis=1, level=1)['Close']
        df['Silver'] = raw.xs('SI=F', axis=1, level=1)['Close']
        df['DXY'] = raw.xs('DX-Y.NYB', axis=1, level=1)['Close']
    
    return df.dropna()

try:
    df = get_data()
    if not df.empty:
        df['Ratio'] = df['Gold'] / df['Silver']
        
        # Lấy giá trị hiện tại và phiên trước
        last_gold, prev_gold = df['Gold'].iloc[-1], df['Gold'].iloc[-2]
        last_silver, prev_silver = df['Silver'].iloc[-1], df['Silver'].iloc[-2]
        last_dxy, prev_dxy = df['DXY'].iloc[-1], df['DXY'].iloc[-2]
        last_ratio = df['Ratio'].iloc[-1]
        last_date = df.index[-1].strftime('%d/%m/%Y')

        # 3. Hiển thị các chỉ số chính
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Vàng (USD/oz)", f"${last_gold:,.2f}", f"{last_gold - prev_gold:,.2f}")
        c2.metric("Bạc (USD/oz)", f"${last_silver:,.2f}", f"{last_silver - prev_silver:,.2f}")
        c3.metric("Chỉ số DXY", f"{last_dxy:.2f}", f"{last_dxy - prev_dxy:.2f}")
        c4.metric("Tỷ lệ Vàng/Bạc", f"{last_ratio:.1f}")

        # --- 🤖 PHẦN MỚI: TỰ ĐỘNG PHÂN TÍCH ---
        st.subheader("🤖 Trạm Phân Tích Thông Minh")
        col_a, col_b = st.columns(2)

        with col_a:
            # Logic phân tích Ratio
            if last_ratio > 80:
                st.info(f"🚩 **Tỷ lệ ({last_ratio:.1f}):** Vàng đang quá đắt so với Bạc. Lịch sử ủng hộ việc tích lũy **Bạc**.")
            elif last_ratio < 50:
                st.warning(f"🚩 **Tỷ lệ ({last_ratio:.1f}):** Bạc đang cực kỳ nóng. Cẩn thận nhịp điều chỉnh, **Vàng** hiện an toàn hơn.")
            else:
                st.success(f"🚩 **Tỷ lệ ({last_ratio:.1f}):** Tương quan Vàng/Bạc ở mức cân bằng.")

        with col_b:
            # Logic phân tích tương quan Gold vs DXY
            gold_up = last_gold > prev_gold
            dxy_up = last_dxy > prev_dxy

            if gold_up and not dxy_up:
                st.success("📈 **Xu hướng:** Vàng tăng do DXY giảm. Đây là biến động thuận chiều vĩ mô điển hình.")
            elif gold_up and dxy_up:
                st.error("⚠️ **Cảnh báo:** Cả Vàng và DXY cùng tăng. Thị trường đang cực kỳ hoảng loạn
