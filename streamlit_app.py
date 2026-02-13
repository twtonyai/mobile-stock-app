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

# 頁面配置
st.set_page_config(
    page_title="美股投資戰情室",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定義 CSS
st.markdown("""
<style>
    .main {padding: 0.5rem;}
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# S&P 500 主要行業
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

# 熱門個股
POPULAR_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", 
    "V", "JNJ", "WMT", "JPM", "MA", "DIS", "NFLX", "COST"
]

@st.cache_data(ttl=300)
def calculate_rsi(data, periods=14):
    """計算 RSI"""
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

# 修改：只快取數據，不快取物件
@st.cache_data(ttl=300)
def fetch_stock_history(ticker, period="6mo"):
    """獲取股票歷史價格數據"""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty:
            return None
        return df
    except Exception as e:
        return None

def get_stock_object(ticker):
    """獲取 Ticker 物件 (不快取)"""
    return yf.Ticker(ticker)

def plot_candlestick(df, ticker):
    """繪製 K 線圖"""
    # 計算移動平均線
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    df['RSI'] = calculate_rsi(df)
    
    # 準備 mplfinance 數據
    mpf_df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    
    # 移動平均線和 RSI (panel=2 因為 volume 佔用 panel 1)
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
        result = translator.translate(text)
        return result if result else text
    except Exception as e:
        # 翻譯失敗時返回原文
        return text

def fetch_news(stock):
    """獲取並翻譯新聞"""
    try:
        news_list = []
        if hasattr(stock, 'news') and stock.news:
            for item in stock.news[:3]:
                title = item.get('title', '')
                link = item.get('link', '')
                
                if title:  # 確保標題存在
                    # 嘗試翻譯，失敗則使用原文
                    translated_title = translate_to_chinese(title)
                    news_list.append({
                        'title': translated_title,
                        'link': link
                    })
        
        return news_list
    except Exception as e:
        return []

def fetch_institutional_holders(stock):
    """獲取機構持股 - 修正：接收 stock 物件而非 ticker 字串"""
    try:
        holders = stock.institutional_holders
        if holders is not None and not holders.empty:
            # 重新命名欄位
            holders = holders.copy()
            holders.columns = ['機構名稱', '持股數', '持股日期', '持股比例', '持股價值']
            return holders.head(10)
        return None
    except Exception as e:
        return None

@st.cache_data(ttl=300)
@st.cache_data(ttl=300)
def fetch_sector_performance():
    """獲取當日行業表現 - 確保所有行業都顯示"""
    sector_data = []
    
    for ticker, name in SP500_SECTORS.items():
        # 預設資料：若抓不到則顯示為「無資料」狀態
        row = {
            'sector': name, 
            'ticker': ticker, 
            'change': 0.0, 
            'status': 'no_data',
            'today': 'N/A',
            'yesterday': 'N/A'
        }
try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="7d")
            
            if not hist.empty and len(hist) >= 2:
                # 紀錄最後兩筆交易日的日期
                row['today'] = hist.index[-1].strftime('%Y-%m-%d')
                row['yesterday'] = hist.index[-2].strftime('%Y-%m-%d')
                
                current = hist['Close'].iloc[-1]
                previous = hist['Close'].iloc[-2]
                row['change'] = ((current - previous) / previous) * 100
                row['status'] = 'ok'
        except:
            pass
        sector_data.append(row)
    return pd.DataFrame(sector_data)

def create_sector_heatmap(df):
    """創建台股風格熱圖 (紅漲綠跌)"""
    if df.empty: return None

    # 準備顯示文字：沒資料時顯示「無資料」
    df['display_text'] = df.apply(
        lambda x: f"{x['change']:+.2f}%" if x['status'] == 'ok' else "無資料", axis=1
    )
    
    # 方塊大小依據：漲跌幅絕對值，最小值給 0.1 確保「無資料」也能看到方塊
    df['abs_change'] = df['change'].abs().apply(lambda x: x if x > 0.01 else 0.5)

    fig = px.treemap(
        df,
        path=['sector'],
        values='abs_change',
        color='change',
        # 台股顏色：綠(跌) -> 灰(平) -> 紅(漲)
        color_continuous_scale=[
            [0, "#228B22"],      # 深綠
            [0.45, "#90EE90"],   # 淺綠
            [0.5, "#808080"],    # 灰色 (0%)
            [0.55, "#FFB6C1"],   # 淺紅
            [1, "#FF0000"]       # 純紅
        ],
        color_continuous_midpoint=0,
        range_color=[-4, 4]
    )

    fig.update_traces(
        # 使用 customdata 帶入我們準備好的 display_text
        texttemplate="<span style='font-size:16px;'><b>%{label}</b></span><br><span style='font-size:20px;'>%{customdata[0]}</span>",
        customdata=df[['display_text']],
        textposition='middle center',
        marker=dict(line=dict(width=1, color='white')),
        hovertemplate='<b>%{label}</b><br>漲跌幅: %{customdata[0]}<extra></extra>'
    )
    
    fig.update_layout(
        height=600,
        margin=dict(t=10, l=10, r=10, b=10),
        coloraxis_colorbar=dict(title="漲跌%", tickvals=[-4, -2, 0, 2, 4])
    )
    return fig

# ========== 主程式 ==========

st.title("📈 美股投資戰情室")
st.caption("專為手機優化的投資看盤工具")

mode = st.radio("選擇功能", ["📊 個股分析", "🔥 S&P 500 熱圖"], horizontal=True)
st.divider()

# ========== 個股分析 ==========
if mode == "📊 個股分析":
    st.subheader("個股分析")
    
    input_method = st.radio("輸入方式", ["下拉選單", "手動輸入"], horizontal=True)
    
    if input_method == "下拉選單":
        ticker = st.selectbox("選擇股票", POPULAR_STOCKS)
    else:
        ticker = st.text_input("輸入代碼", value="AAPL").upper()
    
    if st.button("🔍 分析", type="primary"):
        with st.spinner(f"載入 {ticker} 中..."):
            df = fetch_stock_history(ticker)
            stock = get_stock_object(ticker) # 直接獲取物件
            
            if df is not None and stock is not None:
                # 關鍵指標
                current_price = df['Close'].iloc[-1]
                prev_price = df['Close'].iloc[-2]
                change_pct = ((current_price - prev_price) / prev_price) * 100
                rsi = calculate_rsi(df).iloc[-1]
                trend = get_trend_signal(df)
                
                st.success(f"✅ {ticker} 數據已載入")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("股價", f"${current_price:.2f}", f"{change_pct:+.2f}%")
                col2.metric("RSI(14)", f"{rsi:.1f}")
                col3.metric("趨勢", trend)
                
                # K 線圖
                st.subheader("📈 技術分析圖")
                try:
                    fig = plot_candlestick(df, ticker)
                    st.pyplot(fig)
                except Exception as e:
                    st.error(f"圖表繪製失敗: {str(e)}")
                
                # 機構持股 - 傳入 stock 物件
                st.subheader("🏢 機構持股 TOP 10")
                holders = fetch_institutional_holders(stock)
                if holders is not None:
                    st.dataframe(holders, use_container_width=True, hide_index=True)
                else:
                    st.info("暫無機構持股資料")
                
                # 新聞 - 傳入 stock 物件
                st.subheader("📰 最新新聞 (AI 翻譯)")
                news_list = fetch_news(stock)
                if news_list:
                    for idx, news in enumerate(news_list, 1):
                        st.markdown(f"**{idx}. {news['title']}**")
                        st.link_button("閱讀全文", news['link'], use_container_width=True)
                        if idx < len(news_list):
                            st.divider()
                else:
                    st.info("暫無新聞")
            else:
                st.error(f"無法載入 {ticker}，請確認代碼是否正確")

# ========== S&P 500 熱圖 ==========
elif mode == "🔥 S&P 500 熱圖":
    st.subheader("S&P 500 行業表現")
    st.caption("🔴 紅色=上漲 | 🟢 綠色=下跌")
    
    if st.button("🔄 載入熱圖", type="primary"):
        with st.spinner("載入 11 個行業..."):
            sector_df = fetch_sector_performance()
            
            if not sector_df.empty:
                st.success(f"✅ 載入 {len(sector_df)} 個行業")
                
                avg_change = sector_df['change'].mean()
                st.metric("平均漲跌", f"{avg_change:+.2f}%")
                
            fig = create_sector_heatmap(sector_df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
                
                # --- 新增：顯示取用的數據日期 ---
                # 從 DataFrame 中找出最新的交易日期 (排除 N/A)
                valid_dates = sector_df[sector_df['today'] != 'N/A']
                if not valid_dates.empty:
                    latest_t = valid_dates['today'].max()
                    prev_t = valid_dates['yesterday'].max()
                    st.info(f"📊 **數據基準說明**")
                    st.caption(f"本熱圖計算邏輯：比較 **{latest_t}** (當日收盤) 與 **{prev_t}** (前一交易日收盤) 之價差。")
                else:
                    st.warning("⚠️ 目前抓取不到任何有效日期數據，請檢查網路連線。")
                
                st.subheader("📋 詳細數據")
                display_df = sector_df[['sector', 'ticker', 'change']].copy()
                display_df.columns = ['行業', '代碼', '漲跌%']
                display_df['漲跌%'] = display_df['漲跌%'].apply(lambda x: f"{x:+.2f}%")
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.error("無法載入數據")

st.divider()
st.caption("📊 數據來源: Yahoo Finance | ⚠️ 僅供參考，不構成投資建議")
