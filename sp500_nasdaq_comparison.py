import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.title('U.S. & European Market Index Comparison')

with st.sidebar:
    st.header('Settings')
    st.subheader('Show Indices:')
    show_sp500 = st.toggle('S&P 500', value=True)
    show_nasdaq = st.toggle('NASDAQ', value=True)
    show_russell = st.toggle('Russell 2000', value=True)
    show_dax = st.toggle('DAX', value=False)
    normalize = st.checkbox('Normalize to 100 at start date', value=True)
    show_metrics = st.checkbox('Show performance metrics', value=True)

@st.cache_data(ttl=3600)
def load_data(time_period, show_sp500, show_nasdaq, show_russell, show_dax):
    end_date = datetime.today()
    if time_period == '3 Months':
        start_date = end_date - timedelta(days=90)
    elif time_period == '6 Months':
        start_date = end_date - timedelta(days=180)
    elif time_period == '1 Year':
        start_date = end_date - timedelta(days=365)
    elif time_period == '2 Years':
        start_date = end_date - timedelta(days=365*2)
    else:
        start_date = end_date - timedelta(days=365)
    try:
        data = {}
        if show_sp500:
            data['S&P 500'] = yf.Ticker("^GSPC").history(start=start_date, end=end_date)['Close']
        if show_nasdaq:
            data['NASDAQ'] = yf.Ticker("^IXIC").history(start=start_date, end=end_date)['Close']
        if show_russell:
            data['Russell 2000'] = yf.Ticker("^RUT").history(start=start_date, end=end_date)['Close']
        if show_dax:
            data['DAX'] = yf.Ticker("^GDAXI").history(start=start_date, end=end_date)['Close']
        df = pd.DataFrame(data)
        df = df.dropna(how='all')  # Only drop rows where all indices are missing
        return df, data
    except Exception as e:
        st.error(f"Error in data loading: {str(e)}")
        return pd.DataFrame(), {}

def robust_normalize(df):
    """Normalize each column by its own first valid value."""
    df_norm = df.copy()
    for col in df_norm.columns:
        first_valid = df_norm[col].first_valid_index()
        if first_valid is not None and df_norm[col][first_valid] != 0:
            df_norm[col] = (df_norm[col] / df_norm[col][first_valid]) * 100
    return df_norm

tab1, tab2, tab3, tab4 = st.tabs(["2 Years", "1 Year", "6 Months", "3 Months"])

def display_tab_content(time_period, tab, show_sp500, show_nasdaq, show_russell, show_dax):
    df, data_raw = load_data(time_period, show_sp500, show_nasdaq, show_russell, show_dax)

    # Sidebar debugging for DAX
    with st.sidebar:
        if show_dax:
            st.write("DAX data preview (first 5):", data_raw.get('DAX', 'Not requested'))
            if 'DAX' not in df.columns or df['DAX'].notna().sum() == 0:
                st.warning("No DAX data available for the selected time period. (Yahoo Finance may be missing DAX data.)")

    if not df.empty:
        if normalize:
            df = robust_normalize(df)
        color_map = {}
        if show_sp500: color_map['S&P 500'] = 'blue'
        if show_nasdaq: color_map['NASDAQ'] = 'green'
        if show_russell: color_map['Russell 2000'] = 'red'
        if show_dax: color_map['DAX'] = 'orange'
        available_indices = [col for col in color_map if col in df.columns and df[col].notna().sum() > 0]
        # Tab-level warning (for users)
        if show_dax and ('DAX' not in df.columns or df['DAX'].notna().sum() == 0):
            tab.warning("DAX was requested, but no DAX data is available for this time window.")

        if available_indices:
            fig = px.line(
                df,
                x=df.index,
                y=available_indices,
                title=f'U.S. & European Market Index Performance ({time_period})',
                labels={'value': 'Index Value', 'variable': 'Index'},
                color_discrete_map=color_map
            )
            fig.update_layout(
                hovermode='x unified',
                legend_title_text='Index'
            )
            tab.plotly_chart(fig, use_container_width=True)
        else:
            tab.info("No valid index data available for plotting.")

        if show_metrics and len(df) > 1 and available_indices:
            tab.subheader('Performance Metrics')
            start_values = df[available_indices].iloc[0]
            end_values = df[available_indices].iloc[-1]
            returns = ((end_values - start_values) / start_values) * 100
            days = (df.index[-1] - df.index[0]).days
            years = days / 365.25
            annualized_returns = ((end_values / start_values) ** (1 / years) - 1) * 100
            daily_returns = df[available_indices].pct_change().dropna()
            volatility = daily_returns.std() * (252 ** 0.5) * 100  # Annualized

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
    else:
        tab.info("No data available for the selected indices and time period.")

with tab1:
    display_tab_content("2 Years", tab1, show_sp500, show_nasdaq, show_russell, show_dax)
with tab2:
    display_tab_content("1 Year", tab2, show_sp500, show_nasdaq, show_russell, show_dax)
with tab3:
    display_tab_content("6 Months", tab3, show_sp500, show_nasdaq, show_russell, show_dax)
with tab4:
    display_tab_content("3 Months", tab4, show_sp500, show_nasdaq, show_russell, show_dax)

st.markdown("""
### About This App
- **S&P 500 (^GSPC)**: 500 large-cap U.S. companies across all sectors
- **NASDAQ (^IXIC)**: All stocks on NASDAQ exchange (tech-heavy)
- **Russell 2000 (^RUT)**: Small-cap U.S. companies
- **DAX (^GDAXI)**: 40 major German blue chip companies traded on the Frankfurt Stock Exchange
- Toggle switches control which indices appear in the charts
- Normalization adjusts all indices to start at 100 for easier comparison
- Data source: Yahoo Finance
""")
