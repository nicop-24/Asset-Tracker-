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
# Helper function: download data safely
# ================================
@st.cache_data(ttl=3600)
def get_data():
    all_data = pd.DataFrame()
    for name, symbol in tickers.items():
        try:
            df = yf.download(symbol, period="6mo", interval="1d")[["Close"]]
            df.rename(columns={"Close": name}, inplace=True)
            all_data = pd.concat([all_data, df], axis=1)
        except Exception as e:
            st.warning(f"⚠️ Could not download data for {name}: {e}")
    return all_data.ffill()

daily = get_data()

# ================================
# Ensure all tickers are present
# ================================
for name in tickers.keys():
    if name not in daily.columns:
        daily[name] = None

# ================================
# Handle latest prices
# ================================
today = datetime.date.today()

# If today's data is incomplete, use yesterday
if today in daily.index:
    latest_daily = daily.iloc[-2]
    yesterday_daily = daily.iloc[-3]
    daily_chart = daily.iloc[:-1]
else:
    latest_daily = daily.iloc[-1]
    yesterday_daily = daily.iloc[-2]
    daily_chart = daily

# ================================
# Price Table
# ================================
prices = pd.DataFrame({
    "Latest Price": latest_daily,
    "Prev Close": yesterday_daily
})
prices["% Change vs Prev Close"] = (
    (prices["Latest Price"] - prices["Prev Close"]) / prices["Prev Close"] * 100
).round(2)

st.subheader("📈 Latest Prices and Daily Change")
st.dataframe(prices)

# ================================
# Normalize to base = 100
# ================================
normalized = (daily_chart / daily_chart.iloc[0]) * 100
normalized = normalized.ffill()

# Ensure index is named and reset properly
normalized.index.name = "Date"
normalized_reset = normalized.reset_index()

# Melt into long format safely
normalized_reset = pd.melt(
    normalized_reset,
    id_vars=["Date"],
    var_name="Asset",
    value_name="Value"
)

# Dynamic y-axis scaling
y_max = normalized_reset["Value"].max()
y_upper = int(((y_max // 10) + 1) * 10)
y_lower = 80  # zoom in base

# ================================
# Equity Chart
# ================================
st.subheader("📊 Equity Indices (6 months, normalized to 100)")
equity_assets = ["FTSE 100", "S&P 500", "NASDAQ"]

equity_chart = alt.Chart(
    normalized_reset[normalized_reset["Asset"].isin(equity_assets)]
).mark_line().encode(
    x="Date:T",
    y=alt.Y("Value:Q", scale=alt.Scale(domain=[y_lower, y_upper])),
    color="Asset:N",
    tooltip=[
        "Date:T",
        "Asset:N",
        alt.Tooltip("Value:Q", title="Rebased Value", format=".2f")
    ]
).properties(width=700, height=400)

st.altair_chart(equity_chart, use_container_width=True)

# ================================
# FX Chart
# ================================
st.subheader("💱 Currencies (6 months, normalized to 100)")
fx_assets = ["EUR/USD", "GBP/USD"]

fx_chart = alt.Chart(
    normalized_reset[normalized_reset["Asset"].isin(fx_assets)]
).mark_line().encode(
    x="Date:T",
    y=alt.Y("Value:Q", scale=alt.Scale(domain=[y_lower, y_upper])),
    color="Asset:N",
    tooltip=[
        "Date:T",
        "Asset:N",
        alt.Tooltip("Value:Q", title="Rebased Value", format=".2f")
    ]
).properties(width=700, height=400)

st.altair_chart(fx_chart, use_container_width=True)

# ================================
# Footer with UTC + London time
# ================================
utc_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
london_time = datetime.datetime.now(pytz.timezone("Europe/London")).strftime('%Y-%m-%d %H:%M:%S')

st.caption(f"Data last updated: {utc_time} (UTC) | {london_time} (London time)")

