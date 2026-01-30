import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# 1. Cấu hình trang web
st.set_page_config(page_title="Macro AI Dashboard", layout="wide")
st.title("📊 Hệ Thống Giám Sát & Phân Tích Tương Quan")
st.markdown("---")

# 2. Hàm tải dữ liệu an toàn
@st.cache_data(ttl=3600)
def get_data():
    tickers = ['GC=F', 'SI=F', 'DX-Y.NYB']
    raw = yf.download(tickers, period="2y", auto_adjust=True)
    if raw.empty: return pd.DataFrame()
    
    df = pd.DataFrame(index=raw.index)
    try:
        # Xử lý Multi-index của Yahoo Finance
        df['Gold'] = raw['Close']['GC=F']
        df['Silver'] = raw['Close']['SI=F']
        df['DXY'] = raw['Close']['DX-Y.NYB']
    except:
        try:
            df['Gold'] = raw.xs('GC=F', axis=1, level=1)['Close']
            df['Silver'] = raw.xs('SI=F', axis=1, level=1)['Close']
            df['DXY'] = raw.xs('DX-Y.NYB', axis=1, level=1)['Close']
        except:
            pass
    return df.ffill().dropna()

try:
    df = get_data()
    if not df.empty:
        # Tính toán các chỉ số cần thiết
        df['Ratio'] = df['Gold'] / df['Silver']
        last_gold = df['Gold'].iloc[-1]
        prev_gold = df['Gold'].iloc[-2]
        last_dxy = df['DXY'].iloc[-1]
        prev_dxy = df['DXY'].iloc[-2]
        last_date = df.index[-1].strftime('%d/%m/%Y')

        st.write(f"Dữ liệu cập nhật ngày: **{last_date}**")

        # 3. Hiển thị Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Vàng (USD/oz)", f"${last_gold:,.2f}", f"{last_gold - prev_gold:,.2f}")
        c2.metric("Chỉ số DXY", f"{last_dxy:.2f}", f"{last_dxy - prev_dxy:.2f}")
        c3.metric("Tỷ lệ Vàng/Bạc", f"{df['Ratio'].iloc[-1]:.1f}")

        # 4. VẼ BIỂU ĐỒ TƯƠNG QUAN (SỬA LỖI SYNTAX)
        fig = go.Figure()

        # Thêm Vàng (Trục trái)
        fig.add_trace(go.Scatter(
            x=df.index, 
            y=df['Gold'], 
            name="Vàng (USD/oz)",
            line=dict(color='#FFD700', width=2.5)
        ))

        # Thêm Bạc (Trục trái)
        fig.add_trace(go.Scatter(
            x=df.index, 
            y=df['Silver'], 
            name="Bạc (USD/oz)",
            line=dict(color='#C0C0C0', width=1.5)
        ))

        # Thêm DXY (Trục phải - Secondary Axis)
        fig.add_trace(go.Scatter(
            x=df.index, 
            y=df['DXY'], 
            name="Chỉ số DXY (Trục Phải)",
            line=dict(color='#00CCFF', width=2),
            yaxis="y2"
        ))

        # Cấu hình Layout chuẩn
        fig.update_layout(
            height=700,
            template="plotly_dark",
            hovermode="x unified",
            title=dict(text="Tương Quan Biến Động: Vàng - Bạc - DXY"),
            # Trục Y trái (Vàng/Bạc)
            yaxis=dict(
                title=dict(text="Giá Vàng & Bạc (USD/oz)", font=dict(color="#FFD700")),
                tickfont=dict(color="#FFD700"),
                gridcolor="rgba(255, 255, 255, 0.1)"
            ),
            # Trục Y phải (DXY)
            yaxis2=dict(
                title=dict(text="Chỉ số DXY", font=dict(color="#00CCFF")),
                tickfont=dict(color="#00CCFF"),
                overlaying="y",
                side="right",
                showgrid=False
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)

        # 5. Khu vực dữ liệu
        with st.expander("📥 Xem bảng số liệu chi tiết"):
            st.dataframe(df.sort_index(ascending=False), use_container_width=True)

    else:
        st.error("⚠️ Không thể tải dữ liệu. Hãy kiểm tra kết nối Yahoo Finance.")

except Exception as e:
    st.error(f"Lỗi hệ thống: {str(e)}")
