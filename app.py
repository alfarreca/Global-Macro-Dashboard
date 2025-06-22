
import streamlit as st
import pandas as pd
import yfinance as yf
from fredapi import Fred
import plotly.express as px
import datetime

# Config
st.set_page_config(layout="wide")
st.title("🌍 Global Macro Dashboard")

# API Keys (use Streamlit secrets for FRED)
fred = Fred(api_key=st.secrets["FRED_API_KEY"])

# ========== 1. Header (Time + Refresh) ==========
col1, col2 = st.columns(2)
with col1:
    st.write(f"**Last Updated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
with col2:
    if st.button("🔄 Refresh Data"):
        st.experimental_rerun()

# ========== 2. Global Overview ==========
st.header("🌐 Global Economic Snapshot")

# GDP Growth Map (sample static data)
gdp_data = pd.DataFrame({
    "Country": ["USA", "China", "Germany", "Japan", "India"],
    "GDP_Growth": [2.1, 5.3, 1.5, 1.0, 6.5]
})
fig = px.choropleth(
    gdp_data,
    locations="Country",
    locationmode="country names",
    color="GDP_Growth",
    title="Global GDP Growth Forecast (%)"
)
st.plotly_chart(fig, use_container_width=True)

# ========== 3. Economic Indicators ==========
st.header("📊 Economic Indicators by Region")

# US Data (FRED)
us_gdp = fred.get_series("GDPC1").tail(1).values[0]
us_inflation = fred.get_series("CPIAUCSL").pct_change(12).tail(1).values[0] * 100

col1, col2 = st.columns(2)
with col1:
    st.metric("US GDP (Latest QoQ)", f"${us_gdp:,.2f}B")
with col2:
    st.metric("US Inflation (YoY)", f"{us_inflation:.1f}%")

# ========== 4. Financial Markets ==========
st.header("📈 Financial Markets")

# Stock Markets (Yahoo Finance)
sp500 = yf.Ticker("^GSPC").history(period="1mo")
fig = px.line(sp500, x=sp500.index, y="Close", title="S&P 500")
st.plotly_chart(fig, use_container_width=True)

# ========== 5. Central Bank Watch ==========
st.header("🏦 Central Bank Rates")

fed_rate = fred.get_series("FEDFUNDS").tail(1).values[0]
st.metric("Fed Funds Rate", f"{fed_rate:.2f}%")

# ========== 6. Geopolitical Risk ==========
st.header("⚠️ Geopolitical Risk Index")

# Sample GPR data
gpr_data = pd.DataFrame({
    "Date": pd.date_range(end=datetime.datetime.now(), periods=30),
    "Risk_Index": [50, 55, 60, 58, 52, 49, 47, 50, 53, 56] * 3
})
fig = px.line(gpr_data, x="Date", y="Risk_Index", title="GPR Index")
st.plotly_chart(fig, use_container_width=True)

# ========== 7. Special Indicators ==========
st.header("🔍 Special Indicators")

# Baltic Dry Index (sample)
bdi_data = pd.DataFrame({
    "Date": pd.date_range(end=datetime.datetime.now(), periods=30),
    "BDI": [1500, 1520, 1550, 1530, 1510, 1490, 1480, 1470, 1460, 1450] * 3
})
fig = px.line(bdi_data, x="Date", y="BDI", title="Baltic Dry Index (Shipping Costs)")
st.plotly_chart(fig, use_container_width=True)
