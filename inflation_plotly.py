import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fredapi import Fred
import yfinance as yf

st.set_page_config(layout="wide")
st.title("📉 Inflation vs Interest Rates (US, Eurozone, Japan)")

# ── FRED API key ────────────────────────────────────────────────────────────────
fred_api_key = st.text_input("a79018b53e3085363528cf148b358708", type="password")

if not fred_api_key:
    st.info("🔑 Please enter a FRED API key to load the charts.")
    st.stop()

# Validate key once to avoid hidden failures
try:
    fred = Fred(api_key=fred_api_key)
    _ = fred.get_series("CPIAUCSL")  # quick test call
except Exception as e:
    st.error(f"❌ FRED request failed. Check your API key.\n\n**Error:** {e}")
    st.stop()

# ── Helper to build a dual‑axis chart ───────────────────────────────────────────
def plot_dual(df, x, y1, y2, title, y1_title, y2_title, colors):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df[x], y=df[y1], name=y1_title, line=dict(color=colors[0])))
    fig.add_trace(go.Scatter(x=df[x], y=df[y2], name=y2_title, line=dict(color=colors[1])))
    fig.add_trace(go.Scatter(x=df[x], y=[2]*len(df), name="2 % Target",
                             line=dict(color="gray", dash="dot")))
    fig.update_layout(title=title, xaxis_title="Date", yaxis_title="Percent")
    return fig

# ── U.S. ────────────────────────────────────────────────────────────────────────
st.subheader("🇺🇸 United States")
us_cpi  = fred.get_series("CPIAUCSL")
us_rate = fred.get_series("GS10")           # 10‑year Treasury
df_us = (pd.DataFrame({"CPI": us_cpi, "Rate": us_rate})
         .dropna()
         .loc["2010-01-01":])
df_us["Inflation_YoY"] = df_us["CPI"].pct_change(12) * 100
fig_us = plot_dual(df_us.reset_index(), "index", "Inflation_YoY", "Rate",
                   "US: YoY Inflation vs 10‑Year Yield",
                   "Inflation (%)", "10‑Year Yield (%)",
                   ["red", "blue"])
st.plotly_chart(fig_us, use_container_width=True)

# ── Eurozone ────────────────────────────────────────────────────────────────────
st.subheader("🇪🇺 Eurozone")
ez_cpi  = fred.get_series("CP0000EZ19M086NEST")  # HICP
us10    = yf.download("^TNX", start="2010-01-01", interval="1mo")["Adj Close"]/10
df_ez = (pd.DataFrame({"CPI": ez_cpi, "US10": us10})
         .dropna())
df_ez["Inflation_YoY"] = df_ez["CPI"].pct_change(12) * 100
fig_ez = plot_dual(df_ez.reset_index(), "index", "Inflation_YoY", "US10",
                   "Eurozone: YoY Inflation vs US 10‑Year Yield (proxy)",
                   "Inflation (%)", "US 10‑Year Yield (%)",
                   ["orange", "blue"])
st.plotly_chart(fig_ez, use_container_width=True)

# ── Japan ───────────────────────────────────────────────────────────────────────
st.subheader("🇯🇵 Japan")
jp_cpi  = fred.get_series("JPNCPIALLMINMEI")
jp_rate = fred.get_series("IR3TIB01JPM156N")   # 3‑month interbank rate
df_jp = (pd.DataFrame({"CPI": jp_cpi, "Rate": jp_rate})
         .dropna()
         .loc["2010-01-01":])
df_jp["Inflation_YoY"] = df_jp["CPI"].pct_change(12) * 100
fig_jp = plot_dual(df_jp.reset_index(), "index", "Inflation_YoY", "Rate",
                   "Japan: YoY Inflation vs 3‑Month Rate",
                   "Inflation (%)", "3‑Month Rate (%)",
                   ["green", "blue"])
st.plotly_chart(fig_jp, use_container_width=True)
