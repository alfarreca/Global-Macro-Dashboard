import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import plotly.express as px

st.set_page_config(page_title="Track the Markets: Winners & Losers", layout="wide")

# ----------------------- DATA SETUP -----------------------
DATA = [
    # Name, Yahoo Symbol, Type
    ("S&P 500", "^GSPC", "Index"),
    ("Nasdaq Composite", "^IXIC", "Index"),
    ("Nasdaq-100", "^NDX", "Index"),
    ("S&P 500 Information Tech", "XLK", "ETF"),
    ("S&P 500 Communications Services", "XLC", "ETF"),
    ("S&P 500 Industrials", "XLI", "ETF"),
    ("S&P 500 Consumer Discr", "XLY", "ETF"),
    ("S&P 500 Financials", "XLF", "ETF"),
    ("S&P 500 Health Care", "XLV", "ETF"),
    ("S&P 500 Utilities", "XLU", "ETF"),
    ("S&P 500 Materials", "XLB", "ETF"),
    ("S&P 500 Energy", "XLE", "ETF"),
    ("S&P 500 Consumer Staples", "XLP", "ETF"),
    ("Russell 2000", "^RUT", "Index"),
    ("Dow Jones Industrial Avg", "^DJI", "Index"),
    ("Nikkei 225", "^N225", "Index"),
    ("DAX", "^GDAXI", "Index"),
    ("FTSE 100", "^FTSE", "Index"),
    ("Hang Seng", "^HSI", "Index"),
    ("Shanghai Composite", "000001.SS", "Index"),
    ("Euro STOXX 50", "^STOXX50E", "Index"),
    ("IBEX 35", "^IBEX", "Index"),
    ("Bovespa Index", "^BVSP", "Index"),
    ("Sensex", "^BSESN", "Index"),
    ("Kospi Composite", "^KS11", "Index"),
    ("S&P/TSX Comp", "^GSPTSE", "Index"),
    ("Tel Aviv 35", "^TA35", "Index"),
    ("Bloomberg Commodity Index", "BCOM", "Index"),
    # Commodities
    ("Gold", "GC=F", "Commodity"),
    ("Silver", "SI=F", "Commodity"),
    ("Platinum", "PL=F", "Commodity"),
    ("Cattle", "LE=F", "Commodity"),
    ("Lean Hogs", "HE=F", "Commodity"),
    ("Cocoa", "CC=F", "Commodity"),
    ("Corn", "ZC=F", "Commodity"),
    ("Wheat", "ZW=F", "Commodity"),
    ("Soybeans", "ZS=F", "Commodity"),
    ("Coffee", "KC=F", "Commodity"),
    ("Sugar", "SB=F", "Commodity"),
    ("Natural Gas", "NG=F", "Commodity"),
    ("Crude Oil", "CL=F", "Commodity"),
    ("Orange Juice", "OJ=F", "Commodity"),
    # Currencies (vs USD)
    ("Euro", "EURUSD=X", "Currency"),
    ("Yen", "JPYUSD=X", "Currency"),
    ("Pound Sterling", "GBPUSD=X", "Currency"),
    ("Canadian Dollar", "CADUSD=X", "Currency"),
    ("Swiss Franc", "CHFUSD=X", "Currency"),
    ("Australian Dollar", "AUDUSD=X", "Currency"),
    ("New Zealand Dollar", "NZDUSD=X", "Currency"),
    ("South African Rand", "ZARUSD=X", "Currency"),
    ("Israeli Shekel", "ILSUSD=X", "Currency"),
    ("Polish Zloty", "PLNUSD=X", "Currency"),
    ("Czech Koruna", "CZKUSD=X", "Currency"),
    ("Brazilian Real", "BRLUSD=X", "Currency"),
    ("Indian Rupee", "INRUSD=X", "Currency"),
    ("Russian Ruble", "RUBUSD=X", "Currency"),
    ("Turkish Lira", "TRYUSD=X", "Currency"),
    ("Hungarian Forint", "HUFUSD=X", "Currency"),
    ("Icelandic Krona", "ISKUSD=X", "Currency"),
    ("Danish Krone", "DKKUSD=X", "Currency"),
    ("Norwegian Krone", "NOKUSD=X", "Currency"),
    ("Chilean Peso", "CLPUSD=X", "Currency"),
    ("Argentine Peso", "ARSUSD=X", "Currency"),
    ("Mexican Peso", "MXNUSD=X", "Currency"),
    ("Singapore Dollar", "SGDUSD=X", "Currency"),
    ("Romanian Leu", "RONUSD=X", "Currency"),
    ("Thai Baht", "THBUSD=X", "Currency"),
    ("Indonesian Rupiah", "IDRUSD=X", "Currency"),
    ("Ukrainian Hryvnia", "UAHUSD=X", "Currency"),
    ("Kuwaiti Dinar", "KWDUSD=X", "Currency"),
]

df = pd.DataFrame(DATA, columns=["Name", "Symbol", "Type"])

# ----------------------- STREAMLIT UI -----------------------
st.title("Track the Markets: Winners & Losers (Yahoo Finance, Last Quarter)")

period_months = st.selectbox("Performance period (months):", [3, 6, 12], index=0)
period_days = period_months * 21  # Approx trading days per month

def get_pct_change(symbol, period_days):
    try:
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=int(period_days * 1.5))  # Buffer for weekends/holidays
        data = yf.download(symbol, start=start, end=end, progress=False)
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
bar_colors = chart_df["Type"].map(color_map)

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
