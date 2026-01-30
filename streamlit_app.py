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

st.set_page_config(page_title="Macro Full Dashboard", layout="wide")
st.title("📊 Dashboard Tài Chính & Lãi Suất Toàn Cầu")

@st.cache_data(ttl=3600)
def get_full_data():
    # Tickers: Vàng, Bạc, DXY, LS Mỹ 10Y (^TNX), LS Nhật 10Y (^JGBSY)
    tickers = ['GC=F', 'SI=F', 'DX-Y.NYB', '^TNX', '^JGBSY']
    raw = yf.download(tickers, period="2y", auto_adjust=True)
    
    df = pd.DataFrame(index=raw.index)
    try:
        df['Gold'] = raw['Close']['GC=F']
        df['Silver'] = raw['Close']['SI=F']
        df['DXY'] = raw['Close']['DX-Y.NYB']
        df['US_10Y'] = raw['Close']['^TNX']
        df['JPY_10Y'] = raw['Close']['^JGBSY']
    except:
        # Dự phòng Multi-index
        df['Gold'] = raw.xs('GC=F', axis=1, level=1)['Close']
        df['DXY'] = raw.xs('DX-Y.NYB', axis=1, level=1)['Close']
        df['US_10Y'] = raw.xs('^TNX', axis=1, level=1)['Close']
        df['JPY_10Y'] = raw.xs('^JGBSY', axis=1, level=1)['Close']
    
    return df.dropna(subset=['Gold', 'DXY']) # Đảm bảo có dữ liệu chính

try:
    df = get_full_data()
    if not df.empty:
        # Tính toán các chỉ số
        last_gold = df['Gold'].iloc[-1]
        last_dxy = df['DXY'].iloc[-1]
        last_us10y = df['US_10Y'].iloc[-1]
        last_jpy10y = df['JPY_10Y'].iloc[-1]

        # 3. Hiển thị Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Vàng", f"${last_gold:,.1f}")
        m2.metric("DXY", f"{last_dxy:.2f}")
        m3.metric("LS Mỹ 10Y", f"{last_us10y:.2f}%")
        m4.metric("LS Nhật 10Y", f"{last_jpy10y:.3f}%")

        # 4. Phân tích lãi suất tự động
        st.subheader("🤖 Phân Tích Chênh Lệch Lãi Suất (Yield Spread)")
        spread = last_us10y - last_jpy10y
        
        c1, c2 = st.columns(2)
        with c1:
            if spread > 3:
                st.warning(f"Chênh lệch LS Mỹ-Nhật rất lớn ({spread:.2f}%). Điều này gây áp lực giảm giá cực mạnh lên đồng Yên (JPY) và hỗ trợ DXY.")
            else:
                st.info(f"Chênh lệch LS Mỹ-Nhật đang ở mức {spread:.2f}%.")
        
        with c2:
            st.markdown("""
            **Ghi chú VND:** Lãi suất Việt Nam (VND) hiện không có Ticker trực tiếp trên Yahoo. 
            Tuy nhiên, khi LS Mỹ (US10Y) tăng cao, áp lực tỷ giá lên VND sẽ tăng, buộc Ngân hàng Nhà nước phải hút tiền về hoặc tăng lãi suất để giữ giá đồng tiền.
            """)

        # 5. Biểu đồ đa tầng
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                            subplot_titles=("Giá Vàng", "Chỉ số DXY", "Lợi suất Trái phiếu (Lãi suất thị trường)"))
        
        fig.add_trace(go.Scatter(x=df.index, y=df['Gold'], name="Vàng", line=dict(color='#FFD700')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['DXY'], name="DXY", line=dict(color='#00CCFF')), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['US_10Y'], name="LS Mỹ 10Y (%)", line=dict(color='#FF4B4B')), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['JPY_10Y'], name="LS Nhật 10Y (%)", line=dict(color='#00FF00')), row=3, col=1)

        fig.update_layout(height=900, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi: {e}")
