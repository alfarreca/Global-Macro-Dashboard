import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Get last six months of DAX data
end_date = datetime.today()
start_date = end_date - timedelta(days=180)
dax = yf.Ticker("^GDAXI").history(start=start_date, end=end_date)['Close']

st.write("DAX Data (last 10 rows):")
st.write(dax.tail(10))
st.line_chart(dax)
