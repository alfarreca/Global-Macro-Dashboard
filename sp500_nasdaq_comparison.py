import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time
import random

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

# Enhanced data fetching with retries
def fetch_index_data(ticker, start_date, end_date, max_retries=3):
    for attempt in range(max_retries):
        try:
            # Add random delay to prevent rate limiting
            time.sleep(random.uniform(0.5, 1.5))
            
            data = yf.Ticker(ticker).history(
                start=start_date,
                end=end_date,
                interval="1d",  # Daily data
                auto_adjust=True  # Use adjusted prices
            )['Close']
            
            if not data.empty:
                return data
                
        except Exception as e:
            if attempt == max_retries - 1:
                st.warning(f"Failed to fetch data for {ticker} after {max_retries} attempts")
            continue
    
    return pd.Series(dtype='float64')  # Return empty series if all retries fail

# Function to load data for a specific time period
@st.cache_data(ttl=3600*3)  # Cache for 3 hours
def load_data(time_period):
    end_date = datetime.today()
    start_date = {
        '3 Months': end_date - timedelta(days=90),
        '6 Months': end_date - timedelta(days=180),
        '1 Year': end_date - timedelta(days=365),
        '2 Years': end_date - timedelta(days=365*2)
    }.get(time_period, end_date - timedelta(days=365*2))
    
    data = {}
    tickers = {
        'S&P 500': "^GSPC",
        'NASDAQ': "^IXIC",
        'Russell 2000': "^RUT",
        'DAX': "^GDAXI"
    }
    
    for name, ticker in tickers.items():
        if (name == 'S&P 500' and show_sp500) or \
           (name == 'NASDAQ' and show_nasdaq) or \
           (name == 'Russell 2000' and show_russell) or \
           (name == 'DAX' and show_dax):
            data[name] = fetch_index_data(ticker, start_date, end_date)
    
    df = pd.DataFrame(data).dropna()
    
    # If empty, try with slightly expanded date range
    if df.empty and time_period in ['3 Months', '6 Months']:
        st.warning("No data found, trying with expanded date range...")
        new_start = start_date - timedelta(days=14)
        return load_data(time_period)  # Recursive retry
    
    return df

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
        
        # Only show selected indices
        visible_cols = [col for col in df.columns if col in color_map]
        df = df[visible_cols]
        
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
        tab.error("Data loading failed. Please try:")
        tab.markdown("""
        1. Refreshing the page
        2. Selecting fewer indices
        3. Trying a different time period
        4. Waiting a few minutes if Yahoo Finance is rate limiting
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
