import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# 1. Cấu hình trang web
st.set_page_config(page_title="Gold & DXY 50Y Analysis", layout="wide")
st.title("📊 Phân Tích Tương Quan Vàng & DXY (1976 - 2026)")
st.markdown("---")

# 2. Hàm tải dữ liệu lịch sử
@st.cache_data(ttl=3600)
def get_macro_data():
    # GC=F: Vàng, DX-Y.NYB: Chỉ số Đồng Đô la (DXY)
    tickers = ['GC=F', 'DX-Y.NYB']
    raw = yf.download(tickers, period="max", auto_adjust=True)
    if raw.empty: return pd.DataFrame()
    
    df = pd.DataFrame(index=raw.index)
    try:
        df['Gold'] = raw['Close']['GC=F']
        df['DXY'] = raw['Close']['DX-Y.NYB']
    except:
        # Xử lý trường hợp Multi-index của Yahoo Finance
        df['Gold'] = raw.xs('GC=F', axis=1, level=1)['Close']
        df['DXY'] = raw.xs('DX-Y.NYB', axis=1, level=1)['Close']
    
    return df.ffill().dropna()

try:
    df = get_macro_data()
    if not df.empty:
        # Lấy số liệu hiện tại và phiên trước
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        last_date = df.index[-1].strftime('%d/%m/%Y')

        # 3. Hiển thị Metrics
        st.write(f"Dữ liệu cập nhật ngày: **{last_date}**")
        c1, c2 = st.columns(2)
        c1.metric("Giá Vàng (USD/oz)", f"${curr['Gold']:,.1f}", f"{curr['Gold'] - prev['Gold']:,.1f}")
        c2.metric("Chỉ số DXY", f"{curr['DXY']:.2f}", f"{curr['DXY'] - prev['DXY']:.2f}")

        # --- 🤖 4. HỆ THỐNG PHÂN TÍCH TỰ ĐỘNG ---
        st.subheader("🤖 Trạm Phân Tích Chiến Thuật")
        
        # Tính toán biến động
        gold_diff = curr['Gold'] - prev['Gold']
        dxy_diff = curr['DXY'] - prev['DXY']
        
        col_a, col_b = st.columns(2)
        with col_a:
            if gold_diff > 0 and dxy_diff < 0:
                st.success("✅ **Tương quan Nghịch chuẩn:** Vàng tăng khi DXY giảm. Đây là động lực tăng trưởng bền vững.")
            elif gold_diff < 0 and dxy_diff > 0:
                st.warning("📉 **Áp lực từ USD:** DXY đang mạnh lên, gây sức ép khiến giá Vàng điều chỉnh.")
            elif gold_diff > 0 and dxy_diff > 0:
                st.error("🚨 **CẢNH BÁO BẤT THƯỜNG:** Cả Vàng và USD cùng tăng. Thị trường đang cực kỳ hoảng loạn, dòng tiền tìm nơi trú ẩn an toàn tuyệt đối!")
            else:
                st.info("🔄 **Thị trường tích lũy:** Biến động nhẹ, chưa xác lập xu hướng rõ ràng.")

        with col_b:
            # Phân tích vị thế giá Vàng so với lịch sử 1 năm
            gold_1y_high = df['Gold'].last('365D').max()
            if curr['Gold'] >= gold_1y_high * 0.98:
                st.error("🔥 **Vùng Đỉnh:** Giá Vàng đang giao dịch sát mức cao nhất trong vòng 1 năm qua.")
            elif curr['Gold'] <= df['Gold'].last('365D').min() * 1.05:
                st.success("💎 **Vùng Đáy:** Giá Vàng đang ở vùng thấp tương đối trong vòng 1 năm qua.")
            else:
                st.info("📊 **Vùng Trung Dung:** Giá đang dao động ở giữa biên độ năm.")

        # --- 5. VẼ BIỂU ĐỒ VỚI THANH KÉO (RANGESLIDER) ---
        fig = go.Figure()

        # Đường Vàng (Trục trái)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Gold'], 
            name="Giá Vàng (Trục Trái)", 
            line=dict(color='#FFD700', width=2)
        ))

        # Đường DXY (Trục phải)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['DXY'], 
            name="Chỉ số DXY (Trục Phải)", 
            yaxis="y2", 
            line=dict(color='#00CCFF', width=1.5)
        ))

        # Cấu hình Layout, Trục kép và Thanh kéo
        fig.update_layout(
            height=700,
            template="plotly_dark",
            hovermode="x unified",
            xaxis=dict(
                rangeslider=dict(visible=True), # Thanh kéo thời gian
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1Y", step="year", stepmode="backward"),
                        dict(count=10, label="10Y", step="year", stepmode="backward"),
                        dict(count=30, label="30Y", step="year", stepmode="backward"),
                        dict(step="all", label="MAX")
                    ])
                ),
                type="date"
            ),
            yaxis=dict(
                title=dict(text="Giá Vàng (USD/oz)", font=dict(color="#FFD700")),
                tickfont=dict(color="#FFD700")
            ),
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

        # 6. Bảng dữ liệu chi tiết
        with st.expander("📥 Xem chi tiết dữ liệu lịch sử"):
            st.dataframe(df.sort_index(ascending=False), use_container_width=True)

    else:
        st.error("⚠️ Không thể tải dữ liệu từ Yahoo Finance.")
except Exception as e:
    st.error(f"Lỗi hệ thống: {str(e)}")
