import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# ========== CONFIGURATION ==========

INDEX_TICKERS = {
    'S&P 500': '^GSPC',
    'NASDAQ': '^IXIC',
    'Russell 2000': '^RUT',
    'DAX': '^GDAXI',
    # Add more indices as needed
}

TIMEFRAMES = {
    "2 Years": 365 * 2,
    "1 Year": 365,
    "6 Months": 180,
    "3 Months": 90,
    # Add more timeframes if desired
}

COLOR_MAP = {
    'S&P 500': 'blue',
    'NASDAQ': 'green',
    'Russell 2000': 'red',
    'DAX': 'orange',
    # Add more colors for new indices
}

st.title('Market Index Comparison Dashboard')

# ========== SIDEBAR ==========

with st.sidebar:
    st.header('Settings')
    st.subheader('Select Indices:')
    selected_indices = []
    for idx in INDEX_TICKERS:
        default = idx in ['S&P 500', 'NASDAQ', 'Russell 2000']
        if st.checkbox(idx, value=default):
            selected_indices.append(idx)
    normalize = st.checkbox('Normalize to 100 at start date', value=True)
    show_metrics = st.checkbox('Show performance metrics', value=True)

# ========== LOAD DATA WITH SPINNER AND ERROR HANDLING ==========

@st.cache_data(ttl=3600)
def load_master_data(selected_indices):
    if not selected_indices:
        return pd.DataFrame()
    end_date = datetime.today()
    max_days = max(TIMEFRAMES.values())
    start_date = end_date - timedelta(days=max_days)
    data = {}
    for name in selected_indices:
        ticker = INDEX_TICKERS[name]
        try:
            s = yf.Ticker(ticker).history(start=start_date, end=end_date)['Close']
            data[name] = s
        except Exception as e:
            st.warning(f"Could not fetch {name}: {e}")
    df = pd.DataFrame(data)
    if not df.empty:
        full_range = pd.date_range(df.index.min(), df.index.max(), freq='B')
        df = df.reindex(full_range)
        df = df.ffill().dropna(how='all')
    return df

try:
    with st.spinner("Loading index data from Yahoo Finance (this may take up to 30 seconds)..."):
        master_df = load_master_data(selected_indices)
    if master_df.empty and selected_indices:
        st.error("No data returned. Try with fewer indices or shorter timeframes.")
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# ========== TAB CONTENT FUNCTION ==========

def display_tab_content(days_back, tab, indices, normalize, show_metrics):
    if master_df.empty or not indices:
        tab.info("No data available. Please select at least one index.")
        return

    # Filter and slice to timeframe
    df = master_df[indices].copy()
    cutoff = df.index.max() - pd.Timedelta(days=days_back)
    df = df[df.index >= cutoff]

    # Normalize (only on available values)
    if normalize and not df.empty:
        for col in df.columns:
            first_valid = df[col].first_valid_index()
            if first_valid is not None and df[col][first_valid] != 0:
                df[col] = (df[col] / df[col][first_valid]) * 100

    # Warn about missing data per index
    missing_indices = [col for col in indices if df[col].isna().all()]
    if missing_indices:
        tab.warning(f"Data not available for: {', '.join(missing_indices)} in this period.")

    # Plot only indices with data (not all-NA)
    available_indices = [col for col in df.columns if df[col].notna().sum() > 0]
    if available_indices:
        color_map = {idx: COLOR_MAP.get(idx, None) for idx in available_indices}
        fig = px.line(
            df,
            x=df.index,
            y=available_indices,
            title=f'Market Index Performance ({days_back // 30 if days_back > 30 else days_back} {"Months" if days_back < 365 else "Years"})',
            labels={'value': 'Index Value', 'variable': 'Index'},
            color_discrete_map=color_map
        )
        fig.update_layout(hovermode='x unified', legend_title_text='Index')
        tab.plotly_chart(fig, use_container_width=True)
    else:
        tab.info("No data for the selected indices in this period.")

    # Performance Metrics (for available only)
    if show_metrics and len(df) > 1 and available_indices:
        tab.subheader('Performance Metrics')
        start_values = df[available_indices].iloc[0]
        end_values = df[available_indices].iloc[-1]
        returns = ((end_values - start_values) / start_values) * 100
        days = (df.index[-1] - df.index[0]).days
        years = days / 365.25 if days > 0 else 1
        annualized_returns = ((end_values / start_values) ** (1 / years) - 1) * 100 if years > 0 else None
        daily_returns = df[available_indices].pct_change().dropna()
        volatility = daily_returns.std() * (252 ** 0.5) * 100

        metrics_df = pd.DataFrame({
            'Total Return (%)': returns.round(2),
            'Annualized Return (%)': annualized_returns.round(2),
            'Annualized Volatility (%)': volatility.round(2)
        })
        tab.dataframe(metrics_df.style.format("{:.2f}"), use_container_width=True)

        if len(available_indices) > 1:
            tab.subheader('Correlation Matrix')
            correlation_matrix = daily_returns.corr()
            tab.dataframe(correlation_matrix.style.format("{:.2f}"), use_container_width=True)

# ========== TABS ==========

tabs = st.tabs(list(TIMEFRAMES.keys()))
for i, (label, days_back) in enumerate(TIMEFRAMES.items()):
    with tabs[i]:
        display_tab_content(days_back, tabs[i], selected_indices, normalize, show_metrics)

# ========== FOOTER ==========

st.markdown("""
### About This App
- Compare U.S. and European stock market indices across customizable timeframes
- **Indices:** S&P 500, NASDAQ, Russell 2000, DAX (add more as needed)
- **Features:** Performance normalization, return/volatility metrics, correlation matrix
- Data sourced from [Yahoo Finance](https://finance.yahoo.com)
""")
