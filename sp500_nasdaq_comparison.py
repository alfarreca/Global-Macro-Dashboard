import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time
import random

st.title('Global Market Index Comparison')

# Sidebar controls
with st.sidebar:
    st.header('Settings')
    st.subheader('Show Indices:')
    show_sp500 = st.toggle('S&P 500', value=True)
    show_nasdaq = st.toggle('NASDAQ', value=True)
    show_russell = st.toggle('Russell 2000', value=True)
    show_dax = st.toggle('DAX', value=True)
    normalize = st.checkbox('Normalize to 100 at start date', value=True)
    show_metrics = st.checkbox('Show performance metrics', value=True)

# Map for sidebar toggles and tickers
INDEXES = [
    ("S&P 500", "^GSPC", show_sp500),
    ("NASDAQ", "^IXIC", show_nasdaq),
    ("Russell 2000", "^RUT", show_russell),
    ("DAX", "^GDAXI", show_dax),
]
COLOR_MAP = {
    'S&P 500': '#1f77b4',
    'NASDAQ': '#2ca02c',
    'Russell 2000': '#d62728',
    'DAX': '#9467bd'
}

def fetch_index_data(ticker, start_date, end_date, max_retries=3):
    for attempt in range(max_retries):
        try:
            time.sleep(random.uniform(0.5, 1.5))
            data = yf.Ticker(ticker).history(
                start=start_date, end=end_date,
                interval="1d", auto_adjust=True
            )['Close']
            if not data.empty:
                return data
        except Exception:
            if attempt == max_retries - 1:
                st.warning(f"Failed to fetch data for {ticker} after {max_retries} attempts")
            continue
    return pd.Series(dtype='float64')

@st.cache_data(ttl=3*3600, show_spinner=False)
def load_data(selected_indexes, time_period):
    end_date = datetime.today()
    periods = {
        '3 Months': end_date - timedelta(days=90),
        '6 Months': end_date - timedelta(days=180),
        '1 Year': end_date - timedelta(days=365),
        '2 Years': end_date - timedelta(days=2*365)
    }
    start_date = periods.get(time_period, periods['2 Years'])

    data = {}
    for name, ticker, is_selected in selected_indexes:
        if is_selected:
            data[name] = fetch_index_data(ticker, start_date, end_date)
    if not data:
        return pd.DataFrame()  # No index selected
    df = pd.DataFrame(data).dropna()
    return df

def display_tab_content(time_period, tab, selected_indexes, normalize, show_metrics):
    with tab:
        with st.spinner(f'Loading {time_period} data...'):
            df = load_data(selected_indexes, time_period)
        if not df.empty:
            # Only show columns that were selected
            visible_cols = [name for name, _, is_sel in selected_indexes if is_sel and name in df.columns]
            df = df[visible_cols]

            if df.empty:
                tab.warning("No data for the selected indices in this time period.")
                return

            if normalize:
                df = (df / df.iloc[0]) * 100
            fig = px.line(df,
                          x=df.index,
                          y=df.columns,
                          title=f'Market Index Performance ({time_period})',
                          labels={'value': 'Normalized Value' if normalize else 'Index Value'},
                          color_discrete_map=COLOR_MAP)
            fig.update_layout(
                hovermode='x unified',
                legend_title_text='Index',
                yaxis_title='Normalized Value (Base 100)' if normalize else 'Index Value'
            )
            tab.plotly_chart(fig, use_container_width=True)
            if show_metrics and len(df) > 1:
                tab.subheader('Performance Metrics')
                start_values = df.iloc[0]
                end_values = df.iloc[-1]
                returns = ((end_values - start_values) / start_values) * 100
                days = (df.index[-1] - df.index[0]).days
                years = days / 365.25 if days > 0 else 1
                annualized_returns = ((end_values / start_values) ** (1/years) - 1) * 100
                daily_returns = df.pct_change().dropna()
                volatility = daily_returns.std() * (252 ** 0.5) * 100
                metrics_df = pd.DataFrame({
                    'Total Return (%)': returns.round(2),
                    'Annualized Return (%)': annualized_returns.round(2),
                    'Annualized Volatility (%)': volatility.round(2)
                })
                tab.dataframe(metrics_df.style.format("{:.2f}"), use_container_width=True)
                if len(df.columns) > 1:
                    tab.subheader('Correlation Matrix')
                    correlation_matrix = daily_returns.corr()
                    tab.dataframe(correlation_matrix.style.format("{:.2f}"), use_container_width=True)
        else:
            tab.error("Data loading failed or no indices selected. Please try:")
            tab.markdown("""
            1. Refresh the page  
            2. Select more indices  
            3. Try a different time period  
            4. Wait a few minutes if Yahoo Finance is rate limiting  
            """)

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["2 Years", "1 Year", "6 Months", "3 Months"])

display_tab_content("2 Years", tab1, INDEXES, normalize, show_metrics)
display_tab_content("1 Year", tab2, INDEXES, normalize, show_metrics)
display_tab_content("6 Months", tab3, INDEXES, normalize, show_metrics)
display_tab_content("3 Months", tab4, INDEXES, normalize, show_metrics)

st.markdown("""
### Data Notes
- All prices are closing values
- Normalization resets all indices to 100 at the start date
- Data may have slight discrepancies with official sources
- Russell 2000 data may have more gaps than other indices

### Recommended Setup
For best results:
- Select 2-3 indices at a time
- Try 1 Year or 2 Years time periods first
- Refresh if data doesn't load initially
""")
