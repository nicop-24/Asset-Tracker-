import yfinance as yf
import pandas as pd
import streamlit as st
import datetime

# Assets to track
tickers = {
    "FTSE 100": "^FTSE",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X"
}

st.title("📈 Asset Tracker (Intraday - 15 min)")

# Download last 5 days of 15-minute data
data = yf.download(
    list(tickers.values()), 
    period="5d", 
    interval="15m"
)['Adj Close']

# Rename columns with human-readable labels
data = data.rename(columns={v: k for k, v in tickers.items()})

# Show the latest prices
latest = data.tail(1).T
latest.columns = ["Latest Price"]
st.subheader("Latest Prices (15m delayed)")
st.dataframe(latest)

# Calculate % change over last close
if len(data) > 1:
    prev = data.iloc[-2]
    change = ((latest["Latest Price"] - prev) / prev * 100).round(2)
    changes = pd.DataFrame({"Daily % Change": change})
    st.subheader("Intraday % Change (vs previous 15m)")
    st.dataframe(changes)

# Plot line chart of intraday performance
st.subheader("Intraday Performance (last 5 days, 15m)")
st.line_chart(data)

# Show last update timestamp
st.caption(f"Data last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
