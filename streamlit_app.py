import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# 1. Cấu hình trang web
st.set_page_config(page_title="Macro AI Dashboard", layout="wide")
st.title("📊 Hệ Thống Giám Sát & Phân Tích Tương Quan")
st.markdown("---")

# 2. Hàm tải dữ liệu
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
    return df.ffill().dropna()

try:
    df = get_data()
    if not df.empty:
        # Tính toán Ratio
        df['Ratio'] = df['Gold'] / df['Silver']
        
        # Lấy số liệu hiện tại
        curr = df.iloc[-1]
        prev = df.iloc[-2]

        # 3. Hiển thị Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Vàng (USD/oz)", f"${curr['Gold']:,.1f}", f"{curr['Gold'] - prev['Gold']:,.1f}")
        c2.metric("Bạc (USD/oz)", f"${curr['Silver']:,.2f}", f"{curr['Silver'] - prev['Silver']:,.2f}")
        c3.metric("Chỉ số DXY", f"{curr['DXY']:.2f}", f"{curr['DXY'] - prev['DXY']:.2f}")
        c4.metric("Tỷ lệ Vàng/Bạc", f"{curr['Ratio']:.1f}")

        # 4. VẼ BIỂU ĐỒ 3 CHỈ SỐ (ĐÃ SỬA LỖI HIỂN THỊ ĐƯỜNG BẠC)
        fig = go.Figure()

        # Đường Vàng - Trục trái (Y1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Gold'],
            name="Vàng (Trục Trái)",
            line=dict(color='#FFD700', width=2.5)
        ))

        # Đường Bạc - Chuyển sang Trục phải (Y2) để nhìn rõ hơn
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Silver'],
            name="Bạc (Trục Phải)",
            line=dict(color='#C0C0C0', width=2),
            yaxis="y2"
        ))

        # Đường DXY - Trục phải (Y2)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['DXY'],
            name="DXY (Trục Phải)",
            line=dict(color='#00CCFF', width=2),
            yaxis="y2"
        ))

        # Cấu hình Layout Trục kép
        fig.update_layout(
            height=700,
            template="plotly_dark",
            hovermode="x unified",
            title="Tương Quan Biến Động: Vàng - Bạc - DXY",
            yaxis=dict(
                title="Giá Vàng (USD/oz)",
                titlefont=dict(color="#FFD700"),
                tickfont=dict(color="#FFD700")
            ),
            yaxis2=dict(
                title="Giá Bạc & Chỉ số DXY",
                titlefont=dict(color="#00CCFF"),
                tickfont=dict(color="#00CCFF"),
                overlaying="y",
                side="right",
                showgrid=False # Tắt grid trục 2 để tránh rối mắt
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)

        # 5. Phân tích tự động
        st.info(f"💡 **Phân tích:** Hiện tại Bạc và DXY đang được hiển thị cùng thang đo bên phải (vùng ~100). Điều này giúp bạn so sánh trực tiếp xem khi DXY giảm thì Bạc có bùng nổ mạnh hơn Vàng hay không.")

except Exception as e:
    st.error(f"Lỗi: {e}")
