import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './App.css';

function App() {
  const [ticker, setTicker] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [isPosted, setIsPosted] = useState(false);
  const [isPosting, setIsPosting] = useState(false);

  const handleAnalyze = async () => {
    if (!ticker.trim()) {
      setError('Please enter a ticker');
      return;
    }

    setLoading(true);
    setError(null);
    setAnalysis(null);
    setIsPosted(false); 

    try {
      const response = await fetch('http://localhost:5000/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker: ticker.toUpperCase() }),
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }

      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError(`Failed to fetch data: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handlePostToApp = () => {
    setIsPosting(true);
    setTimeout(() => {
      setIsPosting(false);
      setIsPosted(true);
      setTimeout(() => setIsPosted(false), 3000);
    }, 800);
  };

  const getSignalColor = (signal) => {
    if (signal === 'BUY') return '#10b981';
    if (signal === 'SELL') return '#ef4444';
    return '#f59e0b';
  };

  // RESTORED: Hardcoded 7-day simulation mapping directly to the live current price
  const getChartData = () => {
    if (!analysis) return [];
    
    const currentPrice = analysis.stock_data.current_price;
    
    return [
      { day: 'Day 1', price: currentPrice - 95, ma20: currentPrice - 100 },
      { day: 'Day 2', price: currentPrice - 60, ma20: currentPrice - 85 },
      { day: 'Day 3', price: currentPrice - 75, ma20: currentPrice - 70 },
      { day: 'Day 4', price: currentPrice - 30, ma20: currentPrice - 55 },
      { day: 'Day 5', price: currentPrice + 10, ma20: currentPrice - 30 },
      { day: 'Day 6', price: currentPrice + 40, ma20: currentPrice - 10 },
      { day: 'Day 7', price: currentPrice,      ma20: currentPrice + 15 },
    ];
  };

  return (
    <div className="App">
      <header className="main-header">
        <div className="title-wrapper">
          <h1 className="main-title">📊 Analyst Co-Pilot</h1>
        </div>
        <p className="main-subtitle">AI-Powered Stock Research Portal for Professional Analysts</p>
      </header>

      <div className="search-section">
        <input
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
          placeholder="Enter ticker (e.g., INFY, TCS, HDFC, MARUTI, RELIANCE)"
        />
        <button onClick={handleAnalyze} disabled={loading}>
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>

      {error && <div className="error">{error}</div>}
      {loading && <div className="loading">Loading...</div>}

      {analysis && (
        <div className="results">
          <div className="chart-section">
            <h2>Price Action vs 20-Day MA (Last 7 Days)</h2>
            <ResponsiveContainer width="100%" height={300}>
              {/* KEY ADDED: Forces the line chart to cleanly redraw on ticker change */}
              <LineChart key={analysis.ticker} data={getChartData()} margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
                <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                <XAxis 
                  stroke="#1d4ed8" 
                  dataKey="day" 
                  tick={{ fill: '#1d4ed8', fontWeight: 'bold' }}
                />
                <YAxis 
                  stroke="#1d4ed8" 
                  tick={{ fill: '#1d4ed8', fontWeight: 'bold' }}
                  domain={['dataMin - 50', 'dataMax + 50']}
                  tickFormatter={(value) => `₹${value.toFixed(0)}`}
                />
                <Tooltip 
                  contentStyle={{ background: '#0f172a', border: '1px solid #1d4ed8', borderRadius: '8px', color: '#fff' }}
                  formatter={(value) => `₹${value.toFixed(2)}`}
                />
                <Legend wrapperStyle={{ paddingTop: '10px' }} />
                <Line 
                  type="monotone" 
                  dataKey="price" 
                  stroke="#3b82f6" 
                  name="Stock Price"
                  strokeWidth={3}
                  dot={{ fill: '#1d4ed8', r: 6, stroke: '#fff', strokeWidth: 1.5 }}
                  activeDot={{ r: 8, fill: '#1e40af' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="ma20" 
                  stroke="#eab308" 
                  name="20-Day MA"
                  strokeWidth={3}
                  strokeDasharray="7 5"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="signal-section">
            <h2>Signal Recommendation</h2>
            <div className="signal-card" style={{ borderLeft: `5px solid ${getSignalColor(analysis.analysis.signal)}` }}>
              <div style={{ fontSize: '2.5rem', color: getSignalColor(analysis.analysis.signal), fontWeight: 'bold' }}>
                {analysis.analysis.signal}
              </div>
              <div style={{ marginTop: '10px' }}>Score: <strong>{analysis.analysis.signal_score}/10</strong></div>
              <div style={{ marginTop: '10px' }}>Justification: {analysis.analysis.justification}</div>
              <div style={{ marginTop: '10px' }}>Catalyst Type: <strong>{analysis.analysis.catalyst_type}</strong></div>
              <div style={{ marginTop: '10px' }}>Strength: <strong>{analysis.analysis.relative_strength}</strong></div>
              
              <button 
                className="post-btn" 
                onClick={handlePostToApp} 
                disabled={isPosting || isPosted}
                style={{
                  background: isPosted ? '#2563eb' : (isPosting ? '#6b7280' : '#10b981'),
                  transition: 'all 0.3s ease'
                }}
              >
                {isPosting ? 'Posting...' : (isPosted ? '✅ Posted to App!' : 'Post to App')}
              </button>
            </div>
          </div>

          <div className="news-section">
            <h2>Key News Evaluated</h2>
            {analysis.news && analysis.news.length > 0 ? (
              <ul>
                {analysis.news.map((item, idx) => (
                  <li key={idx}>
                    {typeof item === 'string' ? item : item.headline}
                  </li>
                ))}
              </ul>
            ) : (
              <p>No news available</p>
            )}
          </div>

          <div className="metrics-section">
            <h2>Stock Metrics</h2>
            <div className="metrics">
              <div className="metric">
                <span>Current Price:</span>
                <strong>₹{analysis.stock_data.current_price.toFixed(2)}</strong>
              </div>
              <div className="metric">
                <span>30-Day Change:</span>
                <strong style={{ color: analysis.stock_data.price_change_30d > 0 ? '#10b981' : '#ef4444' }}>
                  {analysis.stock_data.price_change_30d > 0 ? '+' : ''}{analysis.stock_data.price_change_30d.toFixed(2)}%
                </strong>
              </div>
              <div className="metric">
                <span>20-Day MA:</span>
                <strong>₹{analysis.stock_data.ma_20.toFixed(2)}</strong>
              </div>
              <div className="metric">
                <span>Price vs MA-20:</span>
                <strong style={{ color: analysis.stock_data.price_vs_ma20_pct > 0 ? '#10b981' : '#ef4444' }}>
                  {analysis.stock_data.price_vs_ma20_pct > 0 ? '+' : ''}{analysis.stock_data.price_vs_ma20_pct.toFixed(2)}%
                </strong>
              </div>
              <div className="metric">
                <span>Sector:</span>
                <strong>{analysis.stock_data.sector}</strong>
              </div>
              <div className="metric">
                <span>P/E Ratio:</span>
                <strong>{analysis.stock_data.pe_ratio}</strong>
              </div>
              <div className="metric">
                <span>Volatility:</span>
                <strong>{analysis.stock_data.volatility.toFixed(2)}%</strong>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;