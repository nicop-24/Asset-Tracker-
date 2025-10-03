import yfinance as yf
import pandas as pd
import streamlit as st
import datetime
import pytz

# Assets to track
tickers = {
    "FTSE 100": "^FTSE",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X"
}

st.title("📊 Asset Tracker Dashboard")

# ================================
# Part 1: Latest Prices (today vs yesterday)
# ================================
# Get daily closes (6 months, for yesterday and today if available)
daily = yf.download(
    list(tickers.values()),
    period="6mo",
    interval="1d"
)["Close"]

daily = daily.rename(columns={v: k for k, v in tickers.items()})

# Latest close we have (today or yesterday if today not yet reported)
latest_daily = daily.iloc[-1]
yesterday_daily = daily.iloc[-2]

# If today's date is in the index but it's incomplete (trading ongoing),
# then use yesterday's close as "last available"
today = datetime.date.today()
if today in daily.index:
    latest_daily = daily.iloc[-2]  # keep yesterday's value until full day is available
    yesterday_daily = daily.iloc[-3]

# Build table of current vs yesterday
prices = pd.DataFrame({
    "Latest Price": latest_daily,
    "Prev Close": yesterday_daily
})
prices["% Change vs Prev Close"] = ((prices["Latest Price"] - prices["Prev Close"]) / prices["Prev Close"] * 100).round(2)

st.subheader("📈 Latest Prices and Daily Change")
st.dataframe(prices)

# ================================
# Part 2: Charts (Normalized to 100)
# ================================
# Only chart up to yesterday's close
if today in daily.index:
    daily_chart = daily.iloc[:-1]
else:
    daily_chart = daily

# Normalize all series to start at 100
normalized = (daily_chart / daily_chart.iloc[0]) * 100

st.subheader("📊 Equity Indices (6 months, normalized to 100)")
st.line_chart(normalized[["FTSE 100", "S&P 500", "NASDAQ"]])

st.subheader("💱 Currencies (6 months, normalized to 100)")
st.line_chart(normalized[["EUR/USD", "GBP/USD"]])

# ================================
# Footer with UTC + London time
# ================================
utc_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
london_time = datetime.datetime.now(pytz.timezone("Europe/London")).strftime('%Y-%m-%d %H:%M:%S')

st.caption(f"Data last updated: {utc_time} (UTC) | {london_time} (London time)")
