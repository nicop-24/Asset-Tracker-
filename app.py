import yfinance as yf
import pandas as pd
import streamlit as st
import datetime
import pytz
import altair as alt

# ================================
# Assets to track
# ================================
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
daily = yf.download(
    list(tickers.values()),
    period="6mo",
    interval="1d"
)["Close"]

# Rename columns for readability
daily = daily.rename(columns={v: k for k, v in tickers.items()})

# Handle incomplete sessions
latest_daily = daily.iloc[-1]
yesterday_daily = daily.iloc[-2]

today = datetime.date.today()
if today in daily.index:
    latest_daily = daily.iloc[-2]  # use yesterday’s value if today is partial
    yesterday_daily = daily.iloc[-3]

# Build comparison table
prices = pd.DataFrame({
    "Latest Price": latest_daily,
    "Prev Close": yesterday_daily
})
prices["% Change vs Prev Close"] = ((prices["Latest Price"] - prices["Prev Close"]) / prices["Prev Close"] * 100).round(2)

st.subheader("📈 Latest Prices and Daily Change")
st.dataframe(prices)

# ================================
# Part 2: Charts (Normalized, Robust)
# ================================
# Use only full-day closes
if today in daily.index:
    daily_chart = daily.iloc[:-1]
else:
    daily_chart = daily

# Drop tickers with no data
daily_chart = daily_chart.dropna(axis=1, how="all")

# Normalize all series to start at 100
normalized = (daily_chart / daily_chart.iloc[0]) * 100

# Reshape for Altair
normalized_reset = normalized.reset_index().melt("Date", var_name="Asset", value_name="Value")

# Warn if some tickers missing
missing = set(tickers.keys()) - set(normalized.columns)
if missing:
    st.warning(f"⚠️ No data available for: {', '.join(missing)}")

# Define dynamic y-axis range
y_max = normalized_reset["Value"].max()
y_upper = int(((y_max // 10) + 1) * 10)  # round up to nearest 10

# Equity indices chart
st.subheader("📊 Equity Indices (6 months, normalized to 100)")
equity_assets = ["FTSE 100", "S&P 500", "NASDAQ"]

equity_chart = alt.Chart(
    normalized_reset[normalized_reset["Asset"].isin(equity_assets)]
).mark_line().encode(
    x="Date:T",
    y=alt.Y("Value:Q", scale=alt.Scale(domain=[80, y_upper])),
    color="Asset:N",
    tooltip=["Date:T", "Asset:N", alt.Tooltip("Value:Q", format=".2f")]
).properties(width=700, height=400)

st.altair_chart(equity_chart, use_container_width=True)

# FX chart
st.subheader("💱 Currencies (6 months, normalized to 100)")
fx_assets = ["EUR/USD", "GBP/USD"]

fx_chart = alt.Chart(
    normalized_reset[normalized_reset["Asset"].isin(fx_assets)]
).mark_line().encode(
    x="Date:T",
    y=alt.Y("Value:Q", scale=alt.Scale(domain=[80, y_upper])),
    color="Asset:N",
    tooltip=["Date:T", "Asset:N", alt.Tooltip("Value:Q", format=".2f")]
).properties(width=700, height=400)

st.altair_chart(fx_chart, use_container_width=True)

# ================================
# Footer with UTC + London time
# ================================
utc_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
london_time = datetime.datetime.now(pytz.timezone("Europe/London")).strftime('%Y-%m-%d %H:%M:%S')

st.caption(f"Data last updated: {utc_time} (UTC) | {london_time} (London time)")
