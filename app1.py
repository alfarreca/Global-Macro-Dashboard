import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from fredapi import Fred
import plotly.graph_objects as go
import datetime
import time
import threading
import pytz
from dateutil.relativedelta import relativedelta
import warnings
warnings.filterwarnings('ignore')

# Try to import st_aggrid with fallback
try:
    from st_aggrid import AgGrid, GridOptionsBuilder
    AGGRID_AVAILABLE = True
except ImportError:
    AGGRID_AVAILABLE = False
    st.warning("streamlit-aggrid not available. Using standard DataFrame display.")

# Configuration
st.set_page_config(
    layout="wide",
    page_title="Global Macro Pro Dashboard",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# API Clients (using Streamlit secrets)
try:
    fred = Fred(api_key=st.secrets["FRED_API_KEY"])
except Exception as e:
    st.error(f"Failed to initialize FRED API: {str(e)}")
    st.stop()

# Constants
TIME_ZONE = pytz.timezone('America/New_York')
REFRESH_INTERVAL = 60  # seconds

# ==================== STYLING ====================
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 4px solid #4e73df;
    }
    .metric-title { font-size: 0.85rem; color: #5a5c69; text-transform: uppercase; font-weight: 700; margin-bottom: 0.25rem; }
    .metric-value { font-size: 1.5rem; font-weight: 700; color: #2e59d9; }
    .metric-change { font-size: 0.85rem; margin-top: 0.25rem; }
    .positive { color: #1cc88a; }
    .negative { color: #e74a3b; }
    .section-header { color: #4e73df; font-weight: 700; margin: 1.5rem 0 1rem 0; padding-bottom: 0.5rem; border-bottom: 1px solid #e3e6f0; }
    .stTabs [role="tablist"] { margin-bottom: 0; }
    .dataframe { width: 100%; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    .blink { animation: blink 1.5s infinite; }
</style>
""", unsafe_allow_html=True)

# ==================== DATA MANAGER ====================
class DataManager:
    def __init__(self):
        self.data_lock = threading.Lock()
        self.cache = {
            "market": None,
            "economic": None,
            "rates": None,
            "commodities": None,
            "risk": None,
            "news": None
        }
        self.last_updated = datetime.datetime.now(TIME_ZONE)
        self.stop_event = threading.Event()
        
    def fetch_market_data(self):
        indices = {
            "S&P 500": "^GSPC",
            "NASDAQ": "^IXIC",
            "Dow 30": "^DJI",
            "Russell 2000": "^RUT",
            "FTSE 100": "^FTSE",
            "DAX": "^GDAXI",
            "CAC 40": "^FCHI",
            "Nikkei 225": "^N225",
            "Shanghai": "^SSEC",
            "Hang Seng": "^HSI"
        }
        data = []
        for name, ticker in indices.items():
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="2d", interval="1d")
                if not hist.empty:
                    current = hist["Close"].iloc[-1]
                    prev_close = hist["Close"].iloc[0]
                    change_pct = (current - prev_close) / prev_close * 100
                    intraday = stock.history(period="1d", interval="5m") if name == "S&P 500" else None
                    data.append({
                        "Index": name,
                        "Ticker": ticker,
                        "Price": current,
                        "Change": current - prev_close,
                        "Change %": change_pct,
                        "Prev Close": prev_close,
                        "Intraday": intraday,
                        "Updated": datetime.datetime.now(TIME_ZONE)
                    })
            except Exception as e:
                st.error(f"Error fetching {name}: {str(e)}")
        return data
    
    def fetch_economic_indicators(self):
        indicators = {
            "GDP": {"series": "GDPC1", "transform": lambda x: x, "format": "${:,.1f}B"},
            "Inflation": {"series": "CPIAUCSL", "transform": lambda x: x.pct_change(12).iloc[-1]*100, "format": "{:.1f}%"},
            "Unemployment": {"series": "UNRATE", "transform": lambda x: x.iloc[-1], "format": "{:.1f}%"},
            "Retail Sales": {"series": "RSXFS", "transform": lambda x: x.pct_change(12).iloc[-1]*100, "format": "{:.1f}%"},
            "Industrial Production": {"series": "INDPRO", "transform": lambda x: x.pct_change(12).iloc[-1]*100, "format": "{:.1f}%"}
        }
        results = {}
        for name, config in indicators.items():
            try:
                series = fred.get_series(config["series"])
                if name == "GDP":
                    latest_val = config["transform"](series).iloc[-1] / 1e3  # Convert millions to billions
                    formatted_val = config["format"].format(latest_val)
                    value = latest_val
                else:
                    value = config["transform"](series)
                    formatted_val = config["format"].format(value)
                results[name] = {
                    "value": value,
                    "formatted": formatted_val,
                    "history": series.tail(24),
                    "updated": datetime.datetime.now(TIME_ZONE)
                }
            except Exception as e:
                st.error(f"Error fetching {name}: {str(e)}")
        return results
    
    def fetch_central_bank_rates(self):
        rates = {
            "Federal Reserve": {"series": "FEDFUNDS", "color": "#2e59d9"},
            "ECB": {"series": "ECBESTRVOLWGTTRMDMNRT", "color": "#4e73df"},
            "BOE": {"series": "IUDSOIA", "color": "#e74a3b"},
            "BOJ": {"series": "IRSTCI01JPM156N", "color": "#1cc88a"}
        }
        results = {}
        for name, config in rates.items():
            try:
                series = fred.get_series(config["series"])
                current = series.iloc[-1]
                prev = series.iloc[-2] if len(series) > 1 else current
                change = current - prev
                results[name] = {
                    "rate": current,
                    "change": change,
                    "history": series.tail(36),
                    "color": config["color"],
                    "updated": datetime.datetime.now(TIME_ZONE)
                }
            except Exception as e:
                st.error(f"Error fetching {name} rates: {str(e)}")
        return results
    
    def fetch_commodities(self):
        commodities = {
            "Crude Oil (WTI)": {"ticker": "CL=F", "unit": "$/bbl"},
            "Brent Crude": {"ticker": "BZ=F", "unit": "$/bbl"},
            "Gold": {"ticker": "GC=F", "unit": "$/oz"},
            "Silver": {"ticker": "SI=F", "unit": "$/oz"},
            "Copper": {"ticker": "HG=F", "unit": "$/lb"},
            "Natural Gas": {"ticker": "NG=F", "unit": "$/mmBtu"},
            "Wheat": {"ticker": "ZW=F", "unit": "$/bushel"}
        }
        results = []
        for name, config in commodities.items():
            try:
                ticker = yf.Ticker(config["ticker"])
                hist = ticker.history(period="2d", interval="1d")
                if not hist.empty:
                    current = hist["Close"].iloc[-1]
                    prev_close = hist["Close"].iloc[0]
                    change_pct = (current - prev_close) / prev_close * 100
                    results.append({
                        "Commodity": name,
                        "Price": current,
                        "Unit": config["unit"],
                        "Change %": change_pct,
                        "Updated": datetime.datetime.now(TIME_ZONE)
                    })
            except Exception as e:
                st.error(f"Error fetching {name}: {str(e)}")
        return results
    
    def fetch_risk_sentiment(self):
        now = datetime.datetime.now(TIME_ZONE)
        try:
            vix = yf.Ticker("^VIX").history(period="1d").iloc[0]["Close"]
        except Exception as e:
            st.error(f"Error fetching VIX: {str(e)}")
            vix = 20  # Default value
        return {
            "VIX": {
                "value": vix,
                "level": "High" if vix > 30 else "Elevated" if vix > 20 else "Normal",
                "history": yf.Ticker("^VIX").history(period="1mo")["Close"],
                "updated": now
            },
            "GPR": {
                "value": np.random.normal(50, 10),
                "level": "Elevated",
                "history": pd.Series(np.random.normal(50, 5, 30)),
                "updated": now
            },
            "Sentiment": {
                "value": np.random.uniform(0, 100),
                "level": "Neutral",
                "updated": now
            }
        }
    
    def fetch_news(self):
        now = datetime.datetime.now(TIME_ZONE)
        return [
            {
                "headline": "Fed Holds Rates Steady, Signals Potential Cuts Later This Year",
                "source": "Financial Times",
                "timestamp": now - datetime.timedelta(minutes=15),
                "impact": "High",
                "sentiment": -0.7
            },
            {
                "headline": "Inflation Shows Signs of Cooling in Latest Economic Report",
                "source": "Wall Street Journal",
                "timestamp": now - datetime.timedelta(minutes=45),
                "impact": "Medium",
                "sentiment": 0.5
            }
        ]
    
    def update_all_data(self):
        try:
            new_data = {
                "market": self.fetch_market_data(),
                "economic": self.fetch_economic_indicators(),
                "rates": self.fetch_central_bank_rates(),
                "commodities": self.fetch_commodities(),
                "risk": self.fetch_risk_sentiment(),
                "news": self.fetch_news()
            }
            with self.data_lock:
                self.cache = new_data
                self.last_updated = datetime.datetime.now(TIME_ZONE)
        except Exception as e:
            st.error(f"Data update failed: {str(e)}")
    
    def start(self):
        def update_loop():
            while not self.stop_event.is_set():
                self.update_all_data()
                time.sleep(REFRESH_INTERVAL)
        self.thread = threading.Thread(target=update_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        self.stop_event.set()
        self.thread.join()

# Initialize data manager
if 'data_manager' not in st.session_state:
    data_manager = DataManager()
    data_manager.start()
    st.session_state.data_manager = data_manager
else:
    data_manager = st.session_state.data_manager

# ==================== SIDEBAR ====================
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=Macro+Pro", width=150)
    st.markdown("## Dashboard Controls")
    timeframe = st.selectbox(
        "Time Horizon",
        ["Intraday", "1 Week", "1 Month", "3 Months", "1 Year"],
        index=2
    )
    regions = st.multiselect(
        "Regions",
        ["North America", "Europe", "Asia", "Emerging Markets"],
        default=["North America", "Europe", "Asia"]
    )
    st.markdown("---")
    st.markdown(f"**Last Updated:** <span class='blink'>{data_manager.last_updated.strftime('%Y-%m-%d %H:%M:%S')}</span>", 
                unsafe_allow_html=True)
    if st.button("🔄 Manual Refresh"):
        data_manager.update_all_data()
        st.rerun()
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    **Global Macro Pro Dashboard**  
    Professional-grade macroeconomic monitoring tool  
    Version 2.1.0  
    Data updates every 60 seconds  
    """)

# ==================== MAIN DASHBOARD ====================
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
    <h1 style="margin: 0;">Global Macro Pro Dashboard</h1>
    <div style="font-size: 0.9rem; color: #6c757d;">
        {datetime.datetime.now(TIME_ZONE).strftime('%A, %B %d, %Y')}
    </div>
</div>
""", unsafe_allow_html=True)

# ===== MARKET OVERVIEW =====
st.markdown('<div class="section-header">📈 Market Overview</div>', unsafe_allow_html=True)
if data_manager.cache["market"]:
    market_data = data_manager.cache["market"]
    cols = st.columns(4)
    for i, index in enumerate(market_data[:4]):
        with cols[i]:
            change_class = "positive" if index["Change %"] >= 0 else "negative"
            change_arrow = "▲" if index["Change %"] >= 0 else "▼"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{index['Index']}</div>
                <div class="metric-value">{index['Price']:,.2f}</div>
                <div class="metric-change {change_class}">
                    {change_arrow} {abs(index['Change %']):.2f}%
                </div>
            </div>
            """, unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Charts", "Performance Table"])
    with tab1:
        fig = go.Figure()
        if market_data[0]["Intraday"] is not None:
            intraday = market_data[0]["Intraday"]
            fig.add_trace(go.Scatter(
                x=intraday.index,
                y=intraday["Close"],
                name="S&P 500",
                line=dict(color='#4e73df', width=2)
            ))
        fig.update_layout(
            title="S&P 500 Intraday",
            xaxis_title="Time",
            yaxis_title="Price",
            hovermode="x unified",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    with tab2:
        df_market = pd.DataFrame(market_data)
        df_market = df_market[["Index", "Price", "Change", "Change %", "Updated"]]
        if 'Updated' in df_market.columns:
            df_market['Updated'] = df_market['Updated'].astype(str)
        if AGGRID_AVAILABLE:
            try:
                gb = GridOptionsBuilder.from_dataframe(df_market)
                gb.configure_default_column(
                    filterable=True,
                    sortable=True,
                    resizable=True,
                    editable=False,
                    wrapText=True,
                    autoHeight=True
                )
                # No cellStyle!
                gridOptions = gb.build()
                AgGrid(
                    df_market,
                    gridOptions=gridOptions,
                    height=400,
                    theme='streamlit',
                    fit_columns_on_grid_load=True,
                    allow_unsafe_jscode=True
                )
            except Exception as e:
                st.error(f"Error displaying AgGrid table: {str(e)}")
                st.dataframe(df_market.style.format({
                    "Price": "{:,.2f}",
                    "Change": "{:,.2f}",
                    "Change %": "{:,.2f}%"
                }), height=400)
        else:
            st.dataframe(df_market.style.format({
                "Price": "{:,.2f}",
                "Change": "{:,.2f}",
                "Change %": "{:,.2f}%"
            }), height=400)

# ===== ECONOMIC INDICATORS =====
st.markdown('<div class="section-header">📊 Economic Indicators</div>', unsafe_allow_html=True)
if data_manager.cache["economic"]:
    economic_data = data_manager.cache["economic"]
    cols = st.columns(5)
    for i, (name, data) in enumerate(economic_data.items()):
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{name}</div>
                <div class="metric-value">{data['formatted']}</div>
                <div class="metric-change">Latest reading</div>
            </div>
            """, unsafe_allow_html=True)
    fig = go.Figure()
    for name, data in economic_data.items():
        fig.add_trace(go.Scatter(
            x=data["history"].index,
            y=data["history"],
            name=name,
            mode="lines"
        ))
    fig.update_layout(
        title="Economic Indicators Trend",
        xaxis_title="Date",
        yaxis_title="Value",
        hovermode="x unified",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

# ===== CENTRAL BANK RATES =====
st.markdown('<div class="section-header">🏦 Central Bank Rates</div>', unsafe_allow_html=True)
if data_manager.cache["rates"]:
    rates_data = data_manager.cache["rates"]
    cols = st.columns(4)
    for i, (name, data) in enumerate(rates_data.items()):
        with cols[i]:
            change_class = "positive" if data["change"] <= 0 else "negative"  # Lower rates are positive
            change_arrow = "▼" if data["change"] <= 0 else "▲"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{name}</div>
                <div class="metric-value">{data['rate']:.2f}%</div>
                <div class="metric-change {change_class}">
                    {change_arrow} {abs(data['change']):.2f}bps
                </div>
            </div>
            """, unsafe_allow_html=True)
    fig = go.Figure()
    for name, data in rates_data.items():
        fig.add_trace(go.Scatter(
            x=data["history"].index,
            y=data["history"],
            name=name,
            line=dict(color=data["color"], width=2),
            mode="lines"
        ))
    fig.update_layout(
        title="Central Bank Rates History",
        xaxis_title="Date",
        yaxis_title="Rate (%)",
        hovermode="x unified",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

# ===== COMMODITIES =====
st.markdown('<div class="section-header">⛏️ Commodities</div>', unsafe_allow_html=True)
if data_manager.cache["commodities"]:
    commodities_data = data_manager.cache["commodities"]
    df_commodities = pd.DataFrame(commodities_data)
    if 'Updated' in df_commodities.columns:
        df_commodities['Updated'] = df_commodities['Updated'].astype(str)
    if AGGRID_AVAILABLE:
        try:
            gb = GridOptionsBuilder.from_dataframe(df_commodities)
            gb.configure_default_column(
                filterable=True,
                sortable=True,
                resizable=True,
                editable=False
            )
            # No cellStyle!
            gridOptions = gb.build()
            AgGrid(
                df_commodities,
                gridOptions=gridOptions,
                height=300,
                theme="streamlit",
                fit_columns_on_grid_load=True,
                allow_unsafe_jscode=True
            )
        except Exception as e:
            st.error(f"Error displaying AgGrid table: {str(e)}")
            st.dataframe(df_commodities.style.format({
                "Price": "{:,.2f}",
                "Change %": "{:,.2f}%"
            }), height=300)
    else:
        st.dataframe(df_commodities.style.format({
            "Price": "{:,.2f}",
            "Change %": "{:,.2f}%"
        }), height=300)

# ===== RISK & SENTIMENT =====
st.markdown('<div class="section-header">⚠️ Risk & Sentiment</div>', unsafe_allow_html=True)
if data_manager.cache["risk"]:
    risk_data = data_manager.cache["risk"]
    cols = st.columns(3)
    with cols[0]:
        vix_level = risk_data["VIX"]["level"]
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">VIX Index</div>
            <div class="metric-value">{risk_data['VIX']['value']:.2f}</div>
            <div class="metric-change">Level: {vix_level}</div>
        </div>
        """, unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Geopolitical Risk</div>
            <div class="metric-value">{risk_data['GPR']['value']:.1f}</div>
            <div class="metric-change">Level: {risk_data['GPR']['level']}</div>
        </div>
        """, unsafe_allow_html=True)
    with cols[2]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Market Sentiment</div>
            <div class="metric-value">{risk_data['Sentiment']['value']:.1f}</div>
            <div class="metric-change">Level: {risk_data['Sentiment']['level']}</div>
        </div>
        """, unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=risk_data["VIX"]["history"].index,
        y=risk_data["VIX"]["history"],
        name="VIX Index",
        line=dict(color='#e74a3b', width=2)
    ))
    fig.update_layout(
        title="VIX Index (30 Days)",
        xaxis_title="Date",
        yaxis_title="Value",
        hovermode="x unified",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

# ===== NEWS & EVENTS =====
st.markdown('<div class="section-header">📰 News & Events</div>', unsafe_allow_html=True)
if data_manager.cache["news"]:
    news_data = data_manager.cache["news"]
    for news in news_data:
        sentiment_color = "#1cc88a" if news["sentiment"] > 0 else "#e74a3b" if news["sentiment"] < 0 else "#6c757d"
        impact_color = "#e74a3b" if news["impact"] == "High" else "#f6c23e" if news["impact"] == "Medium" else "#1cc88a"
        st.markdown(f"""
        <div class="metric-card" style="margin-bottom: 1rem;">
            <div style="font-weight: 700; margin-bottom: 0.5rem;">{news['headline']}</div>
            <div style="font-size: 0.85rem; color: #6c757d; margin-bottom: 0.25rem;">
                {news['source']} • {news['timestamp'].strftime('%Y-%m-%d %H:%M')}
            </div>
            <div style="display: flex;">
                <span style="font-size: 0.8rem; background: {impact_color}; color: white; padding: 0.2rem 0.5rem; border-radius: 10px; margin-right: 0.5rem;">
                    {news['impact']}
                </span>
                <span style="font-size: 0.8rem; background: {sentiment_color}; color: white; padding: 0.2rem 0.5rem; border-radius: 10px;">
                    Sentiment: {'Positive' if news['sentiment'] > 0 else 'Negative' if news['sentiment'] < 0 else 'Neutral'}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ===== FOOTER =====
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6c757d; font-size: 0.8rem;">
    <p>Global Macro Pro Dashboard v2.1 | Data updates every 60 seconds | © 2023 Macro Analytics</p>
    <p>Disclaimer: This is a simulation for demonstration purposes. Not financial advice.</p>
</div>
""", unsafe_allow_html=True)
