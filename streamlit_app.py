import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# 1. Cấu hình trang web
st.set_page_config(page_title="Gold & DXY 50Y Analysis", layout="wide")
st.title("📊 Phân Tích Vàng & DXY (1976 - 2026) kèm MA200")
st.markdown("---")

# 2. Hàm tải dữ liệu lịch sử
@st.cache_data(ttl=3600)
def get_macro_data():
    tickers = ['GC=F', 'DX-Y.NYB']
    raw = yf.download(tickers, period="max", auto_adjust=True)
    if raw.empty: return pd.DataFrame()
    
    df = pd.DataFrame(index=raw.index)
    try:
        df['Gold'] = raw['Close']['GC=F']
        df['DXY'] = raw['Close']['DX-Y.NYB']
    except:
        df['Gold'] = raw.xs('GC=F', axis=1, level=1)['Close']
        df['DXY'] = raw.xs('DX-Y.NYB', axis=1, level=1)['Close']
    
    # Tính đường trung bình động 200 ngày (MA200) cho Vàng
    df['MA200_Gold'] = df['Gold'].rolling(window=200).mean()
    
    return df.ffill().dropna()

try:
    df = get_macro_data()
    if not df.empty:
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 3. Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Giá Vàng (USD/oz)", f"${curr['Gold']:,.1f}", f"{curr['Gold'] - prev['Gold']:,.1f}")
        c2.metric("MA200 Vàng", f"${curr['MA200_Gold']:,.1f}")
        c3.metric("Chỉ số DXY", f"{curr['DXY']:.2f}", f"{curr['DXY'] - prev['DXY']:.2f}")

        # --- 🤖 4. HỆ THỐNG PHÂN TÍCH TỰ ĐỘNG ---
        st.subheader("🤖 Trạm Phân Tích Chiến Thuật")
        
        col_a, col_b = st.columns(2)
        with col_a:
            # Phân tích tương quan Gold vs DXY
            if (curr['Gold'] - prev['Gold']) > 0 and (curr['DXY'] - prev['DXY']) < 0:
                st.success("✅ **Tương quan Nghịch chuẩn:** Vàng tăng khi DXY giảm.")
            elif (curr['Gold'] - prev['Gold']) > 0 and (curr['DXY'] - prev['DXY']) > 0:
                st.error("🚨 **Bất thường:** Cả Vàng và USD cùng tăng (Thị trường hoảng loạn).")
            else:
                st.info("🔄 **Thị trường tĩnh:** Chưa rõ xu hướng giữa Vàng và DXY.")

        with col_b:
            # Phân tích xu hướng dài hạn với MA200
            diff_ma200 = curr['Gold'] - curr['MA200_Gold']
            percent_above = (diff_ma200 / curr['MA200_Gold']) * 100
            
            if curr['Gold'] > curr['MA200_Gold']:
                st.success(f"📈 **Xu hướng Tăng (Bull):** Vàng đang nằm TRÊN MA200 khoảng {percent_above:.1f}%. Xu hướng dài hạn vẫn tích cực.")
            else:
                st.error(f"📉 **Xu hướng Giảm (Bear):** Vàng đang nằm DƯỚI MA200. Cần thận trọng với rủi ro sụt giảm dài hạn.")

        # --- 5. VẼ BIỂU ĐỒ VỚI MA200 VÀ RANGESLIDER ---
        fig = go.Figure()

        # Đường Vàng (Trục trái)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Gold'], 
            name="Giá Vàng", 
            line=dict(color='#FFD700', width=2)
        ))

        # Đường MA200 (Trục trái)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['MA200_Gold'], 
            name="MA200 (Xu hướng dài hạn)", 
            line=dict(color='#FF00FF', width=1.5, dash='dash') # Màu tím hồng đứt nét
        ))

        # Đường DXY (Trục phải)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['DXY'], 
            name="DXY (Trục Phải)", 
            yaxis="y2", 
            line=dict(color='#00CCFF', width=1.2)
        ))

        # Layout
        fig.update_layout(
            height=750, template="plotly_dark", hovermode="x unified",
            xaxis=dict(
                rangeslider=dict(visible=True),
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1Y", step="year", stepmode="backward"),
                        dict(count=10, label="10Y", step="year", stepmode="backward"),
                        dict(step="all", label="MAX")
                    ])
                ),
                type="date"
            ),
            yaxis=dict(title=dict(text="Giá Vàng (USD)", font=dict(color="#FFD700")), tickfont=dict(color="#FFD700")),
            yaxis2=dict(title=dict(text="DXY", font=dict(color="#00CCFF")), tickfont=dict(color="#00CCFF"), overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("⚠️ Không thể tải dữ liệu.")
except Exception as e:
    st.error(f"Lỗi: {str(e)}")
