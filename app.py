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

st.title("📊 Asset Tracker Dashboard")

# ================================
# Part 1: Latest Prices (Intraday, 15m)
# ================================
intraday = yf.download(
    list(tickers.values()),
    period="5d",
    interval="15m"
)["Close"]

intraday = intraday.rename(columns={v: k for k, v in tickers.items()})

# Latest prices
latest = intraday.tail(1).T
latest.columns = ["Latest Price"]
st.subheader("📈 Latest Prices (15m delayed)")
st.dataframe(latest)

# % change vs previous 15m
if len(intraday) > 1:
    prev = intraday.iloc[-2]
    change = ((latest["Latest Price"] - prev) / prev * 100).round(2)
    changes = pd.DataFrame({"% Change (last 15m)": change})
    st.subheader("🔄 Intraday % Change")
    st.dataframe(changes)

# ================================
# Part 2: Charts (Daily closes, 6 months)
# ================================
daily = yf.download(
    list(tickers.values()),
    period="6mo",
    interval="1d"
)["Adj Close"]

daily = daily.rename(columns={v: k for k, v in tickers.items()})

st.subheader("📊 Equity Indices (6 months, daily closes)")
st.line_chart(daily[["FTSE 100", "S&P 500", "NASDAQ"]])

st.subheader("💱 Currencies (6 months, daily closes)")
st.line_chart(daily[["EUR/USD", "GBP/USD"]])

# ================================
# Footer
# ================================
st.caption(f"Data last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
