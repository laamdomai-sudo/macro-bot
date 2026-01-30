import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# --- 1. CẤU HÌNH & HÀM XỬ LÝ DỮ LIỆU ---
st.set_page_config(page_title="Pro Quant Gold Analysis", layout="wide")
st.title("🧠 AI Quant: Hệ Thống Phân Tích & Dự Báo Vàng Chuyên Sâu")

@st.cache_data(ttl=3600)
def get_advanced_data():
    # Tải dữ liệu
    raw = yf.download(['GC=F', 'DX-Y.NYB'], period="2y", auto_adjust=True) # Lấy 2 năm để nhẹ hơn
    df = pd.DataFrame(index=raw.index)
    
    try:
        df['Gold'] = raw['Close']['GC=F']
        df['DXY'] = raw['Close']['DX-Y.NYB']
    except:
        df['Gold'] = raw.xs('GC=F', axis=1, level=1)['Close']
        df['DXY'] = raw.xs('DX-Y.NYB', axis=1, level=1)['Close']
    
    # 1. Trend Indicators
    df['MA50'] = df['Gold'].rolling(window=50).mean()
    df['MA200'] = df['Gold'].rolling(window=200).mean()
    
    # 2. Momentum Indicators (RSI)
    delta = df['Gold'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 3. Macro Correlation (30 days rolling)
    df['Corr_30d'] = df['Gold'].rolling(window=30).corr(df['DXY'])
    
    # 4. Volatility & Deviation (Z-Score)
    # Đo xem giá hiện tại lệch bao nhiêu độ lệch chuẩn so với MA50
    std_50 = df['Gold'].rolling(window=50).std()
    df['Z_Score'] = (df['Gold'] - df['MA50']) / std_50
    
    return df.ffill().dropna()

# --- 2. LOGIC PHÂN TÍCH TỰ ĐỘNG (THE BRAIN) ---
def analyze_market_context(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    score = 0
    reasons = []
    
    # --- A. Đánh giá Xu Hướng (Trend) ---
    if last['Gold'] > last['MA200']:
        score += 2
        trend_status = "Tăng dài hạn (Bullish)"
        if last['Gold'] > last['MA50']:
            score += 1
            reasons.append("✅ Giá nằm trên cả MA50 & MA200 (Xu hướng khỏe).")
        else:
            reasons.append("⚠️ Giá trên MA200 nhưng dưới MA50 (Điều chỉnh ngắn hạn).")
    else:
        score -= 2
        trend_status = "Giảm dài hạn (Bearish)"
        reasons.append("🔻 Giá nằm dưới MA200 (Xu hướng yếu).")

    # --- B. Đánh giá Động Lượng (RSI) ---
    if last['RSI'] > 75:
        score -= 1.5 # Trừ điểm vì rủi ro đảo chiều cao
        reasons.append("⚠️ RSI > 75: Vùng Quá Mua cực đại (Rủi ro điều chỉnh cao).")
    elif last['RSI'] < 30:
        score += 1.5 # Cộng điểm bắt đáy
        reasons.append("💎 RSI < 30: Vùng Quá Bán (Cơ hội phục hồi kỹ thuật).")
    elif 45 <= last['RSI'] <= 60 and last['Gold'] > last['MA50']:
        score += 1
        reasons.append("✅ RSI ổn định trong xu hướng tăng (Còn dư địa tăng).")

    # --- C. Đánh giá Vĩ Mô (DXY Correlation) ---
    # Nếu DXY giảm và Tương quan là nghịch đảo (-1) -> Tốt cho Vàng
    dxy_change = last['DXY'] - df['DXY'].iloc[-5] # Thay đổi DXY trong 1 tuần
    
    if last['Corr_30d'] < -0.5: # Tương quan nghịch chuẩn
        if dxy_change < 0:
            score += 1.5
            reasons.append("💵 USD suy yếu đang hỗ trợ trực tiếp giá Vàng.")
        else:
            score -= 1
            reasons.append("💵 USD đang hồi phục gây áp lực lên Vàng.")
    elif last['Corr_30d'] > 0.5: # Tương quan thuận (Bất thường)
        reasons.append("❗ Cảnh báo: Vàng & USD cùng chiều (Rủi ro địa chính trị hoặc dòng tiền trú ẩn).")

    # --- D. Đánh giá Biến động (Z-Score) ---
    if last['Z_Score'] > 2:
        score -= 1
        reasons.append("⚠️ Giá tăng quá nóng so với trung bình 50 phiên (Cẩn thận Bull trap).")
    elif last['Z_Score'] < -2:
        score += 1
        reasons.append("✅ Giá giảm quá sâu so với trung bình (Vùng mua hoảng loạn).")

    # --- TỔNG HỢP ---
    sentiment = "TRUNG TÍNH"
    color = "blue"
    if score >= 3: 
        sentiment = "TÍCH CỰC (MUA)"
        color = "green"
    elif score <= -2: 
        sentiment = "TIÊU CỰC (BÁN/CANH SHORT)"
        color = "red"
        
    return sentiment, color, score, reasons, trend_status

# --- 3. GIAO DIỆN STREAMLIT ---
try:
    df = get_advanced_data()
    curr_price = df['Gold'].iloc[-1]
    
    # Lấy kết quả phân tích
    sentiment, color, score, reasons, trend_status = analyze_market_context(df)

    # HEADER INFO
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Giá Vàng (USD)", f"${curr_price:,.2f}", f"{df['Gold'].iloc[-1] - df['Gold'].iloc[-2]:.2f}")
    c2.metric("RSI (14)", f"{df['RSI'].iloc[-1]:.1f}")
    c3.metric("DXY Index", f"{df['DXY'].iloc[-1]:.2f}", f"{df['DXY'].iloc[-1] - df['DXY'].iloc[-2]:.2f}")
    c4.metric("Điểm Tín Hiệu (Max 5)", f"{score:.1f}/5.0")

    st.divider()

    # --- SECTION: BÁO CÁO PHÂN TÍCH THÔNG MINH ---
    st.subheader("🤖 AI Smart Report: Đánh Giá & Dự Báo")
    
    col_analysis, col_chart = st.columns([1, 2])
    
    with col_analysis:
        # Hộp thông báo kết luận chính
        st.markdown(f"""
        <div style="padding: 20px; border-radius: 10px; background-color: {'rgba(0,255,0,0.1)' if color=='green' else 'rgba(255,0,0,0.1)' if color=='red' else 'rgba(0,0,255,0.1)'}; border: 1px solid {color};">
            <h3 style="color:{color}; margin:0;">KẾT LUẬN: {sentiment}</h3>
            <p style="margin-top:10px;"><strong>Xu hướng chính:</strong> {trend_status}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        st.write("#### 📝 Luận điểm chi tiết:")
        for reason in reasons:
            st.write(reason)
            
        st.info("💡 **Gợi ý hành động:** " + 
                ("Canh mua khi giá điều chỉnh nhẹ." if score > 3 else 
                 "Cân nhắc chốt lời từng phần." if score < -2 else 
                 "Quan sát, chờ tín hiệu rõ ràng hơn."))

    with col_chart:
        # Biểu đồ nâng cao với Bollinger Bands (giả lập bằng MA50 +- 2std)
        fig = go.Figure()
        
        # Giá Vàng
        fig.add_trace(go.Scatter(x=df.index, y=df['Gold'], name="Gold", line=dict(color='#FFD700', width=2)))
        
        # MA Trends
        fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], name="MA50 (Ngắn hạn)", line=dict(color='cyan', width=1)))
        fig.add_trace(go.Scatter(x=df.index, y=df['MA200'], name="MA200 (Dài hạn)", line=dict(color='magenta', width=1, dash='dash')))
        
        # Đánh dấu vùng mua/bán
        last_date = df.index[-1]
        if sentiment == "TÍCH CỰC (MUA)":
            fig.add_annotation(x=last_date, y=curr_price, text="BUY ZONE", showarrow=True, arrowhead=1, ax=0, ay=-40, bgcolor="green")
        elif sentiment == "TIÊU CỰC (BÁN/CANH SHORT)":
            fig.add_annotation(x=last_date, y=curr_price, text="SELL ZONE", showarrow=True, arrowhead=1, ax=0, ay=40, bgcolor="red")

        fig.update_layout(
            height=450, template="plotly_dark", 
            title="Biểu đồ phân tích kỹ thuật (Gold vs MA)",
            xaxis_title="", yaxis_title="Price ($)",
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- SECTION: DỮ LIỆU TƯƠNG QUAN CHI TIẾT ---
    st.divider()
    st.subheader("📊 Bảng Chỉ Số Sức Mạnh & Dòng Tiền")
    
    # Tạo dataframe hiển thị đẹp
    display_df = df[['Gold', 'DXY', 'RSI', 'Z_Score', 'Corr_30d']].tail(10).sort_index(ascending=False)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "Gold": st.column_config.NumberColumn("Giá Vàng", format="$%.2f"),
            "DXY": st.column_config.NumberColumn("DXY Index", format="%.2f"),
            "RSI": st.column_config.ProgressColumn("RSI Trend", min_value=0, max_value=100, format="%.1f"),
            "Z_Score": st.column_config.NumberColumn("Độ lệch (Z)", format="%.2f", help=">2: Quá nóng, <-2: Quá lạnh"),
            "Corr_30d": st.column_config.LineChartColumn("Tương quan (30d)", y_min=-1, y_max=1)
        }
    )

except Exception as e:
    st.error(f"Lỗi hệ thống: {str(e)}")
