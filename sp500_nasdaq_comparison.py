import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# App title
st.title('S&P 500 vs NASDAQ Normalized Comparison')

# Sidebar controls
with st.sidebar:
    st.header('Settings')
    
    # Date range selection
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365*5)  # Default 5 years
    
    date_range = st.selectbox(
        'Time Period',
        options=['1 Month', '3 Months', '6 Months', '1 Year', '3 Years', '5 Years', '10 Years', 'Max'],
        index=4  # Default to 5 years
    )
    
    if date_range == '1 Month':
        start_date = end_date - timedelta(days=30)
    elif date_range == '3 Months':
        start_date = end_date - timedelta(days=90)
    elif date_range == '6 Months':
        start_date = end_date - timedelta(days=180)
    elif date_range == '1 Year':
        start_date = end_date - timedelta(days=365)
    elif date_range == '3 Years':
        start_date = end_date - timedelta(days=365*3)
    elif date_range == '5 Years':
        start_date = end_date - timedelta(days=365*5)
    elif date_range == '10 Years':
        start_date = end_date - timedelta(days=365*10)
    else:  # Max
        start_date = datetime(1970, 1, 1)
    
    # Normalization options
    normalize = st.checkbox('Normalize to 100 at start date', value=True)
    
    # Additional metrics
    show_metrics = st.checkbox('Show performance metrics', value=True)

# Download data
@st.cache_data(ttl=3600)  # Cache data for 1 hour
def load_data(start_date, end_date):
    sp500 = yf.download('^GSPC', start=start_date, end=end_date)['Close']
    nasdaq = yf.download('^IXIC', start=start_date, end=end_date)['Close']
    df = pd.DataFrame({'S&P 500': sp500, 'NASDAQ': nasdaq})
    df = df.dropna()
    return df

try:
    df = load_data(start_date, end_date)
    
    if normalize:
        # Normalize to 100 at start date
        df = (df / df.iloc[0]) * 100
    
    # Create the plot
    fig = px.line(df, 
                  x=df.index, 
                  y=df.columns,
                  title=f'S&P 500 vs NASDAQ Performance ({date_range})',
                  labels={'value': 'Index Value', 'variable': 'Index'},
                  color_discrete_map={'S&P 500': 'blue', 'NASDAQ': 'green'})
    
    fig.update_layout(hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)
    
    # Show performance metrics if requested
    if show_metrics and len(df) > 1:
        st.subheader('Performance Metrics')
        
        # Calculate metrics
        start_values = df.iloc[0]
        end_values = df.iloc[-1]
        returns = ((end_values - start_values) / start_values) * 100
        
        # Annualized return calculation
        days = (df.index[-1] - df.index[0]).days
        years = days / 365.25
        annualized_returns = ((end_values / start_values) ** (1/years) - 1) * 100
        
        # Volatility (standard deviation of daily returns)
        daily_returns = df.pct_change().dropna()
        volatility = daily_returns.std() * (252 ** 0.5) * 100  # Annualized
        
        # Create metrics DataFrame
        metrics_df = pd.DataFrame({
            'Total Return (%)': returns.round(2),
            'Annualized Return (%)': annualized_returns.round(2),
            'Annualized Volatility (%)': volatility.round(2)
        })
        
        st.dataframe(metrics_df.style.format("{:.2f}"), use_container_width=True)
        
        # Correlation
        correlation = daily_returns.corr().iloc[0,1]
        st.write(f"Daily Returns Correlation: {correlation:.2f}")
    
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("If the error persists, try reloading the app or checking your internet connection.")

# Add some info
st.markdown("""
### About This App
- **S&P 500 (^GSPC)**: Represents 500 large-cap U.S. companies across all sectors
- **NASDAQ (^IXIC)**: Tracks performance of all stocks listed on the NASDAQ, with heavy tech weighting
- Normalization adjusts both indices to start at 100 for easier comparison of relative performance
- Data source: Yahoo Finance
""")
