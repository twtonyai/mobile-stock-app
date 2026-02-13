# 📈 行動版美股投資戰情室 (Mobile Stock Dashboard)

專為 iPhone 優化的輕量級美股投資看盤工具，提供個股技術分析和 S&P 500 行業熱圖監控。

## 🎯 功能特色

### 📊 個股全方位分析
- **關鍵指標**: 最新股價、漲跌幅、RSI(14)、趨勢判斷
- **技術分析圖**: K線圖 + 20MA/60MA + 成交量 + RSI 副圖
- **機構持股**: 顯示前 10 大機構投資者
- **AI 新聞翻譯**: 自動將英文新聞標題翻譯成繁體中文

### 🔥 S&P 500 行業熱圖
- **美股標準配色**: 紅色代表上漲，綠色代表下跌
- **動態區塊大小**: 依據漲跌幅絕對值決定
- **11 大行業追蹤**: 科技、金融、醫療、消費等主要板塊

## 🚀 快速部署到 Streamlit Cloud

### 步驟 1: 準備 GitHub 儲存庫

1. 在 GitHub 建立新的 **Public** 儲存庫
2. 將以下檔案上傳至儲存庫:
   - `streamlit_app.py`
   - `requirements.txt`
   - `README.md`

### 步驟 2: 部署到 Streamlit Cloud

1. 前往 [Streamlit Cloud](https://streamlit.io/cloud)
2. 使用 GitHub 帳號登入
3. 點擊 "New app"
4. 選擇你的儲存庫、分支和主檔案 (`streamlit_app.py`)
5. 點擊 "Deploy"
6. 等待 2-3 分鐘完成部署

### 步驟 3: 在 iPhone 上使用

1. 開啟 Safari 或 Chrome
2. 訪問你的 Streamlit 應用網址
3. 點擊分享按鈕 → "加入主畫面" (建立快捷方式)
4. 現在可以像 App 一樣快速開啟！

## 💻 本地開發

### 安裝套件

```bash
pip install -r requirements.txt
```

### 執行應用

```bash
streamlit run streamlit_app.py
```

應用將在 `http://localhost:8501` 開啟。

## 📱 手機優化說明

- **響應式設計**: 自動適應不同螢幕尺寸
- **大按鈕**: 易於點擊的介面元素
- **簡潔佈局**: 減少捲動，提升閱讀體驗
- **快速載入**: 優化數據請求，減少等待時間

## 🛠️ 技術架構

- **框架**: Streamlit
- **數據源**: Yahoo Finance API (yfinance)
- **圖表**: mplfinance, Plotly
- **翻譯**: Google Translator API
- **部署**: Streamlit Community Cloud

## 📊 支援股票

### 預設熱門個股
AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, META, BRK.B, V, JNJ, WMT, JPM, MA, PG, UNH, DIS, HD, BAC, NFLX, ADBE, CRM, CSCO, PFE, TMO, COST, INTC

### S&P 500 行業 ETF
- XLK (科技)
- XLF (金融)
- XLV (醫療保健)
- XLY (非必需消費)
- XLC (通訊服務)
- XLI (工業)
- XLP (必需消費)
- XLE (能源)
- XLRE (房地產)
- XLB (原物料)
- XLU (公用事業)

## ⚠️ 免責聲明

本工具僅供參考，不構成任何投資建議。所有投資決策請自行評估風險。

## 📝 授權

MIT License - 自由使用和修改

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

---

**Made with ❤️ for iPhone investors**
