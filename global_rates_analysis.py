import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Cấu hình trang
st.set_page_config(page_title="Macro History & Forecast", layout="wide")
st.title("🧠 Hệ Thống Phân Tích & Dự Báo Vĩ Mô 50 Năm")

# Hàm tải dữ liệu an toàn từ FRED
@st.cache_data(ttl=3600)
def fetch_fred_csv(series_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        data = pd.read_csv(url, index_col=0, parse_dates=True, na_values='.')
        return data if not data.empty else pd.DataFrame()
    except:
        return pd.DataFrame()

# Danh mục mã lãi suất
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

historical_events = [
    {"date": "1980-01-01", "label": "Đỉnh lãi suất Volcker", "color": "#FFA500"},
    {"date": "1987-10-19", "label": "Black Monday", "color": "#FF4B4B"},
    {"date": "2008-09-15", "label": "Khủng hoảng Lehman", "color": "#FF4B4B"},
    {"date": "2020-03-01", "label": "Đại dịch COVID-19", "color": "#00FFCC"},
    {"date": "2022-03-16", "label": "Chu kỳ thắt chặt FED", "color": "#FFA500"}
]

# --- SIDEBAR ---
st.sidebar.header("⚙️ Cấu hình")
term_choice = st.sidebar.radio("Kỳ hạn lãi suất:", list(mapping.keys()))
time_period = st.sidebar.select_slider("Khoảng thời gian:", options=["1Y", "5Y", "10Y", "20Y", "30Y", "50Y"], value="50Y")
show_events = st.sidebar.checkbox("Hiện sự kiện lịch sử", value=True)

try:
    with st.spinner('📡 Đang trích xuất dữ liệu vĩ mô...'):
        current_symbols = mapping[term_choice]
        data_frames = []
        for name, sid in current_symbols.items():
            df_temp = fetch_fred_csv(sid)
            if not df_temp.empty:
                df_temp.columns = [name]
                data_frames.append(df_temp)
        
        df_final = pd.concat(data_frames, axis=1).ffill().dropna().last(time_period)

    if not df_final.empty:
        selected_currencies = st.sidebar.multiselect(
            "Đồng tiền hiển thị:", options=df_final.columns.tolist(),
            default=[c for c in ["USD (Mỹ)", "EUR (Châu Âu)"] if c in df_final.columns]
        )

        # --- SECTION 1: BIỂU ĐỒ CHÍNH ---
        st.subheader(f"📊 Lịch sử Lãi suất {term_choice} ({time_period})")
        fig = go.Figure()
        for col in selected_currencies:
            fig.add_trace(go.Scatter(x=df_final.index, y=df_final[col], name=col, line=dict(width=1.5)))

        if show_events:
            for event in historical_events:
                e_date = pd.to_datetime(event["date"])
                if e_date >= df_final.index[0]:
                    fig.add_vline(x=e_date, line_width=1, line_dash="dash", line_color=event["color"])

        fig.update_layout(height=600, template="plotly_dark", hovermode="x unified",
                          yaxis=dict(title="Lãi suất (%)", gridcolor='rgba(255,255,255,0.1)'),
                          xaxis=dict(rangeslider=dict(visible=True)))
        st.plotly_chart(fig, use_container_width=True)

        # --- SECTION 2: PHÂN TÍCH THÔNG MINH & DỰ BÁO ---
        st.divider()
        st.subheader("🤖 Phân Tích & Dự Báo Thông Minh")
        
        # Chọn đồng tiền trọng tâm để dự báo
        focus_cur = st.selectbox("Chọn đồng tiền để nhận định:", options=selected_currencies if selected_currencies else df_final.columns.tolist())
        
        current_val = df_final[focus_cur].iloc[-1]
        hist_mean = df_final[focus_cur].mean()
        hist_max = df_final[focus_cur].max()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Giá trị hiện tại", f"{current_val:.2f}%")
        c2.metric("Trung bình lịch sử", f"{hist_mean:.2f}%")
        c3.metric("Đỉnh lịch sử", f"{hist_max:.2f}%")

        # Logic Nhận định
        st.info(f"**Nhận định cho {focus_cur}:**")
        if current_val > hist_mean + 1.5:
            st.warning(f"⚠️ Lãi suất hiện tại đang cao hơn đáng kể so với trung bình lịch sử ({hist_mean:.2f}%). Theo quy luật 'Mean Reversion', áp lực giảm lãi suất trong trung hạn là rất lớn khi lạm phát được kiểm soát.")
        elif current_val < hist_mean - 1.5:
            st.success(f"🟢 Lãi suất đang ở vùng thấp lịch sử. Điều này hỗ trợ cực tốt cho các kênh tài sản rủi ro (Chứng khoán, Bất động sản), nhưng cần cảnh giác với rủi ro lạm phát quay trở lại.")
        else:
            st.write(f"🔄 Lãi suất đang dao động quanh mức trung bình dài hạn. Thị trường đang ở trạng thái cân bằng vĩ mô.")

    else:
        st.error("Không có dữ liệu khả dụng.")

except Exception as e:
    st.error(f"Lỗi vận hành: {e}")
