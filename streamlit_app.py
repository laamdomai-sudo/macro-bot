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
import pandas as pd

st.set_page_config(page_title="Interest Rate Correlation", layout="wide")
st.title("📊 Biểu Đồ Tương Quan Lãi Suất Toàn Cầu (USD - JPY - VND)")

@st.cache_data(ttl=3600)
def get_macro_data():
    # Tickers: LS Mỹ 10Y, LS Nhật 10Y, Tỷ giá USDVND
    tickers = ['^TNX', '^JGBSY', 'USDVND=X']
    raw = yf.download(tickers, period="2y", auto_adjust=True)
    
    if raw.empty: return pd.DataFrame()

    df = pd.DataFrame(index=raw.index)
    try:
        df['US_10Y'] = raw.xs('^TNX', axis=1, level=1)['Close']
        df['JPY_10Y'] = raw.xs('^JGBSY', axis=1, level=1)['Close']
        df['USDVND'] = raw.xs('USDVND=X', axis=1, level=1)['Close']
    except:
        df['US_10Y'] = raw['Close']['^TNX']
        df['JPY_10Y'] = raw['Close']['^JGBSY']
        df['USDVND'] = raw['Close']['USDVND=X']
    
    return df.ffill().dropna()

try:
    df = get_macro_data()
    
    if not df.empty:
        # 1. Tạo biểu đồ với 2 trục Y
        fig = go.Figure()

        # Thêm Lãi suất Mỹ (Trục trái)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['US_10Y'],
            name="Lãi suất Mỹ 10Y (%)",
            line=dict(color='#FF4B4B', width=3)
        ))

        # Thêm Lãi suất Nhật (Trục trái)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['JPY_10Y'],
            name="Lãi suất Nhật 10Y (%)",
            line=dict(color='#00FF00', width=3)
        ))

        # Thêm Tỷ giá VND (Trục phải - Secondary Y)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['USDVND'],
            name="Tỷ giá USD/VND (Trục phải)",
            line=dict(color='#FF00FF', width=2, dash='dot'),
            yaxis="y2"
        ))

        # 2. Thiết lập bố cục trục kép
        fig.update_layout(
            height=700,
            template="plotly_dark",
            hovermode="x unified",
            title="Sự tương quan giữa Lãi suất (Mỹ-Nhật) và Tỷ giá VND",
            yaxis=dict(
                title="Lãi suất (%)",
                titlefont=dict(color="#FF4B4B"),
                tickfont=dict(color="#FF4B4B")
            ),
            yaxis2=dict(
                title="Tỷ giá USD/VND",
                titlefont=dict(color="#FF00FF"),
                tickfont=dict(color="#FF00FF"),
                overlaying="y",
                side="right"
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)

        # 3. Phân tích tương quan
        st.subheader("🤖 Nhận định tương quan")
        curr = df.iloc[-1]
        spread = curr['US_10Y'] - curr['JPY_10Y']
        
        st.info(f"""
        - **Chênh lệch lãi suất (Spread):** Hiện tại là **{spread:.2f}%**. 
        - **Quan sát:** Khi đường màu Đỏ (Mỹ) và Xanh lá (Nhật) càng xa nhau, đường màu Hồng (VND) thường có xu hướng dốc lên do áp lực tỷ giá tăng cao. 
        - **Điểm đảo chiều:** Nếu khoảng cách Mỹ-Nhật thu hẹp, áp lực lên VND sẽ giảm bớt.
        """)
    else:
        st.error("Không có dữ liệu. Vui lòng kiểm tra lại kết nối.")

except Exception as e:
    st.error(f"Lỗi: {e}")
