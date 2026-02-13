import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from deep_translator import GoogleTranslator
import warnings

# 忽略警告訊息，保持介面乾淨
warnings.filterwarnings('ignore')

# ==========================================
# 1. 系統配置
# ==========================================
st.set_page_config(
    page_title="美股投資戰情室",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定義 CSS：優化介面與深色模式適配
st.markdown("""
<style>
    .main {padding: 0.5rem;}
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: bold;
    }
    /* 優化數據指標背景 */
    [data-testid="stMetric"] {
        background-color: #262730;
        padding: 10px;
        border-radius: 8px;
        border-left: 5px solid #FF4B4B;
    }
</style>
""", unsafe_allow_html=True)

# S&P 500 主要行業清單
SP500_SECTORS = {
    "XLK": "科技 Technology",
    "XLF": "金融 Financial",
    "XLV": "醫療 Healthcare",
    "XLY": "消費 Consumer",
    "XLC": "通訊 Communication",
    "XLI": "工業 Industrial",
    "XLP": "民生 Staples",
    "XLE": "能源 Energy",
    "XLRE": "房產 Real Estate",
    "XLB": "原料 Materials",
    "XLU": "公用 Utilities"
}

# 熱門個股預設清單
POPULAR_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", 
    "V", "JNJ", "WMT", "JPM", "MA", "DIS", "NFLX", "COST"
]

# ==========================================
# 2. 核心運算函式
# ==========================================

@st.cache_data(ttl=300)
def calculate_rsi(data, periods=14):
    """計算 RSI 強弱指標"""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_trend_signal(df):
    """判斷市場趨勢"""
    if len(df) < 60: return "數據不足"
    current = df['Close'].iloc[-1]
    ma20 = df['Close'].rolling(20).mean().iloc[-1]
    ma60 = df['Close'].rolling(60).mean().iloc[-1]
    
    if current > ma20 > ma60: return "🔥 強勢多頭"
    elif current < ma20 < ma60: return "❄️ 空頭修正"
    else: return "⚖️ 區間盤整"

@st.cache_data(ttl=300, show_spinner=False)
def fetch_stock_history(ticker, period="6mo"):
    """獲取股票歷史數據 (含防呆處理)"""
    try:
        ticker = ticker.strip().upper()
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty: return None
        return df
    except:
        return None

def get_stock_object(ticker):
    """獲取 Ticker 物件 (用於新聞與持股)"""
    return yf.Ticker(ticker)

# ==========================================
# 3. 繪圖函式 (Plotly 靜態美化版)
# ==========================================
def plot_candlestick(df, ticker):
    """
    使用 Plotly 繪製靜態 K 線圖
    優點：手機不誤觸、無亂碼、Y軸右置、美觀
    """
    # 確保資料足夠
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    df['RSI'] = calculate_rsi(df)

    # 建立畫布：3 列 (K線, 成交量, RSI)
    fig = make_subplots(
        rows=3, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.02, 
        row_heights=[0.6, 0.2, 0.2]
    )

    # --- 第 1 層：K 線圖 ---
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name='K線',
        increasing_line_color='#FF0000', # 台股紅漲
        decreasing_line_color='#008000', # 台股綠跌
        showlegend=True
    ), row=1, col=1)

    # 均線
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='MA20', line=dict(color='#4169E1', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], name='MA60', line=dict(color='#FFA500', width=1)), row=1, col=1)

    # --- 第 2 層：成交量 ---
    colors = ['#FF0000' if c >= o else '#008000' for o, c in zip(df['Open'], df['Close'])]
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'], 
        name='成交量', 
        marker_color=colors,
        showlegend=False
    ), row=2, col=1)

    # --- 第 3 層：RSI ---
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='#9370DB', width=1.5), showlegend=False), row=3, col=1)
    # 輔助線
    fig.add_hline(y=70, line_dash="dash", line_color="#555555", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#555555", row=3, col=1)

    # 佈局設定 (靜態化優化)
    fig.update_layout(
        template='plotly_dark',
        xaxis_rangeslider_visible=False,
        height=600,
        margin=dict(t=40, l=10, r=10, b=10),
        title=dict(
            text=f"{ticker} 走勢圖",
            y=0.98, x=0.05,
            font=dict(size=18, color="white")
        ),
        legend=dict(
            orientation="h", y=1, x=0.3,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=10)
        )
    )
    
    # 座標軸優化 (Y軸移至右側)
    fig.update_yaxes(row=1, col=1, side="right", tickformat="$.0f", gridcolor='#333333')
    fig.update_yaxes(row=2, col=1, side="right", showgrid=False, title_text="Vol", title_font=dict(size=10, color="gray"))
    fig.update_yaxes(row=3, col=1, side="right", tickvals=[30, 70], gridcolor='#333333', title_text="RSI", title_font=dict(size=10, color="gray"))
    
    # X軸設定 (移除週末空檔)
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
    
    return fig

# ==========================================
# 4. 行業熱圖邏輯
# ==========================================
@st.cache_data(ttl=300)
def fetch_sector_performance():
    """獲取行業數據 (確保不缺漏)"""
    data = []
    for ticker, name in SP500_SECTORS.items():
        row = {'sector': name, 'ticker': ticker, 'change': 0.0, 'status': 'no_data', 'today': 'N/A', 'yesterday': 'N/A'}
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="7d")
            
            if not hist.empty and len(hist) >= 2:
                # 正常情況：取最後兩日
                row['today'] = hist.index[-1].strftime('%Y-%m-%d')
                row['yesterday'] = hist.index[-2].strftime('%Y-%m-%d')
                curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                row['change'] = ((curr - prev) / prev) * 100
                row['status'] = 'ok'
            elif not hist.empty and len(hist) == 1:
                # 備援情況：只有一日數據
                row['today'] = hist.index[-1].strftime('%Y-%m-%d')
                curr = hist['Close'].iloc[-1]
                prev_close = stock.info.get('previousClose')
                if prev_close:
                    row['change'] = ((curr - prev_close) / prev_close) * 100
                    row['yesterday'] = "PrevClose API"
                    row['status'] = 'ok'
        except:
            pass # 錯誤時保持預設值，避免熱圖缺塊
        data.append(row)
    return pd.DataFrame(data)

def create_sector_heatmap(df):
    """建立台股風格熱圖"""
    if df.empty: return None
    
    # 準備顯示文字
    df['display_text'] = df.apply(lambda x: f"{x['change']:+.2f}%" if x['status'] == 'ok' else "無資料", axis=1)
    # 確保無資料時也有基本大小
    df['abs_change'] = df['change'].abs().apply(lambda x: x if x > 0.01 else 0.5)

    fig = px.treemap(
        df,
        path=['sector'],
        values='abs_change',
        color='change',
        # 台股紅漲綠跌配色
        color_continuous_scale=[
            [0, "#228B22"],      # 深綠 (跌)
            [0.45, "#90EE90"],   # 淺綠
            [0.5, "#808080"],    # 灰 (平)
            [0.55, "#FFB6C1"],   # 淺紅
            [1, "#FF0000"]       # 深紅 (漲)
        ],
        color_continuous_midpoint=0,
        range_color=[-4, 4]
    )
    
    fig.update_traces(
        texttemplate="<span style='font-size:16px;'><b>%{label}</b></span><br><span style='font-size:20px;'>%{customdata[0]}</span>",
        customdata=df[['display_text']],
        textposition='middle center',
        marker=dict(line=dict(width=1, color='white')),
        hovertemplate='<b>%{label}</b><br>漲跌幅: %{customdata[0]}<extra></extra>'
    )
    
    fig.update_layout(
        height=600,
        margin=dict(t=10, l=10, r=10, b=10),
        coloraxis_colorbar=dict(title="漲跌%")
    )
    return fig

# ==========================================
# 5. 主程式介面 (UI)
# ==========================================

st.title("📈 美股投資戰情室")
st.caption("專為手機優化的投資看盤工具")

mode = st.radio("選擇功能", ["📊 個股分析", "🔥 S&P 500 熱圖"], horizontal=True)
st.divider()

# --- 模式一：個股分析 ---
if mode == "📊 個股分析":
    # 1. 輸入與控制區
    col_input, col_period = st.columns([2, 2])
    with col_input:
        input_method = st.radio("輸入方式", ["下拉選單", "手動輸入"], horizontal=True, label_visibility="collapsed")
        if input_method == "下拉選單":
            ticker = st.selectbox("選擇股票", POPULAR_STOCKS)
        else:
            ticker = st.text_input("輸入代碼", value="NVDA").upper().strip()
            
    with col_period:
        time_period = st.select_slider("觀察區間", options=["1mo", "3mo", "6mo", "1y", "2y"], value="6mo")

    if st.button("🔍 分析", type="primary"):
        with st.spinner(f"正在連線華爾街載入 {ticker} ..."):
            # 獲取資料
            df = fetch_stock_history(ticker, period=time_period)
            stock_obj = get_stock_object(ticker)
            
            if df is not None:
                # --- A. 關鍵指標 ---
                latest = df.iloc[-1]
                prev = df.iloc[-2]
                change = latest['Close'] - prev['Close']
                pct = (change / prev['Close']) * 100
                rsi = calculate_rsi(df).iloc[-1]
                trend = get_trend_signal(df)
                
                # 股價顯示 (台股風格背景色)
                c1, c2, c3 = st.columns(3)
                
                if pct > 0:
                    bg, color, arrow = "rgba(255, 75, 75, 0.2)", "#FF4B4B", "▲"
                elif pct < 0:
                    bg, color, arrow = "rgba(0, 200, 83, 0.2)", "#00C853", "▼"
                else:
                    bg, color, arrow = "rgba(128, 128, 128, 0.2)", "#888888", ""
                    
                c1.markdown(f"""
                <div style="margin-bottom: 5px;">
                    <div style="color: #aaa; font-size: 12px;">股價</div>
                    <div style="font-size: 24px; font-weight: bold; color: white;">${latest['Close']:.2f}</div>
                    <div style="background:{bg}; color:{color}; padding: 2px 8px; border-radius: 4px; display:inline-block; font-size: 14px; font-weight:bold;">
                        {arrow} {pct:+.2f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                c2.metric("RSI (14)", f"{rsi:.1f}")
                c3.metric("市場趨勢", trend)

                # --- B. 技術分析圖 (靜態 Plotly) ---
                st.subheader("📈 技術分析圖")
                try:
                    fig = plot_candlestick(df, ticker)
                    # 這裡設定 staticPlot=True 讓手機滑動更順暢
                    st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True, 'displayModeBar': False})
                except Exception as e:
                    st.error(f"圖表繪製失敗: {e}")

                st.divider()

                # --- C. 機構持股 & 新聞 (參考 app.py 邏輯) ---
                col_hold, col_news = st.columns([1, 1])
                
                # 機構持股
                with col_hold:
                    st.subheader("🏢 機構持股 TOP 10")
                    try:
                        holders = stock_obj.institutional_holders
                        if holders is not None and not holders.empty:
                            display_holders = holders.copy()
                            # 防禦性移除不必要欄位
                            for col in ['Shares', 'Value']:
                                if col in display_holders.columns:
                                    display_holders = display_holders.drop(columns=[col])
                            
                            # 格式化日期
                            if 'Date Reported' in display_holders.columns:
                                display_holders['Date Reported'] = pd.to_datetime(display_holders['Date Reported']).dt.strftime('%Y-%m-%d')
                            
                            # 格式化持股比例
                            if 'pctHeld' in display_holders.columns:
                                display_holders['pctHeld'] = (display_holders['pctHeld'] * 100).map('{:.2f}%'.format)

                            st.dataframe(display_holders.head(10), use_container_width=True, hide_index=True)
                        else:
                            st.info("⚠️ 查無機構持股明細")
                    except:
                        st.error("持股數據讀取錯誤")

                # 新聞 (含 AI 翻譯與深度連結解析)
                with col_news:
                    st.subheader("📰 最新新聞 (AI 翻譯)")
                    try:
                        news = stock_obj.news
                        if news:
                            translator = GoogleTranslator(source='auto', target='zh-TW')
                            news_count = 0
                            for item in news[:5]:
                                try:
                                    # 深度解析
                                    content = item.get('content', item)
                                    title_en = content.get('title')
                                    link = content.get('url', content.get('clickThroughUrl', {}).get('url', '#'))
                                    
                                    if title_en:
                                        try:
                                            title_zh = translator.translate(title_en)
                                        except:
                                            title_zh = title_en
                                            
                                        with st.container(border=True):
                                            st.markdown(f"**{title_zh}**")
                                            st.link_button("閱讀全文", link)
                                        news_count += 1
                                        if news_count >= 3: break
                                except:
                                    continue
                            if news_count == 0:
                                st.info("📭 近期無相關新聞")
                        else:
                            st.info("📭 暫無新聞數據")
                    except:
                        st.info("⚠️ 新聞連線暫時中斷")
            else:
                st.error(f"無法載入 {ticker}，請確認代碼是否正確。")

# --- 模式二：S&P 500 熱圖 ---
elif mode == "🔥 S&P 500 熱圖":
    st.subheader("S&P 500 行業表現")
    st.caption("🔴 紅色=上漲 | 🟢 綠色=下跌")
    
    if st.button("🔄 載入熱圖", type="primary"):
        with st.spinner("正在掃描全市場數據..."):
            sector_df = fetch_sector_performance()
            
            if not sector_df.empty:
                st.success(f"✅ 載入完成")
                fig = create_sector_heatmap(sector_df)
                st.plotly_chart(fig, use_container_width=True)
                
                # 顯示數據日期
                valid = sector_df[sector_df['today'] != 'N/A']
                if not valid.empty:
                    st.caption(f"數據基準：{valid['today'].max()} (當日) vs {valid['yesterday'].max()} (前收)")
            else:
                st.error("無法載入數據，請稍後再試")
