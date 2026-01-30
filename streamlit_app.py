import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

st.set_page_config(page_title="Macro Gold Dashboard", layout="wide")

st.title("📊 Hệ Thống Giám Sát Tài Chính")

@st.cache_data(ttl=3600)
def get_clean_data():
    tickers = ['GC=F', 'SI=F', 'DX-Y.NYB']
    # Lấy dữ liệu 1 năm gần nhất để đảm bảo luôn có dữ liệu
    raw_data = yf.download(tickers, period="1y", auto_adjust=True)
    
    if raw_data.empty:
        return pd.DataFrame()

    df = pd.DataFrame()
    # Cách lấy dữ liệu an toàn cho Multi-index
    try:
        df['Gold'] = raw_data['Close']['GC=F']
        df['Silver'] = raw_data['Close']['SI=F']
        df['DXY'] = raw_data['Close']['DX-Y.NYB']
    except:
        # Dự phòng nếu format Yahoo thay đổi
        for t in tickers:
            col_name = 'Gold' if 'GC' in t else ('Silver' if 'SI' in t else 'DXY')
            df[col_name] = raw_data.xs(t, axis=1, level=1)['Close']
            
    return df.dropna()

try:
    df = get_clean_data()
    
    if df.empty:
        st.warning("⚠️ Hiện tại không lấy được dữ liệu từ Yahoo Finance. Vui lòng thử lại sau vài phút.")
    else:
        df['Ratio'] = df['Gold'] / df['Silver']
        
        # Kiểm tra độ dài dữ liệu trước khi dùng iloc
        if len(df) > 0:
            last_gold = df['Gold'].iloc[-1]
            last_dxy = df['DXY'].iloc[-1]
            last_ratio = df['Ratio'].iloc[-1]

            c1, c2, c3 = st.columns(3)
            c1.metric("Vàng (USD/oz)", f"${last_gold:,.2f}")
            c2.metric("Chỉ số DXY", f"{last_dxy:.2f}")
            c3.metric("Tỷ giá Vàng/Bạc", f"{last_ratio:.1f}")

            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)
            fig.add_trace(go.Scatter(x=df.index, y=df['Gold'], name="Vàng", line=dict(color='#FFD700')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['DXY'], name="DXY", fill='tozeroy', line=dict(color='#00CCFF')), row=2, col=1)
            
            fig.update_layout(height=600, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Dữ liệu sau khi xử lý bị trống.")

except Exception as e:
    st.error(f"Lỗi hệ thống: {e}")
