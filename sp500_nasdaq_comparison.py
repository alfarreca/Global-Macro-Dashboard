import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# App title
st.title('U.S. & European Market Index Comparison')

# Sidebar controls
with st.sidebar:
    st.header('Settings')
    
    # Index selection toggles
    st.subheader('Show Indices:')
    show_sp500 = st.toggle('S&P 500', value=True)
    show_nasdaq = st.toggle('NASDAQ', value=True)
    show_russell = st.toggle('Russell 2000', value=True)
    show_dax = st.toggle('DAX', value=False)
    
    # Normalization options
    normalize = st.checkbox('Normalize to 100 at start date', value=True)
    
    # Additional metrics
    show_metrics = st.checkbox('Show performance metrics', value=True)

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
        
        df = pd.DataFrame(data).dropna()
        return df

    except Exception as e:
        st.error(f"Error in data loading: {str(e)}")
        return pd.DataFrame()

# Create tabs for different time periods
tab1, tab2, tab3, tab4 = st.tabs(["2 Years", "1 Year", "6 Months", "3 Months"])

def display_tab_content(time_period, tab):
    df = load_data(time_period)
    
    if not df.empty:
        if normalize:
            df = (df / df.iloc[0]) * 100
        
        # Create color mapping only for visible indices
        color_map = {}
        if show_sp500:
            color_map['S&P 500'] = 'blue'
        if show_nasdaq:
            color_map['NASDAQ'] = 'green'
        if show_russell:
            color_map['Russell 2000'] = 'red'
        if show_dax:
            color_map['DAX'] = 'orange'

        # Create the plot
        fig = px.line(
            df, x=df.index, y=df.columns,
            title=f'U.S. & European Market Index Performance ({time_period})',
            labels={'value': 'Index Value', 'variable': 'Index'},
            color_discrete_map=color_map
        )
        fig.update_layout(
            hovermode='x unified',
            legend_title_text='Index'
        )
        tab.plotly_chart(fig, use_container_width=True)
        
        # Show performance metrics if requested
        if show_metrics and len(df) > 1:
            tab.subheader('Performance Metrics')
            
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
            
            tab.dataframe(metrics_df.style.format("{:.2f}"), use_container_width=True)
            
            # Correlation matrix (only if more than one index selected)
            if len(df.columns) > 1:
                tab.subheader('Correlation Matrix')
                correlation_matrix = daily_returns.corr()
                tab.dataframe(correlation_matrix.style.format("{:.2f}"), 
                              use_container_width=True)

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
### About This App
- **S&P 500 (^GSPC)**: 500 large-cap U.S. companies across all sectors
- **NASDAQ (^IXIC)**: All stocks on NASDAQ exchange (tech-heavy)
- **Russell 2000 (^RUT)**: Small-cap U.S. companies
- **DAX (^GDAXI)**: 40 major German blue chip companies traded on the Frankfurt Stock Exchange
- Toggle switches control which indices appear in the charts
- Normalization adjusts all indices to start at 100 for easier comparison
- Data source: Yahoo Finance
""")
