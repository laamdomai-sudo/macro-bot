import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Cấu hình trang
st.set_page_config(page_title="Global Macro Pro", layout="wide")
st.title("🌍 Dashboard Lãi Suất Toàn Cầu: 2Y vs 10Y")

# Hàm tải dữ liệu an toàn
@st.cache_data(ttl=3600)
def fetch_fred_csv(series_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        data = pd.read_csv(url, index_col=0, parse_dates=True, na_values='.')
        return data if not data.empty else pd.DataFrame()
    except:
        return pd.DataFrame()

# 2. Định nghĩa danh mục mã lãi suất (Cả 2Y và 10Y)
mapping = {
    "10 Năm (Dài hạn)": {
        "USD (Mỹ)": "DGS10",
        "EUR (Châu Âu)": "IRLTLT01EZM156N",
        "JPY (Nhật Bản)": "IRLTLT01JPM156N",
        "GBP (Anh)": "IRLTLT01GBM156N",
        "CNY (Trung Quốc)": "CHNYLD10Y"
    },
    "2 Năm (Ngắn hạn)": {
        "USD (Mỹ)": "DGS2",
        "EUR (Châu Âu)": "IRT3TR01EZM156N",
        "JPY (Nhật Bản)": "IR3TIB01JPM156N",
        "GBP (Anh)": "IRT3TR01GBM156N",
        "CNY (Trung Quốc)": "CHNRYLD2Y"
    }
}

# --- SIDEBAR ---
st.sidebar.header("⚙️ Cấu hình hệ thống")
term_choice = st.sidebar.radio("Chọn kỳ hạn lãi suất:", list(mapping.keys()))
current_symbols = mapping[term_choice]

try:
    with st.spinner(f'📡 Đang tải lãi suất {term_choice}...'):
        data_frames = []
        for name, sid in current_symbols.items():
            df_temp = fetch_fred_csv(sid)
            if not df_temp.empty:
                df_temp.columns = [name]
                data_frames.append(df_temp)
        
        if data_frames:
            df_final = pd.concat(data_frames, axis=1).ffill().dropna().last('3Y')
        else:
            df_final = pd.DataFrame()

    if not df_final.empty:
        # Chọn đồng tiền hiển thị
        available_cols = df_final.columns.tolist()
        selected_currencies = st.sidebar.multiselect(
            "Chọn đồng tiền hiển thị:",
            options=available_cols,
            default=[c for c in ["USD (Mỹ)", "EUR (Châu Âu)"] if c in available_cols]
        )

        st.sidebar.divider()
        st.sidebar.header("⚖️ Phân tích Spread")
        base_cur = st.sidebar.selectbox("Đồng tiền A:", options=available_cols, index=0)
        target_cur = st.sidebar.selectbox("Đồng tiền B:", options=available_cols, index=min(2, len(available_cols)-1))

        # --- SECTION 1: BIỂU ĐỒ CHÍNH ---
        st.subheader(f"📊 Diễn biến Lãi suất {term_choice}")
        if selected_currencies:
            fig = go.Figure()
            for col in selected_currencies:
                fig.add_trace(go.Scatter(x=df_final.index, y=df_final[col], name=col, line=dict(width=2)))
            
            fig.update_layout(
                height=500, template="plotly_dark", hovermode="x unified",
                yaxis=dict(title="Lãi suất (%)", gridcolor='rgba(255,255,255,0.1)'),
                xaxis=dict(rangeslider=dict(visible=True)),
                legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- SECTION 2: BIỂU ĐỒ SPREAD ---
            st.divider()
            st.subheader(f"⚖️ Chênh lệch ({term_choice}): {base_cur} - {target_cur}")
            spread_data = df_final[base_cur] - df_final[target_cur]
            
            c1, c2 = st.columns([1, 3])
            c1.metric("Spread hiện tại", f"{spread_data.iloc[-1]:.2f}%", 
                      f"{spread_data.iloc[-1] - spread_data.iloc[-20]:.2f}% (Tháng)")
            
            with c2:
                fig_spread = go.Figure()
                fig_spread.add_trace(go.Scatter(x=spread_data.index, y=spread_data, fill='tozeroy', name="Spread", line=dict(color='#00FFCC')))
                fig_spread.update_layout(height=300, template="plotly_dark", margin=dict(t=10, b=10))
                st.plotly_chart(fig_spread, use_container_width=True)
            
            # --- KIẾN THỨC VĨ MÔ ---
            with st.expander("💡 Tại sao cần so sánh 2Y và 10Y?"):
                st.write("""
                * **Lãi suất 2 năm:** Phản ánh kỳ vọng về việc tăng/giảm lãi suất của Ngân hàng Trung ương trong tương lai gần.
                * **Lãi suất 10 năm:** Phản ánh sức khỏe kinh tế dài hạn. 
                * **Mẹo đầu tư:** Nếu lãi suất 2Y của một nước tăng nhanh hơn 10Y (Đường cong phẳng lại), đó thường là tín hiệu sắp có suy thoái hoặc thắt chặt tiền tệ cực mạnh.
                """)
        else:
            st.info("Vui lòng chọn đồng tiền hiển thị ở thanh bên.")
    else:
        st.error("Không có dữ liệu. Hãy thử kiểm tra lại kết nối internet.")

except Exception as e:
    st.error(f"Lỗi: {e}")
