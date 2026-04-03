from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
import json
import yfinance as yf
import requests
import anthropic
import time

app = Flask(__name__)
CORS(app)

# Initialize Claude client
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")

# ============================================================================
# MOCK DATA (Only as LAST RESORT fallback)
# ============================================================================

MOCK_STOCKS = {
    "INFY": {"current_price": 2950.50, "price_change_30d": 8.45, "ma_20": 2890.15, "volatility": 2.15, "pe_ratio": 28.5, "sector": "Information Technology"},
    "TCS": {"current_price": 4125.75, "price_change_30d": 6.20, "ma_20": 4050.00, "volatility": 1.95, "pe_ratio": 32.1, "sector": "Information Technology"},
    "HDFC": {"current_price": 2645.00, "price_change_30d": 4.85, "ma_20": 2580.00, "volatility": 1.65, "pe_ratio": 22.3, "sector": "Financials"},
    "MARUTI": {"current_price": 9850.25, "price_change_30d": 3.50, "ma_20": 9600.00, "volatility": 2.45, "pe_ratio": 18.9, "sector": "Auto"},
    "RELIANCE": {"current_price": 2845.50, "price_change_30d": 5.23, "ma_20": 2780.25, "volatility": 1.82, "pe_ratio": 24.3, "sector": "Financials"},
}

MOCK_NEWS = {
    "INFY": ["INFY sees accelerating cloud adoption demand", "INFY Q3 net profit up 18% YoY", "INFY upskilling 25% workforce in generative AI"],
    "TCS": ["TCS wins major contract from US client", "IT sector outlook improves; TCS in focus", "TCS margin expansion drives FY25 guidance up"],
    "HDFC": ["HDFC merger integration on track", "HDFC loan growth accelerates to 15%", "HDFC improves asset quality metrics"],
    "MARUTI": ["MARUTI sales jump 20% in March", "MARUTI launches new EV model", "MARUTI margins improve on cost cuts"],
    "RELIANCE": ["RELIANCE Q3 earnings beat estimates", "RELIANCE announces new energy division expansion", "RELIANCE seen gaining from oil price recovery"],
}

# Helper to format Indian Tickers
def get_yf_ticker(ticker):
    if ticker in ["INFY", "TCS", "MARUTI", "RELIANCE", "WIPRO"]:
        return f"{ticker}.NS"
    elif ticker == "HDFC":
        return "HDFCBANK.NS"
    return ticker

# ============================================================================
# FETCH LIVE STOCK DATA
# ============================================================================

def fetch_stock_data_live(ticker):
    """Try to fetch LIVE stock data from Yahoo Finance"""
    try:
        print(f"📊 Attempting LIVE data fetch for {ticker}...")
        yf_ticker = get_yf_ticker(ticker)
        
        stock = yf.Ticker(yf_ticker)
        hist = stock.history(period="30d")
        info = stock.info
        
        if hist.empty:
            print(f"⚠️  No live data for {ticker}")
            return None
        
        current_price = hist['Close'].iloc[-1]
        price_30d_ago = hist['Close'].iloc[0]
        price_change = ((current_price - price_30d_ago) / price_30d_ago) * 100
        
        ma_20 = hist['Close'].tail(20).mean()
        volatility = hist['Close'].pct_change().std() * 100
        
        print(f"✅ LIVE data fetched for {ticker}: ${current_price:.2f}")
        
        return {
            "ticker": ticker,
            "current_price": float(current_price),
            "price_change_30d": float(price_change),
            "ma_20": float(ma_20),
            "price_vs_ma20_pct": float(((current_price - ma_20) / ma_20 * 100)) if ma_20 > 0 else 0,
            "sector": info.get("sector", "Unknown"),
            "pe_ratio": float(info.get("trailingPE", 0)) if info.get("trailingPE") else "N/A",
            "volatility": float(volatility),
            "data_source": "Yahoo Finance (LIVE)"
        }
        
    except Exception as e:
        print(f"❌ Live data fetch failed: {str(e)}")
        return None

def fetch_news_live(ticker):
    """Try to fetch LIVE news from NewsAPI"""
    try:
        if not NEWS_API_KEY:
            return None
        
        print(f"📰 Attempting LIVE news fetch for {ticker}...")
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": ticker,
            "language": "en",
            "sortBy": "publishedAt",
            "apiKey": NEWS_API_KEY,
            "pageSize": 10,
        }
        
        response = requests.get(url, params=params, timeout=5)
        articles = response.json().get("articles", [])
        
        if not articles:
            return None
        
        news = [article.get("title", "") for article in articles[:10]]
        return news
        
    except Exception as e:
        return None

def get_fallback_data(ticker):
    ticker = ticker.upper()
    if ticker not in MOCK_STOCKS:
        return None
    data = MOCK_STOCKS[ticker]
    return {
        "ticker": ticker,
        "current_price": data["current_price"],
        "price_change_30d": data["price_change_30d"],
        "ma_20": data["ma_20"],
        "price_vs_ma20_pct": ((data["current_price"] - data["ma_20"]) / data["ma_20"] * 100),
        "sector": data["sector"],
        "pe_ratio": data["pe_ratio"],
        "volatility": data["volatility"],
        "data_source": "Mock Data (Fallback)"
    }

def get_fallback_news(ticker):
    return MOCK_NEWS.get(ticker.upper(), [f"Market data available for {ticker}"])

def fetch_stock_data(ticker):
    live_data = fetch_stock_data_live(ticker)
    return live_data if live_data else get_fallback_data(ticker)

def fetch_news(ticker):
    live_news = fetch_news_live(ticker)
    return live_news if live_news else get_fallback_news(ticker)

# ============================================================================
# AI AGENT SYNTHESIS
# ============================================================================

def run_ai_agent_synthesis(ticker, stock_data, news_headlines):
    if not client.api_key:
        return rule_based_analysis(stock_data)
    
    try:
        news_summary = "\n".join([f"- {headline}" for headline in news_headlines[:5]])
        prompt = f"""You are an expert quantitative research analyst. Analyze this stock data.
STOCK DATA:
Ticker: {ticker}
Current Price: ${stock_data['current_price']:.2f}
30-Day Return: {stock_data['price_change_30d']:.2f}%
Sector: {stock_data['sector']}

RECENT NEWS:
{news_summary}

TASKS:
1. Catalyst Check: Is news 'Material' or 'Noise'?
2. Signal: 'BUY', 'HOLD', or 'SELL'?
3. Score: 1-10 integer
4. Justification: Exactly 2 sentences

RESPOND ONLY IN JSON:
{{
    "signal": "BUY/SELL/HOLD",
    "signal_score": 8,
    "catalyst_type": "Material/Noise",
    "relative_strength": "Outperforming/In-line/Underperforming",
    "justification": "Two sentences."
}}"""
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        
        response_text = message.content[0].text
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        return json.loads(response_text[start_idx:end_idx])
        
    except Exception:
        return rule_based_analysis(stock_data)

def rule_based_analysis(stock_data):
    price_change = stock_data['price_change_30d']
    return {
        "signal": "BUY" if price_change > 5 else ("SELL" if price_change < -5 else "HOLD"),
        "signal_score": 8 if price_change > 5 else (3 if price_change < -5 else 5),
        "catalyst_type": "Mixed",
        "relative_strength": "Outperforming" if price_change > 3 else "In-line",
        "justification": f"Stock is performing with a 30-day return of {price_change:.1f}%."
    }

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/analyze', methods=['POST'])
def analyze_stock():
    try:
        data = request.get_json()
        ticker = data.get('ticker', '').strip().upper()
        
        stock_data = fetch_stock_data(ticker)
        news = fetch_news(ticker)
        analysis = run_ai_agent_synthesis(ticker, stock_data, news)
        
        return jsonify({
            "ticker": ticker,
            "stock_data": stock_data,
            "news": news[:5],
            "analysis": analysis,
            "status": "success"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route('/api/chart/<ticker>', methods=['GET'])
def get_chart_data(ticker):
    """Fetches real 30-day closing prices for the chart"""
    try:
        yf_ticker = get_yf_ticker(ticker.upper())
        stock = yf.Ticker(yf_ticker)
        hist = stock.history(period="30d")
        
        if hist.empty:
            # Fake fallback data if ticker not found
            return jsonify([{"day": f"Day {i}", "price": 100 + i, "ma20": 100} for i in range(1, 31)])
        
        chart_data = []
        ma_20_series = hist['Close'].rolling(window=20).mean()
        
        for i in range(len(hist)):
            date_str = hist.index[i].strftime('%b %d')
            chart_data.append({
                "day": date_str,
                "price": float(hist['Close'].iloc[i]),
                "ma20": float(ma_20_series.iloc[i]) if not os.path.isna(ma_20_series.iloc[i]) else float(hist['Close'].iloc[i])
            })
            
        return jsonify(chart_data)
    except Exception:
        return jsonify([])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)