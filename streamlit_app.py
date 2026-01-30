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
    # Tickers: Vàng, Bạc, DXY
    tickers = ['GC=F', 'SI=F', 'DX-Y.NYB']
    raw = yf.download(tickers, period="2y", auto_adjust=True)
    if raw.empty: return pd.DataFrame()
    
    df = pd.DataFrame(index=raw.index)
    try:
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
        # Tính toán các chỉ số
        df['Ratio'] = df['Gold'] / df['Silver']
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        last_date = df.index[-1].strftime('%d/%m/%Y')

        st.write(f"Dữ liệu cập nhật ngày: **{last_date}**")

        # 3. Hiển thị Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Vàng (USD/oz)", f"${curr['Gold']:,.1f}", f"{curr['Gold'] - prev['Gold']:,.1f}")
        c2.metric("Bạc (USD/oz)", f"${curr['Silver']:,.2f}", f"{curr['Silver'] - prev['Silver']:,.2f}")
        c3.metric("Chỉ số DXY", f"{curr['DXY']:.2f}", f"{curr['DXY'] - prev['DXY']:.2f}")
        c4.metric("Tỷ lệ Vàng/Bạc", f"{curr['Ratio']:.1f}", f"{curr['Ratio'] - df['Ratio'].iloc[-2]:.2f}")

        # --- 🤖 4. HỆ THỐNG PHÂN TÍCH & CẢNH BÁO TỰ ĐỘNG ---
        st.subheader("🤖 Trạm Phân Tích & Cảnh Báo Chiến Thuật")
        col_alert1, col_alert2 = st.columns(2)
        
        with col_alert1:
            st.markdown("#### ⚡ Tương quan Vĩ mô (Gold vs DXY)")
            gold_move = curr['Gold'] - prev['Gold']
            dxy_move = curr['DXY'] - prev['DXY']
            
            if gold_move > 0 and dxy_move < 0:
                st.success("✅ **Tương quan Chuẩn:** Vàng tăng khi USD yếu. Tín hiệu tăng trưởng lành mạnh.")
            elif gold_move < 0 and dxy_move > 0:
                st.warning("📉 **Áp lực tỷ giá:** USD mạnh đang đè nặng lên giá Vàng.")
            elif gold_move > 0 and dxy_move > 0:
                st.error("🚨 **CẢNH BÁO:** Vàng & USD cùng tăng. Dòng tiền đang cực kỳ hoảng loạn tìm nơi trú ẩn!")
            else:
                st.info("🔄 **Thị trường tĩnh:** Chưa có xu hướng rõ ràng.")

        with col_alert2:
            st.markdown("#### 🔍 Tín hiệu Kim loại (Gold/Silver Ratio)")
            ratio = curr['Ratio']
            if ratio > 85:
                st.error(f"🔴 **Tín hiệu Bạc Rẻ:** Ratio ({ratio:.1f}) rất cao. Bạc đang bị định giá thấp hơn Vàng.")
            elif ratio < 65:
                st.warning(f"⚠️ **Tín hiệu Bạc Đắt:** Ratio ({ratio:.1f}) thấp. Cẩn thận nhịp điều chỉnh của Bạc.")
            else:
                st.success(f"🟢 **Vùng Trung Tính:** Tỷ lệ ({ratio:.1f}) đang ở mức cân bằng.")

        # --- 5. VẼ BIỂU ĐỒ TƯƠNG QUAN (Sửa lỗi titlefont) ---
        fig = go.Figure()

        # Vàng (Trục trái)
        fig.add_trace(go.Scatter(x=df.index, y=df['Gold'], name="Vàng", line=dict(color='#FFD700', width=2.5)))

        # Bạc & DXY (Trục phải để hiện rõ đường Bạc)
        fig.add_trace(go.Scatter(x=df.index, y=df['Silver'], name="Bạc (Trục Phải)", 
                                 line=dict(color='#C0C0C0', width=1.5), yaxis="y2"))
        fig.add_trace(go.Scatter(x=df.index, y=df['DXY'], name="DXY (Trục Phải)", 
                                 line=dict(color='#00CCFF', width=2), yaxis="y2"))

        fig.update_layout(
            height=700,
            template="plotly_dark",
            hovermode="x unified",
            title=dict(text="Tương Quan Biến Động Toàn Cầu"),
            yaxis=dict(
                title=dict(text="Giá Vàng (USD/oz)", font=dict(color="#FFD700")),
                tickfont=dict(color="#FFD700")
            ),
            yaxis2=dict(
                title=dict(text="Giá Bạc & Chỉ số DXY", font=dict(color="#00CCFF")),
                tickfont=dict(color="#00CCFF"),
                overlaying="y",
                side="right",
                showgrid=False
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📥 Xem bảng số liệu chi tiết"):
            st.dataframe(df.sort_index(ascending=False), use_container_width=True)

    else:
        st.error("⚠️ Không thể tải dữ liệu.")
except Exception as e:
    st.error(f"Lỗi hệ thống: {str(e)}")
