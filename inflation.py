# Prepare a script that combines FRED and Yahoo Finance data for Streamlit app

streamlit_script = """
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fredapi import Fred
import yfinance as yf

st.set_page_config(layout="wide")
st.title("📉 Inflation vs Interest Rates (US, Eurozone, Japan)")

# User inputs API key
fred_api_key = st.text_input("a79018b53e3085363528cf148b358708", type="password")

if fred_api_key:
    fred = Fred(api_key=fred_api_key)

    st.markdown("## 📊 US Data")
    us_cpi = fred.get_series("CPIAUCSL")
    us_rate = fred.get_series("GS10")  # 10-year treasury

    df_us = pd.DataFrame({"US_CPI": us_cpi, "US_10Y": us_rate})
    df_us = df_us.dropna()
    df_us = df_us.loc["2010-01-01":]

    fig_us, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(df_us.index, df_us["US_CPI"].pct_change(12)*100, label="YoY Inflation (%)")
    ax1.plot(df_us.index, df_us["US_10Y"], label="10Y Treasury Yield (%)")
    ax1.axhline(2, color="gray", linestyle="--", label="2% Target")
    ax1.set_title("US: Inflation vs Interest Rate")
    ax1.legend()
    ax1.grid(True)
    st.pyplot(fig_us)

    st.markdown("## 📊 Eurozone Data")
    eu_cpi = fred.get_series("CP0000EZ19M086NEST")  # Eurozone HICP
    eu_rate = yf.download("^TNX", start="2010-01-01", interval="1mo")["Adj Close"] / 10

    df_eu = pd.DataFrame({"EZ_CPI": eu_cpi})
    df_eu["EZ_Inflation"] = df_eu["EZ_CPI"].pct_change(12) * 100
    df_eu["US_Yield_Proxy"] = eu_rate
    df_eu = df_eu.dropna()

    fig_eu, ax2 = plt.subplots(figsize=(10, 4))
    ax2.plot(df_eu.index, df_eu["EZ_Inflation"], label="EZ Inflation YoY (%)")
    ax2.plot(df_eu.index, df_eu["US_Yield_Proxy"], label="US 10Y Yield Proxy (%)")
    ax2.axhline(2, color="gray", linestyle="--", label="2% Target")
    ax2.set_title("Eurozone: Inflation vs US 10Y Proxy")
    ax2.legend()
    ax2.grid(True)
    st.pyplot(fig_eu)

    st.markdown("## 📊 Japan Data")
    jp_cpi = fred.get_series("JPNCPIALLMINMEI")  # Japan CPI
    jp_rate = fred.get_series("IR3TIB01JPM156N")  # Japan 3M Interbank Rate as proxy

    df_jp = pd.DataFrame({
        "JP_CPI": jp_cpi,
        "JP_3M": jp_rate
    }).dropna()
    df_jp["JP_Inflation"] = df_jp["JP_CPI"].pct_change(12) * 100
    df_jp = df_jp.loc["2010-01-01":]

    fig_jp, ax3 = plt.subplots(figsize=(10, 4))
    ax3.plot(df_jp.index, df_jp["JP_Inflation"], label="JP Inflation YoY (%)")
    ax3.plot(df_jp.index, df_jp["JP_3M"], label="JP 3M Rate (%)")
    ax3.axhline(2, color="gray", linestyle="--", label="2% Target")
    ax3.set_title("Japan: Inflation vs Interest Rate")
    ax3.legend()
    ax3.grid(True)
    st.pyplot(fig_jp)
"""

# Save it to a file for download
path = "/mnt/data/inflation_vs_interest_global.py"
with open(path, "w") as f:
    f.write(streamlit_script)

path
