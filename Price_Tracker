import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import tempfile
import os

# App title
st.title('Ticker Price Change Tracker')

# Function to calculate weeks
def get_week_dates(weeks_back):
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=weeks_back)
    return start_date, end_date

# Function to get price change for a period
def get_price_change(ticker, start_date, end_date):
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if len(data) > 0:
            start_price = data['Close'].iloc[0]
            end_price = data['Close'].iloc[-1]
            return (end_price - start_price) / start_price * 100  # Percentage change
        else:
            return None
    except:
        return None

# File uploader
uploaded_file = st.file_uploader("Upload Excel file with tickers", type=['xlsx'])

if uploaded_file is not None:
    # Read the Excel file
    try:
        # Save uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        # Read the Excel file
        df_tickers = pd.read_excel(tmp_file_path)
        
        # Clean up the temporary file
        os.unlink(tmp_file_path)
        
        # Assume tickers are in the first column
        tickers = df_tickers.iloc[:, 0].dropna().astype(str).unique()
        
        if len(tickers) > 0:
            st.success(f"Found {len(tickers)} tickers in the uploaded file")
            
            # Button to fetch data
            if st.button('Fetch Price Changes'):
                with st.spinner('Fetching data from Yahoo Finance...'):
                    # Prepare results dataframe
                    results = pd.DataFrame(index=tickers)
                    
                    # Get data for each week
                    for week in range(1, 7):
                        start_date, end_date = get_week_dates(week)
                        week_label = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                        
                        # Get price changes for all tickers
                        changes = []
                        for ticker in tickers:
                            change = get_price_change(ticker, start_date, end_date)
                            changes.append(change)
                        
                        results[f'Week {week}'] = changes
                        results[f'Week {week} Dates'] = week_label
                    
                    # Display results
                    st.subheader('Weekly Price Changes (%)')
                    
                    # Create display dataframe with just the percentage changes
                    display_df = results[[f'Week {i}' for i in range(1, 7)]].copy()
                    display_df.columns = [f'Week {i}' for i in range(1, 7)]
                    
                    # Format percentages
                    styled_df = display_df.style.format("{:.2f}%", na_rep="N/A")
                    
                    # Show the table
                    st.dataframe(styled_df)
                    
                    # Show date ranges
                    st.caption("Date ranges for each week:")
                    for i in range(1, 7):
                        st.caption(f"Week {i}: {results[f'Week {i} Dates'].iloc[0]}")
                    
                    # Download button
                    csv = results.to_csv(index=True).encode('utf-8')
                    st.download_button(
                        "Download Results as CSV",
                        csv,
                        "ticker_price_changes.csv",
                        "text/csv",
                        key='download-csv'
                    )
        else:
            st.error("No tickers found in the uploaded file.")
            
    except Exception as e:
        st.error(f"Error reading the Excel file: {str(e)}")
else:
    st.info("Please upload an Excel file with tickers in the first column.")
