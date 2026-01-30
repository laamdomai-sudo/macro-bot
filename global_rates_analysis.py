import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Cấu hình trang
st.set_page_config(page_title="Macro History & Events", layout="wide")
st.title("🌍 Dashboard Lãi Suất & Sự Kiện Kinh Tế 50 Năm")

# Hàm tải dữ liệu an toàn
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

# Danh sách sự kiện lịch sử quan trọng
historical_events = [
    {"date": "1980-01-01", "label": "Lãi suất Mỹ đạt đỉnh (Volcker Era)", "color": "orange"},
    {"date": "1987-10-19", "label": "Black Monday", "color": "red"},
    {"date": "2000-03-10", "label": "Bong bóng Dot-com", "color": "red"},
    {"date": "2008-09-15", "label": "Lehman Brothers Phá sản", "color": "red"},
    {"date": "2020-03-01", "label": "Đại dịch COVID-19", "color": "green"},
    {"date": "2022-03-16", "label": "FED bắt đầu chu kỳ tăng lãi suất", "color": "orange"}
]

# --- SIDEBAR ---
st.sidebar.header("⚙️ Cấu hình")
term_choice = st.sidebar.radio("Kỳ hạn lãi suất:", list(mapping.keys()))
time_period =
