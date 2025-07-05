import yfinance as yf
data = yf.download("^GSPC", period="6mo")
print(data.tail())
