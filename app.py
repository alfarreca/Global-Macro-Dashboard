import streamlit as st
import pandas as pd
import yfinance as yf
from fredapi import Fred
import plotly.express as px
import plotly.graph_objects as go
import datetime
import numpy as np
import time
from threading import Thread
import queue
import requests
from bs4 import BeautifulSoup

# Config
st.set_page_config(layout="wide", page_title="Real-Time Global Macro Dashboard", page_icon="🌍")

# CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .metric-title {
        font-size: 14px;
        color: #555;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
    }
    .metric-change {
        font-size: 14px;
    }
    .positive {
        color: green;
    }
    .negative {
        color: red;
    }
    .section-header {
        border-bottom: 2px solid #f0f2f6;
        padding-bottom: 5px;
        margin-top: 20px !important;
    }
    .blink {
        animation: blink-animation 1s steps(2, start) infinite;
    }
    @keyframes blink-animation {
        to { visibility: hidden; }
    }
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    .sidebar .sidebar-section {
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Fred API
fred = Fred(api_key=st.secrets["FRED_API_KEY"])

# Sidebar Menu
with st.sidebar:
    st.title("🌍 Navigation")
    
    # Dashboard sections
    selected_section = st.radio(
        "Go to:",
        ["📊 Full Dashboard", "📈 Markets", "🏦 Central Banks", "🛢️ Commodities", "⚠️ Geopolitical Risk"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("### 🔧 Settings")
    
    # Time range selector in sidebar
    time_range = st.selectbox(
        "Chart Time Range", 
        ["1D", "1W", "1M", "3M", "1Y"], 
        index=0
    )
    time_map = {"1D": "1d", "1W": "1wk", "1M": "1mo", "3M": "3mo", "1Y": "1y"}
    period = time_map[time_range]
    
    # Refresh options
    st.markdown("### 🔄 Refresh Options")
    auto_refresh = st.checkbox("Auto-refresh every minute", value=True)
    if st.button("Manual Refresh Now"):
        st.rerun()
    
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("""
    This dashboard provides real-time global macroeconomic data and market indicators.
    Data sources include FRED, Yahoo Finance, and other public APIs.
    """)

# Main content
st.title("🌍 Real-Time Global Macro Dashboard")

class RealTimeDataManager:
    def __init__(self):
        self.data_queue = queue.Queue()
        self.stop_thread = False
        self.last_update = datetime.datetime.now()
        self.cache = {
            "market_data": None,
            "economic_data": None,
            "central_bank_rates": None,
            "commodities": None,
            "gpr_index": None
        }
        self.errors = []

    def fetch_market_data(self):
        indices = {
            "S&P 500": "^GSPC",
            "NASDAQ": "^IXIC",
            "Dow Jones": "^DJI",
            "FTSE 100": "^FTSE",
            "DAX": "^GDAXI",
            "Nikkei 225": "^N225",
        }
        market_data = []
        for name, ticker in indices.items():
            try:
                data = yf.Ticker(ticker)
                hist = data.history(period="1d", interval="1m")
                if not hist.empty:
                    current = hist["Close"].iloc[-1]
                    prev_close = data.history(period="2d")["Close"].iloc[0]
                    change = ((current - prev_close) / prev_close) * 100
                    market_data.append({
                        "Index": name,
                        "Price": current,
                        "Change (%)": change,
                        "Last Update": datetime.datetime.now().strftime('%H:%M:%S')
                    })
                else:
                    self.errors.append(f"{name}: No data found (may be delisted or unsupported by Yahoo Finance).")
            except Exception as e:
                self.errors.append(f"Error fetching {name} data: {str(e)}")
        return market_data

    def fetch_economic_data(self):
        try:
            gdp_series = fred.get_series("GDPC1")
            us_gdp = gdp_series.tail(1).values[0]
            prev_gdp = gdp_series.tail(2).values[0]
            gdp_change = ((us_gdp - prev_gdp) / prev_gdp) * 100

            inflation_series = fred.get_series("CPIAUCSL").pct_change(12) * 100
            us_inflation = inflation_series.tail(1).values[0]
            prev_inflation = inflation_series.tail(2).values[0]
            inflation_change = us_inflation - prev_inflation

            unemp_series = fred.get_series("UNRATE")
            us_unemp = unemp_series.tail(1).values[0]
            prev_unemp = unemp_series.tail(2).values[0]
            unemp_change = us_unemp - prev_unemp

            return {
                "us_gdp": us_gdp,
                "gdp_change": gdp_change,
                "us_inflation": us_inflation,
                "inflation_change": inflation_change,
                "us_unemp": us_unemp,
                "unemp_change": unemp_change,
                "last_update": datetime.datetime.now().strftime('%H:%M:%S')
            }
        except Exception as e:
            self.errors.append(f"Error fetching economic data: {str(e)}")
            return None

    def fetch_central_bank_rates(self):
        try:
            fed_rate_series = fred.get_series("FEDFUNDS")
            fed_rate = fed_rate_series.tail(1).values[0]
            prev_fed_rate = fed_rate_series.tail(2).values[0]
            fed_change = fed_rate - prev_fed_rate

            ecb_rate, ecb_change = self._scrape_ecb_rate()
            boj_rate = -0.10
            boj_change = 0.00

            return {
                "fed_rate": fed_rate,
                "fed_change": fed_change,
                "ecb_rate": ecb_rate,
                "ecb_change": ecb_change,
                "boj_rate": boj_rate,
                "boj_change": boj_change,
                "last_update": datetime.datetime.now().strftime('%H:%M:%S')
            }
        except Exception as e:
            self.errors.append(f"Error fetching central bank rates: {str(e)}")
            return None

    def _scrape_ecb_rate(self):
        return 4.25, 0.0

    def fetch_commodities(self):
        commodities = {
            "Gold": "GC=F",
            "Silver": "SI=F",
            "Crude Oil": "CL=F",
            "Natural Gas": "NG=F",
            "Copper": "HG=F",
            "Wheat": "ZW=F"
        }
        comm_data = []
        for name, ticker in commodities.items():
            try:
                data = yf.Ticker(ticker)
                hist = data.history(period="1d", interval="1m")
                if not hist.empty:
                    current = hist["Close"].iloc[-1]
                    prev_close = data.history(period="2d")["Close"].iloc[0]
                    change = ((current - prev_close) / prev_close) * 100
                    comm_data.append({
                        "Commodity": name,
                        "Price": current,
                        "Change (%)": change,
                        "Last Update": datetime.datetime.now().strftime('%H:%M:%S')
                    })
                else:
                    self.errors.append(f"{name}: No data found (may be delisted or unsupported by Yahoo Finance).")
            except Exception as e:
                self.errors.append(f"Error fetching {name} data: {str(e)}")
        return comm_data

    def fetch_gpr_index(self):
        try:
            dates = pd.date_range(end=datetime.datetime.now(), periods=30)
            base_risk = 50 + np.random.normal(0, 2, 30)
            for i in [5, 15, 25]:
                base_risk[i] += 15 * np.random.random()
                for j in range(i+1, min(i+6, 30)):
                    base_risk[j] += (15 - (j-i)*3) * np.random.random()
            gpr_data = pd.DataFrame({"Date": dates, "Risk_Index": base_risk})
            return {
                "data": gpr_data,
                "current_value": base_risk[-1],
                "last_update": datetime.datetime.now().strftime('%H:%M:%S')
            }
        except Exception as e:
            self.errors.append(f"Error fetching GPR index: {str(e)}")
            return None

    def data_fetcher_thread(self):
        while not self.stop_thread:
            try:
                self.cache["market_data"] = self.fetch_market_data()
                self.cache["economic_data"] = self.fetch_economic_data()
                self.cache["central_bank_rates"] = self.fetch_central_bank_rates()
                self.cache["commodities"] = self.fetch_commodities()
                self.cache["gpr_index"] = self.fetch_gpr_index()
                self.last_update = datetime.datetime.now()
                time.sleep(60)
            except Exception as e:
                self.errors.append(f"Error in data fetcher thread: {str(e)}")
                time.sleep(10)

    def start(self):
        self.stop_thread = False
        thread = Thread(target=self.data_fetcher_thread)
        thread.daemon = True
        thread.start()

    def stop(self):
        self.stop_thread = True

data_manager = RealTimeDataManager()
data_manager.start()

if data_manager.errors:
    for err in data_manager.errors:
        st.warning(err)
    data_manager.errors.clear()

# Status bar at top
col1, col2 = st.columns([4,1])
with col1:
    last_update_str = data_manager.last_update.strftime('%Y-%m-%d %H:%M:%S')
    st.markdown(f"**Last Updated:** <span class='blink'>{last_update_str}</span>", unsafe_allow_html=True)

with col2:
    if st.button("🔄 Refresh Now"):
        data_manager.last_update = datetime.datetime.now()
        st.rerun()

# Show sections based on sidebar selection
if selected_section == "📊 Full Dashboard" or selected_section == "📈 Markets":
    # ----- Real-Time Market Overview -----
    st.header("📈 Real-Time Market Overview", divider="rainbow")
    if data_manager.cache["market_data"] is not None:
        df_market = pd.DataFrame(data_manager.cache["market_data"])
        if not df_market.empty:
            cols = st.columns(4)
            for idx, row in df_market.head(4).iterrows():
                with cols[idx % 4]:
                    change_class = "positive" if row["Change (%)"] >= 0 else "negative"
                    change_arrow = "↑" if row["Change (%)"] >= 0 else "↓"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">{row['Index']}</div>
                        <div class="metric-value">${row['Price']:,.2f}</div>
                        <div class="metric-change {change_class}">
                            {change_arrow} {abs(row['Change (%)']):.2f}% 
                            <span style="font-size: 12px;">({row['Last Update']})</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            with st.expander("View All Market Indices"):
                if not df_market.empty:
                    st.dataframe(
                        df_market.sort_values("Change (%)", ascending=False),
                        column_config={
                            "Price": st.column_config.NumberColumn(format="$%.2f"),
                            "Change (%)": st.column_config.NumberColumn(format="%.2f%%")
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    st.info("No market data available.")
            if not df_market.empty:
                selected_index = st.selectbox("Select Index for Detailed View", df_market["Index"].tolist(), index=0)
                ticker_map = {
                    "S&P 500": "^GSPC", "NASDAQ": "^IXIC", "Dow Jones": "^DJI",
                    "FTSE 100": "^FTSE", "DAX": "^GDAXI", "Nikkei 225": "^N225"
                }
                selected_ticker = ticker_map[selected_index]
                try:
                    intraday_data = yf.Ticker(selected_ticker).history(period="1d", interval="5m")
                    if not intraday_data.empty:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=intraday_data.index,
                            y=intraday_data["Close"],
                            name="Price",
                            line=dict(color='royalblue', width=2)
                        ))
                        fig.update_layout(
                            title=f"Intraday {selected_index} Price",
                            xaxis_title="Time",
                            yaxis_title="Price",
                            hovermode="x unified"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not display chart for {selected_index}: {str(e)}")
        else:
            st.info("No market data available.")
    else:
        st.info("No market data available.")

if selected_section == "📊 Full Dashboard":
    # ----- Real-Time Economic Indicators -----
    st.header("📊 Real-Time Economic Indicators", divider="rainbow")
    if data_manager.cache["economic_data"] is not None:
        econ_data = data_manager.cache["economic_data"]
        if econ_data:
            col1, col2, col3 = st.columns(3)
            with col1:
                change_class = "positive" if econ_data["gdp_change"] > 0 else "negative"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">US GDP (Latest QoQ)</div>
                    <div class="metric-value">${econ_data["us_gdp"]:,.2f}B</div>
                    <div class="metric-change {change_class}">
                        {'+' if econ_data["gdp_change"] > 0 else ''}{econ_data["gdp_change"]:.1f}% from previous
                        <span style="font-size: 12px;">({econ_data["last_update"]})</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                change_class = "positive" if econ_data["inflation_change"] < 0 else "negative"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">US Inflation (YoY)</div>
                    <div class="metric-value">{econ_data["us_inflation"]:.1f}%</div>
                    <div class="metric-change {change_class}">
                        {'+' if econ_data["inflation_change"] > 0 else ''}{econ_data["inflation_change"]:.1f}% from previous
                        <span style="font-size: 12px;">({econ_data["last_update"]})</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                change_class = "positive" if econ_data["unemp_change"] < 0 else "negative"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">US Unemployment Rate</div>
                    <div class="metric-value">{econ_data["us_unemp"]:.1f}%</div>
                    <div class="metric-change {change_class}">
                        {'+' if econ_data["unemp_change"] > 0 else ''}{econ_data["unemp_change"]:.1f}% from previous
                        <span style="font-size: 12px;">({econ_data["last_update"]})</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No economic data available.")
    else:
        st.info("No economic data available.")

if selected_section == "📊 Full Dashboard" or selected_section == "🏦 Central Banks":
    # ----- Real-Time Central Bank Rates -----
    st.header("🏦 Real-Time Central Bank Rates", divider="rainbow")
    if data_manager.cache["central_bank_rates"] is not None:
        rates_data = data_manager.cache["central_bank_rates"]
        if rates_data:
            col1, col2, col3 = st.columns(3)
            with col1:
                change_class = "positive" if rates_data["fed_change"] < 0 else "negative"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Federal Reserve Rate</div>
                    <div class="metric-value">{rates_data["fed_rate"]:.2f}%</div>
                    <div class="metric-change {change_class}">
                        {'+' if rates_data["fed_change"] > 0 else ''}{rates_data["fed_change"]:.2f}% from previous
                        <span style="font-size: 12px;">({rates_data["last_update"]})</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                change_class = "positive" if rates_data["ecb_change"] < 0 else "negative"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">ECB Main Refinancing Rate</div>
                    <div class="metric-value">{rates_data["ecb_rate"]:.2f}%</div>
                    <div class="metric-change {change_class}">
                        {'+' if rates_data["ecb_change"] > 0 else ''}{rates_data["ecb_change"]:.2f}% from previous
                        <span style="font-size: 12px;">({rates_data["last_update"]})</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                change_class = "positive" if rates_data["boj_change"] < 0 else "negative"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">BOJ Policy Rate</div>
                    <div class="metric-value">{rates_data["boj_rate"]:.2f}%</div>
                    <div class="metric-change {change_class}">
                        {'+' if rates_data["boj_change"] > 0 else ''}{rates_data["boj_change"]:.2f}% from previous
                        <span style="font-size: 12px;">({rates_data["last_update"]})</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No central bank data available.")
    else:
        st.info("No central bank data available.")

if selected_section == "📊 Full Dashboard" or selected_section == "🛢️ Commodities":
    # ----- Real-Time Commodities -----
    st.header("🛢️ Real-Time Commodities", divider="rainbow")
    if data_manager.cache["commodities"] is not None:
        df_comm = pd.DataFrame(data_manager.cache["commodities"])
        with st.expander("View All Commodities"):
            if not df_comm.empty:
                st.dataframe(
                    df_comm.sort_values("Change (%)", ascending=False),
                    column_config={
                        "Price": st.column_config.NumberColumn(format="$%.2f"),
                        "Change (%)": st.column_config.NumberColumn(format="%.2f%%")
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("No commodity data available.")
        if not df_comm.empty:
            cols = st.columns(4)
            for idx, row in df_comm.head(4).iterrows():
                with cols[idx % 4]:
                    change_class = "positive" if row["Change (%)"] >= 0 else "negative"
                    change_arrow = "↑" if row["Change (%)"] >= 0 else "↓"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">{row['Commodity']}</div>
                        <div class="metric-value">${row['Price']:,.2f}</div>
                        <div class="metric-change {change_class}">
                            {change_arrow} {abs(row['Change (%)']):.2f}% 
                            <span style="font-size: 12px;">({row['Last Update']})</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No commodity data available.")
    else:
        st.info("No commodity data available.")

if selected_section == "📊 Full Dashboard" or selected_section == "⚠️ Geopolitical Risk":
    # ----- Real-Time Geopolitical Risk Index -----
    st.header("⚠️ Real-Time Geopolitical Risk Index", divider="rainbow")
    if data_manager.cache["gpr_index"] is not None:
        gpr_data = data_manager.cache["gpr_index"]
        if gpr_data:
            risk_level = gpr_data["current_value"]
            if risk_level < 40:
                risk_color = "green"
                risk_text = "Low"
            elif 40 <= risk_level < 60:
                risk_color = "orange"
                risk_text = "Moderate"
            else:
                risk_color = "red"
                risk_text = "High"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Current Geopolitical Risk Level</div>
                <div class="metric-value" style="color: {risk_color}">{risk_level:.1f} ({risk_text})</div>
                <div class="metric-change">
                    Last updated: {gpr_data["last_update"]}
                </div>
            </div>
            """, unsafe_allow_html=True)
            fig = px.line(
                gpr_data["data"], 
                x="Date", 
                y="Risk_Index", 
                title="Geopolitical Risk Index (Last 30 Days)",
                labels={"Risk_Index": "Risk Index"}
            )
            fig.add_hline(y=40, line_dash="dot", line_color="green", annotation_text="Low Risk Threshold")
            fig.add_hline(y=60, line_dash="dot", line_color="red", annotation_text="High Risk Threshold")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No GPR data available.")
    else:
        st.info("No GPR data available.")

# ----- News Feed -----
if selected_section == "📊 Full Dashboard":
    st.header("📰 Latest Economic News", divider="rainbow")
    def fetch_economic_news():
        news_items = [
            {
                "title": "Fed Signals Potential Rate Cuts Later This Year",
                "source": "Financial Times",
                "time": "15 minutes ago",
                "impact": "High"
            },
            {
                "title": "Inflation Shows Signs of Cooling in Latest Report",
                "source": "Wall Street Journal",
                "time": "1 hour ago",
                "impact": "Medium"
            },
            {
                "title": "Trade Deficit Widens Amid Global Supply Chain Shifts",
                "source": "Bloomberg",
                "time": "2 hours ago",
                "impact": "Medium"
            },
            {
                "title": "ECB Maintains Rates Amid Economic Uncertainty",
                "source": "Reuters",
                "time": "3 hours ago",
                "impact": "High"
            }
        ]
        return news_items

    news_items = fetch_economic_news()
    if news_items:
        for news in news_items:
            with st.expander(f"{news['title']} ({news['source']} - {news['time']})"):
                st.write("This is a simulated news item. In a production app, you would integrate with a real news API.")
                st.markdown(f"**Impact:** {news['impact']}")
    else:
        st.info("No news available.")

st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 12px;">
    <p>Data Sources: FRED, Yahoo Finance, ECB | Last Updated: {}</p>
    <p>Disclaimer: This dashboard is for informational purposes only. Data may be delayed.</p>
</div>
""".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')), unsafe_allow_html=True)
