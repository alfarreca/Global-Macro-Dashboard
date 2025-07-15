
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fredapi import Fred
import yfinance as yf

st.set_page_config(layout="wide")
st.title("📉 Inflation vs Interest Rates (US, Eurozone, Japan)")

# User inputs API key
fred_api_key = st.text_input("a79018b53e3085363528cf148b358708", type="password")

if fred_api_key:
    fred = Fred(api_key=fred_api_key)

    # --- US ---
    st.subheader("🇺🇸 United States")
    us_cpi = fred.get_series("CPIAUCSL")
    us_rate = fred.get_series("GS10")
    df_us = pd.DataFrame({"US_CPI": us_cpi, "US_10Y": us_rate}).dropna()
    df_us = df_us.loc["2010-01-01":]
    df_us["Inflation_YoY"] = df_us["US_CPI"].pct_change(12) * 100

    fig_us = go.Figure()
    fig_us.add_trace(go.Scatter(x=df_us.index, y=df_us["Inflation_YoY"],
                                name="YoY Inflation (%)", line=dict(color="red")))
    fig_us.add_trace(go.Scatter(x=df_us.index, y=df_us["US_10Y"],
                                name="10Y Treasury Yield (%)", line=dict(color="blue")))
    fig_us.add_trace(go.Scatter(x=df_us.index, y=[2]*len(df_us),
                                name="2% Target", line=dict(color="gray", dash="dot")))
    fig_us.update_layout(title="US: Inflation vs Interest Rate", xaxis_title="Date", yaxis_title="Percentage")
    st.plotly_chart(fig_us, use_container_width=True)

    # --- Eurozone ---
    st.subheader("🇪🇺 Eurozone")
    eu_cpi = fred.get_series("CP0000EZ19M086NEST")
    eu_rate = yf.download("^TNX", start="2010-01-01", interval="1mo")["Adj Close"] / 10
    df_eu = pd.DataFrame({"EZ_CPI": eu_cpi}).dropna()
    df_eu["EZ_Inflation"] = df_eu["EZ_CPI"].pct_change(12) * 100
    df_eu["US_Yield_Proxy"] = eu_rate
    df_eu = df_eu.dropna()

    fig_eu = go.Figure()
    fig_eu.add_trace(go.Scatter(x=df_eu.index, y=df_eu["EZ_Inflation"],
                                name="EZ Inflation YoY (%)", line=dict(color="orange")))
    fig_eu.add_trace(go.Scatter(x=df_eu.index, y=df_eu["US_Yield_Proxy"],
                                name="US 10Y Yield Proxy (%)", line=dict(color="blue")))
    fig_eu.add_trace(go.Scatter(x=df_eu.index, y=[2]*len(df_eu),
                                name="2% Target", line=dict(color="gray", dash="dot")))
    fig_eu.update_layout(title="Eurozone: Inflation vs US Yield Proxy", xaxis_title="Date", yaxis_title="Percentage")
    st.plotly_chart(fig_eu, use_container_width=True)

    # --- Japan ---
    st.subheader("🇯🇵 Japan")
    jp_cpi = fred.get_series("JPNCPIALLMINMEI")
    jp_rate = fred.get_series("IR3TIB01JPM156N")
    df_jp = pd.DataFrame({"JP_CPI": jp_cpi, "JP_3M": jp_rate}).dropna()
    df_jp = df_jp.loc["2010-01-01":]
    df_jp["JP_Inflation"] = df_jp["JP_CPI"].pct_change(12) * 100

    fig_jp = go.Figure()
    fig_jp.add_trace(go.Scatter(x=df_jp.index, y=df_jp["JP_Inflation"],
                                name="JP Inflation YoY (%)", line=dict(color="green")))
    fig_jp.add_trace(go.Scatter(x=df_jp.index, y=df_jp["JP_3M"],
                                name="JP 3M Rate (%)", line=dict(color="blue")))
    fig_jp.add_trace(go.Scatter(x=df_jp.index, y=[2]*len(df_jp),
                                name="2% Target", line=dict(color="gray", dash="dot")))
    fig_jp.update_layout(title="Japan: Inflation vs Interest Rate", xaxis_title="Date", yaxis_title="Percentage")
    st.plotly_chart(fig_jp, use_container_width=True)
