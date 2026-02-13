import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import mplfinance as mpf
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
import io
import warnings
warnings.filterwarnings('ignore')

# 頁面配置 - 針對手機優化
st.set_page_config(
    page_title="美股投資戰情室",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定義 CSS - 手機優化
st.markdown("""
<style>
    /* 手機優化 */
    .main {
        padding: 0.5rem;
    }
    
    /* 指標卡片樣式 */
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
        text-align: center;
    }
    
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        margin: 5px 0;
    }
    
    .metric-label {
        font-size: 14px;
        color: #666;
    }
    
    /* 按鈕樣式 */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: bold;
    }
    
    /* 熱圖優化 */
    .plotly-graph-div {
        height: 600px !important;
    }
</style>
""", unsafe_allow_html=True)

# S&P 500 主要行業代碼和名稱
SP500_SECTORS = {
    "XLK": "科技 (Technology)",
    "XLF": "金融 (Financial)",
    "XLV": "醫療保健 (Healthcare)",
    "XLY": "非必需消費 (Consumer Discretionary)",
    "XLC": "通訊服務 (Communication)",
    "XLI": "工業 (Industrial)",
    "XLP": "必需消費 (Consumer Staples)",
    "XLE": "能源 (Energy)",
    "XLRE": "房地產 (Real Estate)",
    "XLB": "原物料 (Materials)",
    "XLU": "公用事業 (Utilities)"
}

# 熱門個股清單
POPULAR_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK.B",
    "V", "JNJ", "WMT", "JPM", "MA", "PG", "UNH", "DIS", "HD", "BAC",
    "NFLX", "ADBE", "CRM", "CSCO", "PFE", "TMO", "COST", "INTC"
]

def calculate_rsi(data, periods=14):
    """計算 RSI 指標"""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_trend_signal(df):
    """判斷趨勢"""
    if len(df) < 60:
        return "數據不足"
    
    current_price = df['Close'].iloc[-1]
    ma20 = df['Close'].rolling(20).mean().iloc[-1]
    ma60 = df['Close'].rolling(60).mean().iloc[-1]
    rsi = calculate_rsi(df).iloc[-1]
    
    if current_price > ma20 > ma60 and rsi > 50:
        return "多頭 🚀"
    elif current_price < ma20 < ma60 and rsi < 50:
        return "空頭 📉"
    else:
        return "盤整 ↔️"

def fetch_stock_data(ticker, period="6mo"):
    """獲取股票數據"""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty:
            return None, None
        return df, stock
    except Exception as e:
        st.error(f"無法獲取 {ticker} 的數據: {str(e)}")
        return None, None

def plot_candlestick(df, ticker):
    """繪製 K 線圖"""
    # 計算移動平均線
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    df['RSI'] = calculate_rsi(df)
    
    # 準備 mplfinance 數據
    mpf_df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    
    # 移動平均線
    apds = [
        mpf.make_addplot(df['MA20'], color='blue', width=1.5),
        mpf.make_addplot(df['MA60'], color='orange', width=1.5),
        mpf.make_addplot(df['RSI'], panel=2, color='purple', ylabel='RSI')
    ]
    
    # 自定義樣式
    mc = mpf.make_marketcolors(
        up='red', down='green',
        edge='inherit',
        wick='inherit',
        volume='inherit'
    )
    s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=False)
    
    # 繪製圖表
    fig, axes = mpf.plot(
        mpf_df,
        type='candle',
        style=s,
        addplot=apds,
        volume=True,
        title=f'{ticker} 技術分析圖',
        ylabel='股價 ($)',
        ylabel_lower='成交量',
        figsize=(10, 8),
        returnfig=True,
        panel_ratios=(3, 1, 1)
    )
    
    return fig

def translate_to_chinese(text):
    """翻譯成繁體中文"""
    try:
        translator = GoogleTranslator(source='en', target='zh-TW')
        return translator.translate(text)
    except:
        return text

def fetch_news(ticker, stock):
    """獲取並翻譯新聞"""
    try:
        news = stock.news[:3] if hasattr(stock, 'news') and stock.news else []
        translated_news = []
        
        for item in news:
            title = item.get('title', '')
            link = item.get('link', '')
            translated_title = translate_to_chinese(title)
            translated_news.append({
                'title': translated_title,
                'link': link
            })
        
        return translated_news
    except:
        return []

def fetch_institutional_holders(stock):
    """獲取機構持股"""
    try:
        holders = stock.institutional_holders
        if holders is not None and not holders.empty:
            holders.columns = ['機構名稱', '持股數', '持股日期', '持股比例', '持股價值']
            return holders.head(10)
        return None
    except:
        return None

def fetch_sector_performance():
    """獲取 S&P 500 行業表現"""
    sector_data = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, (ticker, name) in enumerate(SP500_SECTORS.items()):
        try:
            status_text.text(f"正在載入 {name}...")
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            
            if not hist.empty and len(hist) >= 2:
                # 計算漲跌幅
                current = hist['Close'].iloc[-1]
                previous = hist['Close'].iloc[-2]
                change = ((current - previous) / previous) * 100
                
                sector_data.append({
                    'sector': name,
                    'ticker': ticker,
                    'change': change
                })
            
            progress_bar.progress((idx + 1) / len(SP500_SECTORS))
        except Exception as e:
            st.warning(f"無法載入 {name}: {str(e)}")
            continue
    
    progress_bar.empty()
    status_text.empty()
    
    return pd.DataFrame(sector_data)

def create_sector_heatmap(df):
    """創建行業熱圖 - 美股標準配色（綠跌紅漲）"""
    if df.empty:
        return None
    
    # 計算絕對值用於區塊大小
    df['abs_change'] = df['change'].abs()
    
    # 格式化顯示文字
    df['display_text'] = df.apply(
        lambda x: f"<b>{x['sector']}</b><br><b style='font-size:18px'>{x['change']:+.2f}%</b>",
        axis=1
    )
    
    # 使用 RdYlGn_r 配色（反轉）：綠色=負值（下跌），紅色=正值（上漲）
    fig = px.treemap(
        df,
        path=['sector'],
        values='abs_change',
        color='change',
        color_continuous_scale='RdYlGn_r',  # 反轉配色
        color_continuous_midpoint=0,
        custom_data=['display_text'],
        title='S&P 500 行業熱圖 (紅漲綠跌)'
    )
    
    # 更新佈局
    fig.update_traces(
        texttemplate='%{customdata[0]}',
        textposition='middle center',
        marker=dict(line=dict(width=2, color='white'))
    )
    
    fig.update_layout(
        height=600,
        margin=dict(t=50, l=10, r=10, b=10),
        coloraxis_colorbar=dict(
            title="漲跌幅 (%)",
            tickformat='+.1f'
        )
    )
    
    return fig

# ==================== 主程式 ====================

st.title("📈 美股投資戰情室")
st.caption("行動版投資看盤工具 - 專為 iPhone 優化")

# 功能模式選擇
mode = st.radio(
    "選擇功能",
    ["📊 個股分析", "🔥 S&P 500 熱圖"],
    horizontal=True
)

st.divider()

# ==================== 模式 A: 個股分析 ====================
if mode == "📊 個股分析":
    st.subheader("個股全方位分析")
    
    # 輸入方式選擇
    input_method = st.radio(
        "選擇輸入方式",
        ["下拉選單", "手動輸入"],
        horizontal=True
    )
    
    if input_method == "下拉選單":
        ticker = st.selectbox("選擇股票", POPULAR_STOCKS)
    else:
        ticker = st.text_input("輸入股票代碼 (如 AAPL)", value="AAPL").upper()
    
    if st.button("🔍 開始分析", type="primary"):
        with st.spinner(f"正在分析 {ticker}..."):
            df, stock = fetch_stock_data(ticker)
            
            if df is not None and stock is not None:
                # 計算指標
                current_price = df['Close'].iloc[-1]
                prev_price = df['Close'].iloc[-2]
                price_change = current_price - prev_price
                price_change_pct = (price_change / prev_price) * 100
                volume = df['Volume'].iloc[-1]
                rsi = calculate_rsi(df).iloc[-1]
                trend = get_trend_signal(df)
                
                # 顯示關鍵指標
                st.success(f"✅ 成功載入 {ticker} 數據")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("股價", f"${current_price:.2f}", f"{price_change_pct:+.2f}%")
                
                with col2:
                    st.metric("RSI(14)", f"{rsi:.1f}", "")
                
                with col3:
                    st.metric("趨勢", trend, "")
                
                # K 線圖
                st.subheader("📈 技術分析圖")
                fig = plot_candlestick(df, ticker)
                st.pyplot(fig)
                
                # 機構持股
                st.subheader("🏢 機構持股 TOP 10")
                holders = fetch_institutional_holders(stock)
                if holders is not None:
                    st.dataframe(holders, use_container_width=True)
                else:
                    st.info("暫無機構持股資料")
                
                # AI 翻譯新聞
                st.subheader("📰 最新新聞 (AI 翻譯)")
                news_list = fetch_news(ticker, stock)
                
                if news_list:
                    for idx, news in enumerate(news_list, 1):
                        with st.container():
                            st.markdown(f"**{idx}. {news['title']}**")
                            st.link_button("閱讀全文", news['link'], use_container_width=True)
                            st.divider()
                else:
                    st.info("暫無相關新聞")
            else:
                st.error(f"無法載入 {ticker} 的數據，請確認股票代碼是否正確")

# ==================== 模式 B: S&P 500 熱圖 ====================
elif mode == "🔥 S&P 500 熱圖":
    st.subheader("S&P 500 行業表現")
    st.caption("紅色=上漲 | 綠色=下跌 | 區塊大小=波動程度")
    
    if st.button("🔄 載入熱圖", type="primary"):
        with st.spinner("正在載入 11 個行業數據..."):
            sector_df = fetch_sector_performance()
            
            if not sector_df.empty:
                st.success(f"✅ 成功載入 {len(sector_df)} 個行業數據")
                
                # 顯示統計
                avg_change = sector_df['change'].mean()
                st.metric("平均漲跌幅", f"{avg_change:+.2f}%")
                
                # 繪製熱圖
                fig = create_sector_heatmap(sector_df)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                
                # 顯示詳細數據
                st.subheader("📋 詳細數據")
                display_df = sector_df[['sector', 'ticker', 'change']].copy()
                display_df.columns = ['行業', '代碼', '漲跌幅 (%)']
                display_df['漲跌幅 (%)'] = display_df['漲跌幅 (%)'].apply(lambda x: f"{x:+.2f}%")
                display_df = display_df.sort_values('行業')
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.error("無法載入行業數據，請稍後再試")

# 頁尾
st.divider()
st.caption("📱 數據來源: Yahoo Finance | ⚠️ 僅供參考，不構成投資建議")
