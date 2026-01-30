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

        # --- 🤖 5. HỆ THỐNG PHÂN TÍCH & CẢNH BÁO TỰ ĐỘNG ---
        st.subheader("🤖 Trạm Phân Tích & Cảnh Báo Chiến Thuật")
        
        col_alert1, col_alert2 = st.columns(2)
        
        with col_alert1:
            st.markdown("#### ⚡ Tương quan Vĩ mô (Gold vs DXY)")
            gold_delta = curr['Gold'] - prev['Gold']
            dxy_delta = curr['DXY'] - prev['DXY']
            
            if gold_delta > 0 and dxy_delta < 0:
                st.success("✅ **Tương quan Thuận:** Vàng tăng do USD yếu đi. Đây là tín hiệu tăng trưởng bền vững.")
            elif gold_delta < 0 and dxy_delta > 0:
                st.warning("📉 **Áp lực tỷ giá:** USD mạnh lên đang ép giá Vàng giảm xuống.")
            elif gold_delta > 0 and dxy_delta > 0:
                st.error("🚨 **CẢNH BÁO BẤT THƯỜNG:** Cả Vàng và USD cùng tăng. Thị trường đang cực kỳ hoảng loạn, dòng tiền tìm nơi trú ẩn an toàn tuyệt đối!")
            else:
                st.info("🔄 **Thị trường tích lũy:** Chưa có xu hướng rõ ràng giữa Vàng và DXY.")

        with col_alert2:
            st.markdown("#### 🔍 Tín hiệu Kim loại (Gold/Silver Ratio)")
            ratio = curr['Ratio']
            if ratio > 85:
                st.error(f"🔴 **Tín hiệu Bạc Rẻ:** Tỷ lệ ({ratio:.1f}) đang ở mức cao lịch sử. Ưu tiên tích lũy Bạc hơn Vàng.")
            elif ratio < 65:
                st.warning(f"⚠️ **Tín hiệu Bạc Đắt:** Tỷ lệ ({ratio:.1f}) thấp. Bạc đã tăng quá nóng, cân nhắc chốt lời chuyển sang Vàng.")
            else:
                st.success(f"🟢 **Tỷ lệ ổn định:** Tỷ lệ ({ratio:.1f}) nằm trong vùng trung bình, phù hợp nắm giữ cả hai.")

        # 4. VẼ BIỂU ĐỒ (Giữ nguyên cấu hình trục kép của bạn)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Gold'], name="Vàng", line=dict(color='#FFD700', width=2.5)))
        fig.add_trace(go.Scatter(x=df.index, y=df['Silver'], name="Bạc (Trục Phải)", line=dict(color='#C0C0C0', width=1.5), yaxis="y2"))
        fig.add_trace(go.Scatter(x=df.index, y=df['DXY'], name="DXY (Trục Phải)", line=dict(color='#00CCFF', width=2), yaxis="y2"))

        fig.update_layout(
            height=600, template="plotly_dark", hovermode="x unified",
            yaxis=dict(title="Giá Vàng (USD/oz)", titlefont=dict(color="#FFD700"), tickfont=dict(color="#FFD700")),
            yaxis2=dict(title="Bạc & DXY", overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", y=1.05, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig, use_container_width=True)

        # 6. Khu vực dữ liệu
        with st.expander("📥 Xem bảng số liệu chi tiết"):
            st.dataframe(df.sort_index(ascending=False), use_container_width=True)

    else:
        st.error("⚠️ Không thể tải dữ liệu.")
except Exception as e:
    st.error(f"Lỗi hệ thống: {str(e)}")
