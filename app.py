def fetch_risk_sentiment(self):
    """Fetch risk and sentiment indicators"""
    now = datetime.datetime.now(TIME_ZONE)
    
    try:
        vix = yf.Ticker("^VIX").history(period="1d").iloc[0]["Close"]
    except Exception as e:
        st.error(f"Error fetching VIX: {str(e)}")
        vix = 20  # Default value
        
    return {
        "VIX": {
            "value": vix,
            "level": "High" if vix > 30 else "Elevated" if vix > 20 else "Normal",
            "history": yf.Ticker("^VIX").history(period="1mo")["Close"],
            "updated": now
        },
        "GPR": {
            "value": np.random.normal(50, 10),
            "level": "Elevated",
            "history": pd.Series(np.random.normal(50, 5, 30)),
            "updated": now
        },
        "Sentiment": {
            "value": np.random.uniform(0, 100),
            "level": "Neutral",
            "updated": now
        }
    }
