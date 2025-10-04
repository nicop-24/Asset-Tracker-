import yfinance as yf
import pandas as pd
import streamlit as st
import datetime
import pytz
import altair as alt

st.title("📊 Asset Tracker Dashboard")

# ==============================================================
# Primary tickers and fallback tickers
# ==============================================================
tickers_primary = {
    "FTSE 100": "^FTSE",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
}

tickers_fallback = {
    "S&P 500": "SPY",  # ETF proxy
    "NASDAQ": "QQQ",   # ETF proxy
}

# ==============================================================
# Step 1. Download data safely (with fallback)
# ==============================================================
st.caption("Fetching data from Yahoo Finance...")

data_frames = {}
for name, ticker in tickers_primary.items():
    try:
        df = yf.download(ticker, period="6mo", interval="1d")["Close"]
        if df.empty and name in tickers_fallback:
            # Try fallback if primary failed
            fallback_ticker = tickers_fallback[name]
            st.warning(f"⚠️ No data for {name} ({ticker}). Trying fallback: {fallback_ticker}")
            df = yf.download(fallback_ticker, period="6mo", interval="1d")["Close"]
        if not df.empty:
            df.name = name
            data_frames[name] = df
        else:
            st.warning(f"⚠️ Still no data for {name}. Skipping.")
    except Exception as e:
        st.warning(f"⚠️ Failed to load {name}: {e}")

# Display summary
st.write("✅ Data fetched per ticker:")
for name, df in data_frames.items():
    st.write(f"{name}: {len(df)} rows, from {df.index.min()} to {df.index.max()}")

# Stop if nothing loaded
if len(data_frames) == 0:
    st.error("No data could be fetched. Please check connection or tickers.")
    st.stop()

# Combine into one DataFrame
daily = pd.concat(data_frames.values(), axis=1)

# ==============================================================
# Step 2. Latest Prices (today vs yesterday)
# ==============================================================
today = datetime.date.today()
latest_daily = daily.iloc[-1]
yesterday_daily = daily.iloc[-2]

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

# ==============================================================
# Step 3. Charts (normalized)
# ==============================================================
# Trim incomplete day
if today in daily.index:
    daily_chart = daily.iloc[:-1]
else:
    daily_chart = daily

# Normalize to 100
normalized = (daily_chart / daily_chart.iloc[0]) * 100
normalized_reset = normalized.reset_index().melt("Date", var_name="Asset", value_name="Value")

# Dynamic y-axis
y_max = normalized_reset["Value"].max()
y_upper = int(((y_max // 10) + 1) * 10)

# ==============================================================
# Equity chart
# ==============================================================
st.subheader("📊 Equity Indices (6 months, normalized to 100)")
equity_assets = ["FTSE 100", "S&P 500", "NASDAQ"]
available_equities = [a for a in equity_assets if a in normalized.columns]

if len(available_equities) == 0:
    st.warning("No equity index data available.")
else:
    equity_chart = (
        alt.Chart(normalized_reset[normalized_reset["Asset"].isin(available_equities)])
        .mark_line()
        .encode(
            x="Date:T",
            y=alt.Y("Value:Q", scale=alt.Scale(domain=[80, y_upper])),
            color="Asset:N",
            tooltip=["Date:T", "Asset:N", "Value:Q"]
        )
        .properties(width=700, height=400)
    )
    st.altair_chart(equity_chart, use_container_width=True)

# ==============================================================
# FX chart
# ==============================================================
st.subheader("💱 Currencies (6 months, normalized to 100)")
fx_assets = ["EUR/USD", "GBP/USD"]
available_fx = [a for a in fx_assets if a in normalized.columns]

if len(available_fx) == 0:
    st.warning("No FX data available.")
else:
    fx_chart = (
        alt.Chart(normalized_reset[normalized_reset["Asset"].isin(available_fx)])
        .mark_line()
        .encode(
            x="Date:T",
            y=alt.Y("Value:Q", scale=alt.Scale(domain=[80, y_upper])),
            color="Asset:N",
            tooltip=["Date:T", "Asset:N", "Value:Q"]
        )
        .properties(width=700, height=400)
    )
    st.altair_chart(fx_chart, use_container_width=True)

# ==============================================================
# Footer
# ==============================================================
utc_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
london_time = datetime.datetime.now(pytz.timezone("Europe/London")).strftime('%Y-%m-%d %H:%M:%S')
st.caption(f"Data last updated: {utc_time} (UTC) | {london_time} (London time)")
