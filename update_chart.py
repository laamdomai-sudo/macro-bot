import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def build_dashboard():
    # 1. Tải dữ liệu
    tickers = ['GC=F', 'SI=F', 'DX-Y.NYB']
    data = yf.download(tickers, start='1976-01-01', auto_adjust=True, progress=False)
    
    # Xử lý dữ liệu tránh lỗi Multi-index
    df = pd.DataFrame()
    df['Gold'] = data['Close']['GC=F']
    df['Silver'] = data['Close']['SI=F']
    df['DXY'] = data['Close']['DX-Y.NYB']
    df = df.dropna()
    df['Ratio'] = df['Gold'] / df['Silver']

    # 2. Vẽ Dashboard
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                        subplot_titles=("Giá Vàng & Bạc (USD/oz)", "Chỉ số DXY", "Tỷ lệ Vàng/Bạc"))

    fig.add_trace(go.Scatter(x=df.index, y=df['Gold'], name="Vàng", line=dict(color='#FFD700')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Silver'], name="Bạc", line=dict(color='#C0C0C0')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['DXY'], name="DXY", fill='tozeroy', line=dict(color='#1f77b4')), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Ratio'], name="Tỷ lệ", line=dict(color='#00ffcc')), row=3, col=1)

    fig.update_layout(height=1000, template="plotly_dark", title="HỆ THỐNG CẬP NHẬT TỰ ĐỘNG")
    
    # 3. Xuất file HTML
    fig.write_html("index.html")

if __name__ == "__main__":
    build_dashboard()
