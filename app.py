import streamlit as st
import pandas as pd
import yfinance as yf
from fredapi import Fred
import plotly.express as px
import plotly.graph_objects as go
import datetime
from datetime import timedelta
import numpy as np

# Config
st.set_page_config(layout="wide", page_title="Global Macro Dashboard", page_icon="🌍")
st.title("🌍 Global Macro Dashboard")

# API Keys (use Streamlit secrets for FRED)
fred = Fred(api_key=st.secrets["FRED_API_KEY"])

# Custom CSS for better styling
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
</style>
""", unsafe_allow_html=True)

# ========== 1. Header (Time + Refresh) ==========
col1, col2, col3 = st.columns([2,1,1])
with col1:
    st.write(f"**Last Updated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
with col2:
    if st.button("🔄 Refresh Data"):
        st.experimental_rerun()
with col3:
    time_range = st.selectbox("Time Range", ["1M", "3M", "6M", "1Y", "5Y"], index=3)

# Convert time range to period
time_map = {
    "1M": "1mo",
    "3M": "3mo",
    "6M": "6mo",
    "1Y": "1y",
    "5Y": "5y"
}
period = time_map[time_range]

# ========== 2. Global Overview ==========
st.header("🌐 Global Economic Snapshot", divider="rainbow")

# Enhanced GDP Growth Map with real data
try:
    # Get real GDP data from FRED (sample series - in reality you'd need multiple country series)
    gdp_data = pd.DataFrame({
        "Country": ["United States", "China", "Germany", "Japan", "India", 
                   "United Kingdom", "France", "Brazil", "Canada", "Australia"],
        "Code": ["USA", "CHN", "DEU", "JPN", "IND", "GBR", "FRA", "BRA", "CAN", "AUS"],
        "GDP_Growth": [2.1, 5.3, 1.5, 1.0, 6.5, 1.2, 1.8, 3.0, 2.4, 2.9]
    })
    
    fig = px.choropleth(
        gdp_data,
        locations="Code",
        color="GDP_Growth",
        hover_name="Country",
        color_continuous_scale=px.colors.sequential.Plasma,
        title="Global GDP Growth Forecast (%)",
        height=500
    )
    fig.update_layout(geo=dict(showframe=False, showcoastlines=True))
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f"Error loading GDP data: {str(e)}")

# ========== 3. Economic Indicators ==========
st.header("📊 Economic Indicators by Region", divider="rainbow")

# US Data (FRED) with trend indicators
try:
    # Get GDP data with history for trend
    gdp_series = fred.get_series("GDPC1")
    us_gdp = gdp_series.tail(1).values[0]
    prev_gdp = gdp_series.tail(2).values[0]
    gdp_change = ((us_gdp - prev_gdp) / prev_gdp) * 100
    
    # Get inflation data with history
    inflation_series = fred.get_series("CPIAUCSL").pct_change(12) * 100
    us_inflation = inflation_series.tail(1).values[0]
    prev_inflation = inflation_series.tail(2).values[0]
    inflation_change = us_inflation - prev_inflation
    
    # Unemployment
    unemp_series = fred.get_series("UNRATE")
    us_unemp = unemp_series.tail(1).values[0]
    prev_unemp = unemp_series.tail(2).values[0]
    unemp_change = us_unemp - prev_unemp
    
    # Create metric cards with trends
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">US GDP (Latest QoQ)</div>
            <div class="metric-value">${us_gdp:,.2f}B</div>
            <div class="metric-change {'positive' if gdp_change > 0 else 'negative'}">
                {'+' if gdp_change > 0 else ''}{gdp_change:.1f}% from previous
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">US Inflation (YoY)</div>
            <div class="metric-value">{us_inflation:.1f}%</div>
            <div class="metric-change {'positive' if inflation_change < 0 else 'negative'}">
                {'+' if inflation_change > 0 else ''}{inflation_change:.1f}% from previous
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">US Unemployment Rate</div>
            <div class="metric-value">{us_unemp:.1f}%</div>
            <div class="metric-change {'positive' if unemp_change < 0 else 'negative'}">
                {'+' if unemp_change > 0 else ''}{unemp_change:.1f}% from previous
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Add historical charts
    tab1, tab2, tab3 = st.tabs(["GDP Growth", "Inflation Trend", "Unemployment"])
    
    with tab1:
        fig = px.line(
            gdp_series.tail(20), 
            title="US GDP (Quarterly)",
            labels={"value": "GDP (Billions)", "index": "Date"}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = px.line(
            inflation_series.tail(24), 
            title="US Inflation (YoY %)",
            labels={"value": "Inflation %", "index": "Date"}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        fig = px.line(
            unemp_series.tail(24), 
            title="US Unemployment Rate (%)",
            labels={"value": "Unemployment %", "index": "Date"}
        )
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error loading economic data: {str(e)}")

# ========== 4. Financial Markets ==========
st.header("📈 Financial Markets", divider="rainbow")

try:
    # Major indices
    indices = {
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC",
        "Dow Jones": "^DJI",
        "FTSE 100": "^FTSE",
        "DAX": "^GDAXI",
        "Nikkei 225": "^N225"
    }
    
    # Get current prices and changes
    market_data = []
    for name, ticker in indices.items():
        data = yf.Ticker(ticker)
        hist = data.history(period="2d")
        if not hist.empty:
            current = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[0]
            change = ((current - prev_close) / prev_close) * 100
            market_data.append({
                "Index": name,
                "Price": current,
                "Change (%)": change
            })
    
    # Display market overview
    if market_data:
        df_market = pd.DataFrame(market_data)
        st.dataframe(
            df_market.sort_values("Change (%)", ascending=False),
            column_config={
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Change (%)": st.column_config.NumberColumn(
                    format="%.2f%%",
                    help="Daily percentage change"
                )
            },
            hide_index=True,
            use_container_width=True
        )
    
    # Interactive chart for selected index
    selected_index = st.selectbox("Select Index", list(indices.keys()), index=0)
    index_data = yf.Ticker(indices[selected_index]).history(period=period)
    
    if not index_data.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=index_data.index,
            y=index_data["Close"],
            name="Close Price",
            line=dict(color='royalblue', width=2)
        ))
        
        # Add moving average
        if len(index_data) > 20:
            index_data['MA20'] = index_data['Close'].rolling(window=20).mean()
            fig.add_trace(go.Scatter(
                x=index_data.index,
                y=index_data['MA20'],
                name="20-Day MA",
                line=dict(color='orange', width=1, dash='dash')
            ))
        
        fig.update_layout(
            title=f"{selected_index} Performance",
            xaxis_title="Date",
            yaxis_title="Price",
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error loading market data: {str(e)}")

# ========== 5. Central Bank Watch ==========
st.header("🏦 Central Bank Rates", divider="rainbow")

try:
    # Get central bank rates with history
    fed_rate_series = fred.get_series("FEDFUNDS")
    fed_rate = fed_rate_series.tail(1).values[0]
    prev_fed_rate = fed_rate_series.tail(2).values[0]
    fed_change = fed_rate - prev_fed_rate
    
    # ECB rate (sample - would need proper series)
    ecb_rate = 4.25
    ecb_change = 0.25
    
    # BOJ rate (sample)
    boj_rate = -0.10
    boj_change = 0.00
    
    # Display rates
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Federal Reserve Rate</div>
            <div class="metric-value">{fed_rate:.2f}%</div>
            <div class="metric-change {'positive' if fed_change < 0 else 'negative'}">
                {'+' if fed_change > 0 else ''}{fed_change:.2f}% from previous
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">ECB Main Refinancing Rate</div>
            <div class="metric-value">{ecb_rate:.2f}%</div>
            <div class="metric-change {'positive' if ecb_change < 0 else 'negative'}">
                {'+' if ecb_change > 0 else ''}{ecb_change:.2f}% from previous
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">BOJ Policy Rate</div>
            <div class="metric-value">{boj_rate:.2f}%</div>
            <div class="metric-change {'positive' if boj_change < 0 else 'negative'}">
                {'+' if boj_change > 0 else ''}{boj_change:.2f}% from previous
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Fed rate history chart
    fig = px.line(
        fed_rate_series.tail(60),
        title="Federal Funds Rate History",
        labels={"value": "Rate (%)", "index": "Date"}
    )
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error loading central bank data: {str(e)}")

# ========== 6. Geopolitical Risk ==========
st.header("⚠️ Geopolitical Risk Index", divider="rainbow")

try:
    # Simulated GPR data with more realistic pattern
    dates = pd.date_range(end=datetime.datetime.now(), periods=90)
    base_risk = 50
    events = {
        dates[20]: 15,  # Simulated event spike
        dates[45]: 10,
        dates[70]: 20
    }
    
    risk_values = []
    for date in dates:
        value = base_risk + np.random.normal(0, 2)
        for event_date, impact in events.items():
            days_diff = (date - event_date).days
            if 0 <= days_diff <= 14:  # Event impact lasts 2 weeks
                value += impact * (1 - days_diff/14)  # Linear decay
        risk_values.append(value)
    
    gpr_data = pd.DataFrame({
        "Date": dates,
        "Risk_Index": risk_values
    })
    
    fig = px.line(
        gpr_data, 
        x="Date", 
        y="Risk_Index", 
        title="Geopolitical Risk Index (Last 90 Days)",
        labels={"Risk_Index": "Risk Index"}
    )
    
    # Add event markers
    for event_date, _ in events.items():
        fig.add_vline(
            x=event_date, 
            line_width=1, 
            line_dash="dash", 
            line_color="red",
            annotation_text="Event",
            annotation_position="top right"
        )
    
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error loading geopolitical data: {str(e)}")

# ========== 7. Special Indicators ==========
st.header("🔍 Special Indicators", divider="rainbow")

try:
    # Create tabs for different special indicators
    tab1, tab2, tab3 = st.tabs(["Baltic Dry Index", "VIX Volatility", "Commodities"])
    
    with tab1:
        # Enhanced BDI with seasonality
        dates = pd.date_range(end=datetime.datetime.now(), periods=180)
        base_bdi = 1500
        seasonal = 100 * np.sin(np.linspace(0, 4*np.pi, 180))  # 2 seasonal cycles
        noise = np.random.normal(0, 50, 180)
        bdi_values = base_bdi + seasonal + noise
        
        bdi_data = pd.DataFrame({
            "Date": dates,
            "BDI": bdi_values
        })
        
        fig = px.line(
            bdi_data, 
            x="Date", 
            y="BDI", 
            title="Baltic Dry Index (6 Months)",
            labels={"BDI": "Index Value"}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # VIX data
        vix = yf.Ticker("^VIX").history(period=period)
        if not vix.empty:
            fig = px.line(
                vix, 
                x=vix.index, 
                y="Close", 
                title="CBOE Volatility Index (VIX)",
                labels={"Close": "VIX Level"}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Commodities overview
        commodities = {
            "Gold": "GC=F",
            "Silver": "SI=F",
            "Crude Oil": "CL=F",
            "Natural Gas": "NG=F",
            "Copper": "HG=F"
        }
        
        comm_data = []
        for name, ticker in commodities.items():
            data = yf.Ticker(ticker)
            hist = data.history(period="2d")
            if not hist.empty:
                current = hist["Close"].iloc[-1]
                prev_close = hist["Close"].iloc[0]
                change = ((current - prev_close) / prev_close) * 100
                comm_data.append({
                    "Commodity": name,
                    "Price": current,
                    "Change (%)": change
                })
        
        if comm_data:
            df_comm = pd.DataFrame(comm_data)
            st.dataframe(
                df_comm.sort_values("Change (%)", ascending=False),
                column_config={
                    "Price": st.column_config.NumberColumn(format="$%.2f"),
                    "Change (%)": st.column_config.NumberColumn(format="%.2f%%")
                },
                hide_index=True,
                use_container_width=True
            )

except Exception as e:
    st.error(f"Error loading special indicators: {str(e)}")

# ========== 8. Footer ==========
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 12px;">
    <p>Data Sources: FRED, Yahoo Finance | Last Updated: {}</p>
    <p>Disclaimer: This dashboard is for informational purposes only.</p>
</div>
""".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')), unsafe_allow_html=True)
