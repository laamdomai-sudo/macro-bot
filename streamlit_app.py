import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# 1. Cấu hình trang web
st.set_page_config(page_title="Macro AI Dashboard", layout="wide")
st.title("📊 Hệ Thống Giám Sát & Phân Tích Tài Chính Tự Động")
st.markdown("---")

# 2. Hàm tải dữ liệu (An toàn tuyệt đối)
@st.cache_data(ttl=3600)
def get_data():
    tickers = ['GC=F', 'SI=F', 'DX-Y.NYB']
    # Tải dữ liệu
    raw = yf.download(tickers, period="2y", auto_adjust=True)
    
    if raw.empty: return pd.DataFrame()

    df = pd.DataFrame(index=raw.index)
    
    # Xử lý bóc tách dữ liệu để tránh lỗi
    try:
        # Cách lấy dữ liệu chuẩn
        df['Gold'] = raw['Close']['GC=F']
        df['Silver'] = raw['Close']['SI=F']
        df['DXY'] = raw['Close']['DX-Y.NYB']
    except:
        # Cách lấy dữ liệu dự phòng
        try:
            df['Gold'] = raw.xs('GC=F', axis=1, level=1)['Close']
            df['Silver'] = raw.xs('SI=F', axis=1, level=1)['Close']
            df['DXY'] = raw.xs('DX-Y.NYB', axis=1, level=1)['Close']
        except:
            pass # Bỏ qua nếu lỗi
            
    return df.dropna()

try:
    df = get_data()

    if not df.empty:
        # Tính toán các chỉ số
        df['Ratio'] = df['Gold'] / df['Silver']
        
        # Lấy giá trị hiện tại và phiên trước đó
        last_gold = df['Gold'].iloc[-1]
        prev_gold = df['Gold'].iloc[-2]
        
        last_silver = df['Silver'].iloc[-1]
        prev_silver = df['Silver'].iloc[-2]
        
        last_dxy = df['DXY'].iloc[-1]
        prev_dxy = df['DXY'].iloc[-2]
        
        last_ratio = df['Ratio'].iloc[-1]
        last_date = df.index[-1].strftime('%d/%m/%Y')

        st.write(f"Dữ liệu cập nhật ngày: **{last_date}**")

        # 3. Hiển thị Metrics (Chỉ số)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Vàng (USD/oz)", f"${last_gold:,.2f}", f"{last_gold - prev_gold:,.2f}")
        c2.metric("Bạc (USD/oz)", f"${last_silver:,.2f}", f"{last_silver - prev_silver:,.2f}")
        c3.metric("Chỉ số DXY", f"{last_dxy:.2f}", f"{last_dxy - prev_dxy:.2f}")
        c4.metric("Tỷ lệ Vàng/Bạc", f"{last_ratio:.1f}", f"{last_ratio - df['Ratio'].iloc[-2]:.2f}")

        # --- 🤖 TRẠM PHÂN TÍCH THÔNG MINH (Đã sửa lỗi hiển thị) ---
        st.subheader("🤖 Trạm Phân Tích Thông Minh")
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("#### 🔍 Định giá Vàng/Bạc")
            # Logic Ratio
            if last_ratio > 80:
                st.info(f"""🔴 **Tỷ lệ cao ({last_ratio:.1f}):** Vàng đang quá đắt so với Bạc. Lịch sử cho thấy đây là vùng giá hấp dẫn để tích lũy Bạc.""")
            elif last_ratio < 50:
                st.warning(f"""⚠️ **Tỷ lệ thấp ({last_ratio:.1f}):** Bạc đang tăng nóng. Dòng tiền có xu hướng chốt lời Bạc để quay lại Vàng an toàn hơn.""")
            else:
                st.success(f"""🟢 **Tỷ lệ cân bằng ({last_ratio:.1f}):** Thị trường kim loại quý đang phát triển ổn định, chưa có sự lệch pha quá mức.""")

        with col_b:
            st.markdown("#### ⚡ Tương quan Vĩ mô (Vàng vs DXY)")
            # Logic Tương quan
            gold_up = last_gold > prev_gold
            dxy_up = last_dxy > prev_dxy

            if gold_up and not dxy_up:
                st.success("""✅ **Tương quan Chuẩn:** Vàng tăng + DXY giảm. Đồng USD suy yếu đang là động lực chính đẩy giá Vàng đi lên.""")
            elif gold_up and dxy_up:
                st.error("""🚨 **Cảnh báo Bất thường:** Cả Vàng và DXY cùng tăng. Dòng tiền đang cực kỳ hoảng loạn, tìm mọi nơi trú ẩn (Cash + Gold).""")
            elif not gold_up and dxy_up:
                st.warning("""📉 **Áp lực Tỷ giá:** Đồng USD hồi phục mạnh đang gây áp lực khiến giá Vàng điều chỉnh giảm.""")
            else:
                st.info("""💤 **Thị trường Lưỡng lự:** Cả hai chỉ số cùng giảm nhẹ hoặc đi ngang, chờ đợi tin tức kinh tế mới.""")

        # 4. Vẽ biểu đồ 2 tầng
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                            subplot_titles=("Xu hướng giá Vàng & Bạc", "Sức mạnh đồng USD (DXY)"),
                            row_width=[0.4, 0.6])

        # Tầng 1: Gold & Silver
        fig.add_trace(go.Scatter(x=df.index, y=df['Gold'], name="Vàng", line=dict(color='#FFD700', width=2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Silver'], name="Bạc", line=dict(color='#C0C0C0', width=1.5)), row=1, col=1)

        # Tầng 2: DXY
        fig.add_trace(go.Scatter(x=df.index, y=df['DXY'], name="DXY", fill='tozeroy', line=dict(color='#00CCFF')), row=2, col=1)

        fig.update_layout(height=800, template="plotly_dark", hovermode="x unified", 
                          legend=dict(orientation="h", y=1.02))
        
        st.plotly_chart(fig, use_container_width=True)

        # 5. Khu vực tải dữ liệu
        with st.expander("📥 Xem bảng dữ liệu chi tiết"):
            st.dataframe(df.sort_index(ascending=False), use_container_width=True)
            st.download_button("Tải file Excel/CSV", df.to_csv(), "macro_data.csv")
    
    else:
        st.error("⚠️ Không lấy được dữ liệu. Vui lòng thử lại sau vài phút hoặc nhấn Reboot App.")

except Exception as e:
    st.error(f"Lỗi hệ thống: {e}")

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# 1. Cấu hình trang
st.set_page_config(page_title="Macro Correlation Dashboard", layout="wide")
st.title("📊 Phân Tích Tương Quan Lãi Suất & Kim Loại Quý")

@st.cache_data(ttl=3600)
def get_macro_data():
    # Tickers: Vàng, DXY, LS Mỹ 10Y, LS Nhật 10Y, Tỷ giá USDVND
    tickers = ['GC=F', 'DX-Y.NYB', '^TNX', '^JGBSY', 'USDVND=X']
    raw = yf.download(tickers, period="2y", auto_adjust=True)
    
    if raw.empty:
        return pd.DataFrame()

    df = pd.DataFrame(index=raw.index)
    try:
        # Sử dụng .xs để bóc tách dữ liệu an toàn từ Multi-index
        df['Gold'] = raw.xs('GC=F', axis=1, level=1)['Close']
        df['DXY'] = raw.xs('DX-Y.NYB', axis=1, level=1)['Close']
        df['US_10Y'] = raw.xs('^TNX', axis=1, level=1)['Close']
        df['JPY_10Y'] = raw.xs('^JGBSY', axis=1, level=1)['Close']
        df['USDVND'] = raw.xs('USDVND=X', axis=1, level=1)['Close']
    except Exception:
        # Cách lấy dự phòng nếu format đơn giản
        for t, name in zip(tickers, ['Gold', 'DXY', 'US_10Y', 'JPY_10Y', 'USDVND']):
            if t in raw['Close']:
                df[name] = raw['Close'][t]
    
    # Điền dữ liệu trống bằng giá trị gần nhất để tránh lỗi out-of-bounds
    return df.ffill().dropna()

try:
    df = get_macro_data()
    
    if df.empty or len(df) < 2:
        st.warning("⚠️ Đang chờ dữ liệu từ Yahoo Finance... Hãy nhấn 'Reboot App' nếu lỗi kéo dài.")
    else:
        # Lấy giá trị phiên hiện tại và phiên trước
        curr = df.iloc[-1]
        prev = df.iloc[-2]

        # 2. Hiển thị Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Lãi suất Mỹ (10Y)", f"{curr['US_10Y']:.2f}%", f"{curr['US_10Y'] - prev['US_10Y']:.2f}")
        c2.metric("Lãi suất Nhật (10Y)", f"{curr['JPY_10Y']:.3f}%", f"{curr['JPY_10Y'] - prev['JPY_10Y']:.3f}")
        c3.metric("Tỷ giá USD/VND", f"{curr['USDVND']:,.0f} đ", f"{curr['USDVND'] - prev['USDVND']:,.0f}")

        # 3. Vẽ biểu đồ tương quan
        fig = make_subplots(
            rows=3, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.07,
            subplot_titles=("Giá Vàng (Vàng) & Chỉ số DXY (Xanh)", "So sánh Lãi suất Mỹ (Đỏ) vs Nhật (Xanh Lá)", "Tỷ giá USD/VND"),
            row_heights=[0.4, 0.4, 0.2]
        )

        # Tầng 1: Gold & DXY
        fig.add_trace(go.Scatter(x=df.index, y=df['Gold'], name="Vàng", line=dict(color='#FFD700')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['DXY'] * (df['Gold'].max()/df['DXY'].max()), name="DXY (Quy đổi)", line=dict(color='#00CCFF', dash='dot')), row=1, col=1)

        # Tầng 2: LS Mỹ vs Nhật (Gộp chung để thấy Spread)
        fig.add_trace(go.Scatter(x=df.index, y=df['US_10Y'], name="LS Mỹ 10Y", line=dict(color='#FF4B4B')), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['JPY_10Y'], name="LS Nhật 10Y", line=dict(color='#00FF00')), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['US_10Y'] - df['JPY_10Y'], name="Chênh lệch (Spread)", fill='tozeroy', line=dict(width=0)), row=2, col=1)

        # Tầng 3: Tỷ giá VND
        fig.add_trace(go.Scatter(x=df.index, y=df['USDVND'], name="USD/VND", line=dict(color='#FF00FF')), row=3, col=1)

        fig.update_layout(height=900, template="plotly_dark", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        # 4. Phân tích tự động
        spread = curr['US_10Y'] - curr['JPY_10Y']
        st.info(f"💡 **Phân tích:** Chênh lệch lãi suất Mỹ - Nhật hiện là **{spread:.2f}%**. Khoảng cách này càng rộng thì áp lực mất giá lên đồng Yên và VND càng lớn.")

except Exception as e:
    st.error(f"Đã xảy ra lỗi: {e}")
