import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import plotly.express as px

st.set_page_config(page_title="Track the Markets: Winners & Losers", layout="wide")

# ----------------------- DATA SETUP -----------------------
DATA = [
    # Try with just 5 for debugging, then expand!
    ("S&P 500", "^GSPC", "Index"),
    ("Nasdaq Composite", "^IXIC", "Index"),
    ("Gold", "GC=F", "Commodity"),
    ("EUR/USD", "EURUSD=X", "Currency"),
    ("Dow Jones", "^DJI", "Index"),
    # Uncomment more after working!
    # ... (rest of your DATA list)
]

df = pd.DataFrame(DATA, columns=["Name", "Symbol", "Type"])

st.title("Track the Markets: Winners & Losers (Yahoo Finance, Last Quarter)")

period_months = st.selectbox("Performance period (months):", [3, 6, 12], index=0)
period_days = period_months * 21  # Approx trading days per month

def get_pct_change(symbol, period_days):
    try:
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=int(period_days * 1.5))  # Buffer for weekends/holidays
        data = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=True)
        if len(data) < 2:
            return None
        first = data['Adj Close'].iloc[0]
        last = data['Adj Close'].iloc[-1]
        return ((last - first) / first) * 100
    except Exception:
        return None

@st.cache_data(ttl=3600, show_spinner=True)
def build_results(df, period_days):
    results = []
    for _, row in df.iterrows():
        pct = get_pct_change(row["Symbol"], period_days)
        results.append(pct)
    return results

with st.spinner("Fetching latest prices and calculating performance..."):
    df["% Change"] = build_results(df, period_days)

# --- Debug output for missing data ---
failed = df[df["% Change"].isnull()]
if not failed.empty:
    st.warning(f"Could not fetch data for {len(failed)} out of {len(df)} tickers.")
    st.write(failed[["Name", "Symbol", "Type"]])
else:
    st.success("All tickers loaded successfully.")

show_types = st.multiselect(
    "Select types to show:",
    options=["Index", "ETF", "Commodity", "Currency"],
    default=["Index", "ETF", "Commodity", "Currency"]
)

chart_df = df[df["Type"].isin(show_types) & df["% Change"].notnull()].sort_values("% Change", ascending=False)
chart_df.reset_index(drop=True, inplace=True)

color_map = {
    "Index": "#2196f3",
    "ETF": "#bdbdbd",
    "Commodity": "#757575",
    "Currency": "#43a047"
}

fig = px.bar(
    chart_df,
    x="% Change",
    y="Name",
    orientation="h",
    color="Type",
    color_discrete_map=color_map,
    text="Symbol",
    height=max(600, 20 * len(chart_df))
)

fig.update_layout(
    showlegend=True,
    yaxis=dict(tickfont=dict(size=11)),
    xaxis_title=f"% Change (last {period_months} months)",
    yaxis_title="",
    margin=dict(l=180, r=30, t=40, b=40)
)
fig.update_traces(textposition='outside', textfont=dict(size=10))

st.plotly_chart(fig, use_container_width=True)
st.dataframe(chart_df[["Name", "Symbol", "Type", "% Change"]], use_container_width=True)
