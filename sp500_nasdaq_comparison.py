import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time
import random
from pandas_datareader import data as pdr

# App title
st.title('Global Market Index Comparison')

# Sidebar controls
with st.sidebar:
    st.header('Settings')
    
    # Index selection toggles
    st.subheader('Show Indices:')
    show_sp500 = st.toggle('S&P 500', value=True)
    show_nasdaq = st.toggle('NASDAQ', value=True)
    show_russell = st.toggle('Russell 2000', value=True)
    show_dax = st.toggle('DAX', value=True)
    
    # Normalization options
    normalize = st.checkbox('Normalize to 100 at start date', value=True)
    
    # Additional metrics
    show_metrics = st.checkbox('Show performance metrics', value=True)

# Function to fetch data with multiple fallback methods
def fetch_index_data(ticker, start_date, end_date):
    methods = [
        lambda: yf.Ticker(ticker).history(start=start_date, end=end_date)['Close'],
        lambda: pdr.get_data_yahoo(ticker, start=start_date, end=end_date)['Close']
    ]
    
    for method in methods:
        try:
            data = method()
            if not data.empty:
                return data
        except:
            continue
    
    return pd.Series()  # Return empty series if all methods fail

# Function to load data for a specific time period
@st.cache_data(ttl=3600)
def load_data(time_period):
    end_date = datetime.today()
    
    if time_period == '3 Months':
        start_date = end_date - timedelta(days=90)
    elif time_period == '6 Months':
        start_date = end_date - timedelta(days=180)
    elif time_period == '1 Year':
        start_date = end_date - timedelta(days=365)
    elif time_period == '2 Years':
        start_date = end_date - timedelta(days=365*2)
    
    try:
        data = {}
        time.sleep(random.uniform(0.5, 1.5))  # Rate limiting protection
        
        if show_sp500:
            data['S&P 500'] = fetch_index_data("^GSPC", start_date, end_date)
        if show_nasdaq:
            data['NASDAQ'] = fetch_index_data("^IXIC", start_date, end_date)
        if show_russell:
            data['Russell 2000'] = fetch_index_data("^RUT", start_date, end_date)
        if show_dax:
            data['DAX'] = fetch_index_data("^GDAXI", start_date, end_date)
        
        df = pd.DataFrame(data).dropna()
        
        # If we have no data, try expanding the date range slightly
        if df.empty:
            start_date = start_date - timedelta(days=7)  # Try 1 week earlier
            return load_data(time_period)  # Recursively try again
            
        return df
    
    except Exception as e:
        st.error(f"Error in data loading: {str(e)}")
        return pd.DataFrame()

# Create tabs for different time periods
tab1, tab2, tab3, tab4 = st.tabs(["2 Years", "1 Year", "6 Months", "3 Months"])

def display_tab_content(time_period, tab):
    with st.spinner(f'Loading {time_period} data...'):
        df = load_data(time_period)
    
    if not df.empty:
        if normalize:
            df = (df / df.iloc[0]) * 100
        
        color_map = {
            'S&P 500': '#1f77b4',
            'NASDAQ': '#2ca02c',
            'Russell 2000': '#d62728',
            'DAX': '#9467bd'
        }
        
        visible_columns = [col for col in df.columns if col in color_map]
        df = df[visible_columns]
        
        fig = px.line(df, 
                    x=df.index, 
                    y=df.columns,
                    title=f'Market Index Performance ({time_period})',
                    labels={'value': 'Normalized Value' if normalize else 'Index Value'},
                    color_discrete_map=color_map)
        
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
            years = days / 365.25
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
                tab.dataframe(correlation_matrix.style.format("{:.2f}"), 
                            use_container_width=True)
    else:
        tab.error("Failed to load data. Possible solutions:")
        tab.markdown("""
        - Try again later (Yahoo Finance may be temporarily unavailable)
        - Select fewer indices
        - Try a different time period
        - Check your internet connection
        """)

# Display content for each tab
with tab1:
    display_tab_content("2 Years", tab1)

with tab2:
    display_tab_content("1 Year", tab2)

with tab3:
    display_tab_content("6 Months", tab3)

with tab4:
    display_tab_content("3 Months", tab4)

# Add some info
st.markdown("""
### Troubleshooting Guide
If you're not seeing data:
1. First, wait 1 minute and refresh the page
2. Try selecting fewer indices
3. Try a different time period
4. Check [Yahoo Finance status](https://finance.yahoo.com)

### Data Sources
- **S&P 500 (^GSPC)**: 500 large-cap U.S. companies
- **NASDAQ (^IXIC)**: Tech-heavy U.S. stocks
- **Russell 2000 (^RUT)**: Small-cap U.S. companies
- **DAX (^GDAXI)**: German blue-chip stocks
""")
