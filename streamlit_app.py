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
    return df.dropna()

try:
    df = get_data()
    if not df.empty:
        # Tính toán các chỉ số
        df['Ratio'] = df['Gold'] / df['Silver']
        last_gold, prev_gold = df['Gold'].iloc[-1], df['Gold'].iloc[-2]
        last_silver, prev_silver = df['Silver'].iloc[-1], df['Silver'].iloc[-2]
        last_dxy, prev_dxy = df['DXY'].iloc[-1], df['DXY'].iloc[-2]
        last_ratio = df['Ratio'].iloc[-1]
        last_date = df.index[-1].strftime('%d/%m/%Y')

        st.write(f"Dữ liệu cập nhật ngày: **{last_date}**")

        # 3. Hiển thị Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Vàng (USD/oz)", f"${last_gold:,.2f}", f"{last_gold - prev_gold:,.2f}")
        c2.metric("Bạc (USD/oz)", f"${last_silver:,.2f}", f"{last_silver - prev_silver:,.2f}")
        c3.metric("Chỉ số DXY", f"{last_dxy:.2f}", f"{last_dxy - prev_dxy:.2f}")
        c4.metric("Tỷ lệ Vàng/Bạc", f"{last_ratio:.1f}")

        # --- 🤖 TRẠM PHÂN TÍCH ---
        st.subheader("🤖 Trạm Phân Tích Thông Minh")
        col_a, col_b = st.columns(2)
        with col_a:
            if last_ratio > 80: st.info(f"🔴 **Vàng/Bạc ({last_ratio:.1f}):** Ưu tiên tích lũy Bạc.")
            elif last_ratio < 50: st.warning(f"⚠️ **Vàng/Bạc ({last_ratio:.1f}):** Cẩn thận nhịp chốt lời Bạc.")
            else: st.success("🟢 Thị trường kim loại quý ổn định.")
        with col_b:
            if last_gold > prev_gold and last_dxy < prev_dxy: st.success("✅ **Tương quan Chuẩn:** Vàng tăng khi DXY giảm.")
            elif last_gold > prev_gold and last_dxy > prev_dxy: st.error("🚨 **Bất thường:** Cả Vàng và DXY cùng tăng (Thị trường hoảng loạn).")
            else: st.info("💤 Thị trường đang trong trạng thái tích lũy.")

        # 4. VẼ BIỂU ĐỒ TƯƠNG QUAN TRÊN CÙNG 1 KHUNG (TRỤC Y KÉP)
        fig = go.Figure()

        # Thêm Vàng (Trục trái)
        fig.add_trace(go.Scatter(x=df.index, y=df['Gold'], name="Vàng (Trục Trái)",
                                 line=dict(color='#FFD700', width=2.5)))

        # Thêm Bạc (Trục trái)
        fig.add_trace(go.Scatter(x=df.index, y=df['Silver'], name="Bạc (Trục Trái)",
                                 line=dict(color='#C0C0C0', width=1.5)))

        # Thêm DXY (Trục phải)
        fig.add_trace(go.Scatter(x=df.index, y=df['DXY'], name="Chỉ số DXY (Trục Phải)",
                                 line=dict(color='#00CCFF', width=2),
                                 yaxis="y2"))

        # Cấu hình Layout cho Trục Y kép
        fig.update_layout(
            height=700,
            template="plotly_dark",
            hovermode="x unified",
            title="Biểu đồ Tương quan: Vàng - Bạc - DXY",
            yaxis=dict(title="Giá Vàng & Bạc (USD/oz)", titlefont=dict(color="#FFD700"), tickfont=dict(color="#FFD700")),
            yaxis2=dict(title="Chỉ số DXY", titlefont=dict(color="#00CCFF"), tickfont=dict(color="#00CCFF"),
                        overlaying="y", side="right"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)

        # 5. Khu vực tải dữ liệu
        with st.expander("📥 Xem bảng dữ liệu chi tiết"):
            st.dataframe(df.sort_index(ascending=False), use_container_width=True)
            st.download_button("Tải file CSV", df.to_csv(), "macro_data.csv")
    
    else:
        st.error("⚠️ Không lấy được dữ liệu.")
except Exception as e:
    st.error(f"Lỗi hệ thống: {e}")

