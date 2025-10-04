import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
import pytz
import altair as alt

# ============================================================
# SETTINGS
# ============================================================
st.set_page_config(page_title="Asset Tracker Dashboard", layout="wide")
st.title("📊 Asset Tracker Dashboard")

tickers = {
    "FTSE 100": "^FTSE",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X"
}

# ============================================================
# FETCH DATA
# ============================================================
@st.cache_data(ttl=900)  # cache for 15 minutes
def fetch_data():
    data = yf.download(
        tickers=list(tickers.values()),
        period="6mo",
        interval="1d",
        auto_adjust=True,
        progress=False,
    )["Close"]
    data = data.rename(columns={v: k for k, v in tickers.items()})
    data = data.dropna(how="all")
    return data

daily = fetch_data()

# Ensure we only use fully available (last complete) trading day
latest_date = daily.dropna().index.max()
latest_data = daily.loc[latest_date]
# previous available trading day
prev_date = daily.loc[:latest_date].iloc[-2].name
prev_data = daily.loc[prev_date]

# ============================================================
# TABLE: Latest Prices and Daily Change
# ============================================================
prices = pd.DataFrame({
    "Asset": daily.columns,
    "Latest Price": [latest_data[a] for a in daily.columns],
    "Prev Close": [prev_data[a] for a in daily.columns]
})
prices["% Change"] = ((prices["Latest Price"] - prices["Prev Close"]) / prices["Prev Close"] * 100).round(2)

st.subheader("📈 Latest Prices and Daily Change")
st.dataframe(prices, hide_index=True, use_container_width=True)

# ============================================================
# CHARTS
# ============================================================
# Only up to last complete trading day
chart_data = daily.loc[:latest_date]

# Normalize (base 100)
normalized = (chart_data / chart_data.iloc[0]) * 100
normalized = normalized.reset_index().melt(id_vars="Date", var_name="Asset", value_name="Value")

# ============================================================
# EQUITY CHART
# ============================================================
st.subheader("📊 Equity Indices (Base 100)")

equities = ["FTSE 100", "S&P 500", "NASDAQ"]
eq_chart = (
    alt.Chart(normalized[normalized["Asset"].isin(equities)])
    .mark_line()
    .encode(
        x="Date:T",
        y=alt.Y("Value:Q", title="Normalized (Base 100)"),
        color="Asset:N",
        tooltip=["Date:T", "Asset:N", "Value:Q"]
    )
    .properties(height=400)
)
st.altair_chart(eq_chart, use_container_width=True)

# ============================================================
# FX CHART
# ============================================================
st.subheader("💱 FX Rates (Base 100)")

fx_pairs = ["EUR/USD", "GBP/USD"]
fx_chart = (
    alt.Chart(normalized[normalized["Asset"].isin(fx_pairs)])
    .mark_line()
    .encode(
        x="Date:T",
        y=alt.Y("Value:Q", title="Normalized (Base 100)"),
        color="Asset:N",
        tooltip=["Date:T", "Asset:N", "Value:Q"]
    )
    .properties(height=400)
)
st.altair_chart(fx_chart, use_container_width=True)

# ============================================================
# TIMESTAMPS
# ============================================================
utc_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
london_time = datetime.datetime.now(pytz.timezone("Europe/London")).strftime('%Y-%m-%d %H:%M:%S')

st.caption(f"Data last updated: {utc_time} UTC | {london_time} London time")
