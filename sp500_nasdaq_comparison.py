# Sidebar controls
with st.sidebar:
    st.header('Settings')
    
    # Index selection toggles
    st.subheader('Show Indices:')
    show_sp500 = st.toggle('S&P 500', value=True)
    show_nasdaq = st.toggle('NASDAQ', value=True)
    show_russell = st.toggle('Russell 2000', value=True)
    show_dax = st.toggle('DAX', value=False)   # <-- Add this line
    
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
    
    try:
        data = {}
        if show_sp500:
            data['S&P 500'] = yf.Ticker("^GSPC").history(start=start_date, end=end_date)['Close']
        if show_nasdaq:
            data['NASDAQ'] = yf.Ticker("^IXIC").history(start=start_date, end=end_date)['Close']
        if show_russell:
            data['Russell 2000'] = yf.Ticker("^RUT").history(start=start_date, end=end_date)['Close']
        if show_dax:
            data['DAX'] = yf.Ticker("^GDAXI").history(start=start_date, end=end_date)['Close'] # <-- Add this line
        
        df = pd.DataFrame(data).dropna()
        return df
    
    except Exception as e:
        st.error(f"Error in data loading: {str(e)}")
        return pd.DataFrame()

# In display_tab_content, add DAX to color mapping
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
            color_map['DAX'] = 'orange' # <-- Add this line

        # ... (rest of your function remains unchanged) ...

# In the About section, add a description for DAX
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
