import yfinance as yf
import pandas as pd
import streamlit as st
import datetime
import pytz
import altair as alt

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
daily = yf.download(
    list(tickers.values()),
    period="6mo",
    interval="1d"
)["Close"]

daily = daily.rename(columns={v: k for k, v in tickers.items()})

# Handle latest vs yesterday (adjust if today incomplete)
latest_daily = daily.iloc[-1]
yesterday_daily = daily.iloc[-2]

today = datetime.date.today()
if today in daily.index:
    latest_daily = daily.iloc[-2]
    yesterday_daily = daily.iloc[-3]

prices = pd.DataFrame({
    "Latest Price": latest_daily,
    "Prev Close": yesterday_daily
})
prices["% Change vs Prev Close"] = ((prices["Latest Price"] - prices["Prev Close"]) / prices["Prev Close"] * 100).round(2)

st.subheader("📈 Latest Prices and Daily Change")
st.dataframe(prices)

# ================================
# Part 2: Charts (Normalized & Zoomed)
# ================================
if today in daily.index:
    daily_chart = daily.iloc[:-1]
else:
    daily_chart = daily

normalized = (daily_chart / daily_chart.iloc[0]) * 100
norm_reset = normalized.reset_index().melt("Date", var_name="Asset", value_name="Value")

st.subheader("📊 Equity Indices (normalized to 100, zoomed 80–120)")
chart_equities = (
    alt.Chart(norm_reset[norm_reset["Asset"].isin(["FTSE 100", "S&P 500", "NASDAQ"])])
    .mark_line()
    .encode(
        x="Date:T",
        y=alt.Y("Value:Q", scale=alt.Scale(domain=[80, 120])),
        color="Asset:N",
        tooltip=["Date:T", "Asset:N", "Value:Q"]
    )
    .properties(width=700, height=400)
)
st.altair_chart(chart_equities, use_container_width=True)

st.subheader("💱 Currencies (normalized to 100, zoomed 80–120)")
chart_fx = (
    alt.Chart(norm_reset[norm_reset["Asset"].isin(["EUR/USD", "GBP/USD"])])
    .mark_line()
    .encode(
        x="Date:T",
        y=alt.Y("Value:Q", scale=alt.Scale(domain=[80, 120])),
        color="Asset:N",
        tooltip=["Date:T", "Asset:N", "Value:Q"]
    )
    .properties(width=700, height=400)
)
st.altair_chart(chart_fx, use_container_width=True)

# ================================
# Footer with UTC + London time
# ================================
utc_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
london_time = datetime.datetime.now(pytz.timezone("Europe/London")).strftime('%Y-%m-%d %H:%M:%S')

st.caption(f"Data last updated: {utc_time} (UTC) | {london_time} (London time)")
