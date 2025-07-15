# Fully updated inflation_plotly.py with robust FRED-only data fetching (no Yahoo)

updated_fred_only_script = """
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fredapi import Fred

st.set_page_config(layout="wide")
st.title("📉 Inflation vs Interest Rates (US, Eurozone, Japan)")

# ── API input ──
fred_api_key = st.text_input("a79018b53e3085363528cf148b358708", type="password")
if not fred_api_key:
    st.info("🔑 Please enter a FRED API key to load charts.")
    st.stop()

# ── Init FRED ──
try:
    fred = Fred(api_key=fred_api_key)
    fred.get_series("CPIAUCSL")  # test
except Exception as e:
    st.error(f"❌ FRED error: {e}")
    st.stop()

# ── Helper plot ──
def plot_dual(df, x, y1, y2, title, y1_title, y2_title, colors):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df[x], y=df[y1], name=y1_title, line=dict(color=colors[0])))
    fig.add_trace(go.Scatter(x=df[x], y=df[y2], name=y2_title, line=dict(color=colors[1])))
    fig.add_trace(go.Scatter(x=df[x], y=[2]*len(df), name="2% Target", line=dict(color="gray", dash="dot")))
    fig.update_layout(title=title, xaxis_title="Date", yaxis_title="Percent")
    return fig

# ── U.S. ──
st.subheader("🇺🇸 United States")
us_cpi = fred.get_series("CPIAUCSL")
us_rate = fred.get_series("GS10")
df_us = pd.DataFrame({"CPI": us_cpi, "Rate": us_rate}).dropna().loc["2010-01-01":]
df_us["Inflation_YoY"] = df_us["CPI"].pct_change(12) * 100
fig_us = plot_dual(df_us.reset_index(), "index", "Inflation_YoY", "Rate",
                   "US: YoY Inflation vs 10-Year Yield",
                   "Inflation (%)", "10-Year Yield (%)", ["red", "blue"])
st.plotly_chart(fig_us, use_container_width=True)

# ── Eurozone ──
st.subheader("🇪🇺 Eurozone")
ez_cpi = fred.get_series("CP0000EZ19M086NEST")  # HICP
us10 = fred.get_series("DGS10").resample("M").last() / 100
us10 = us10.reindex(ez_cpi.index, method="ffill")
df_ez = pd.DataFrame({"EZ_CPI": ez_cpi, "US10": us10}).dropna()
df_ez["EZ_Inflation"] = df_ez["EZ_CPI"].pct_change(12) * 100
fig_ez = plot_dual(df_ez.reset_index(), "index", "EZ_Inflation", "US10",
                   "Eurozone: Inflation vs US 10Y Yield",
                   "Inflation (%)", "US 10Y Yield (%)", ["orange", "blue"])
st.plotly_chart(fig_ez, use_container_width=True)

# ── Japan ──
st.subheader("🇯🇵 Japan")
jp_cpi = fred.get_series("JPNCPIALLMINMEI")
jp_rate = fred.get_series("IR3TIB01JPM156N")  # 3M interbank
df_jp = pd.DataFrame({"JP_CPI": jp_cpi, "JP_3M": jp_rate}).dropna().loc["2010-01-01":]
df_jp["JP_Inflation"] = df_jp["JP_CPI"].pct_change(12) * 100
fig_jp = plot_dual(df_jp.reset_index(), "index", "JP_Inflation", "JP_3M",
                   "Japan: Inflation vs 3-Month Rate",
                   "Inflation (%)", "3M Rate (%)", ["green", "blue"])
st.plotly_chart(fig_jp, use_container_width=True)
"""

# Save it
final_clean_path = "/mnt/data/inflation_plotly_fred_only.py"
with open(final_clean_path, "w") as f:
    f.write(updated_fred_only_script)

final_clean_path
