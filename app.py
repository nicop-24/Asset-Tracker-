import yfinance as yf
import pandas as pd
import streamlit as st
import datetime
import pytz
import altair as alt

st.title("📊 Asset Tracker Dashboard")

# ================================
# Assets
# ================================
equity_tickers = {
    "FTSE 100": "^FTSE",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC"
}

fx_tickers = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X"
}

all_tickers = {**equity_tickers, **fx_tickers}

# ================================
# Download 6 months of daily + intraday
# ================================
@st.cache_data(ttl=900)  # cache 15 minutes
def get_data():
    data_daily = pd.DataFrame()
    data_intraday = pd.DataFrame()
    for name, symbol in all_tickers.items():
        try:
            # Daily closes for chart & table
            df_daily = yf.download(symbol, period="6mo", interval="1d")[["Close"]].rename(columns={"Close": name})
            data_daily = pd.concat([data_daily, df_daily], axis=1)

            # Intraday 15m for latest values
            df_intraday = yf.download(symbol, period="7d", interval="15m")[["Close"]].rename(columns={"Close": name})
            data_intraday = pd.concat([data_intraday, df_intraday], axis=1)
        except Exception as e:
            st.warning(f"⚠️ Could not download {name}: {e}")

    return data_daily.ffill(), data_intraday.ffill()

daily, intraday = get_data()

# ================================
# Table: Latest Prices & % Change
# ================================
today = datetime.datetime.utcnow().date()
latest_prices = intraday.iloc[-1].combine_first(daily.iloc[-1])
prev_prices = daily.iloc[-2]

prices = pd.DataFrame({
    "Latest Price": latest_prices,
    "Prev Close": prev_prices
})
prices["% Change vs Prev Close"] = ((prices["Latest Price"] - prices["Prev Close"]) / prices["Prev Close"] * 100).round(2)

st.subheader("📈 Latest Prices and Daily Change")
st.dataframe(prices)

# ================================
# Equity Chart (Base 100)
# ================================
equity_chart_data = daily[list(equity_tickers.keys())].ffill()
normalized = (equity_chart_data / equity_chart_data.iloc[0]) * 100

# Dynamic Y axis: min 80, max = highest + 20
y_lower = 80
y_upper = int(normalized.max().max() + 20)

# Melt for Altair
normalized_reset = normalized.reset_index()
normalized_reset.rename(columns={normalized_reset.columns[0]: "Date"}, inplace=True)
normalized_reset = pd.melt(normalized_reset, id_vars=["Date"], var_name="Asset", value_name="Value")

st.subheader("📊 Equity Indices (6 months, normalized to 100)")
equity_chart = alt.Chart(normalized_reset).mark_line().encode(
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
# FX Charts
# ================================
fx_chart_data = daily[list(fx_tickers.keys())].ffill()
fx_normalized = (fx_chart_data / fx_chart_data.iloc[0]) * 100

fx_reset = fx_normalized.reset_index()
fx_reset.rename(columns={fx_reset.columns[0]: "Date"}, inplace=True)
fx_reset = pd.melt(fx_reset, id_vars=["Date"], var_name="Asset", value_name="Value")

st.subheader("💱 Currencies (6 months, normalized to 100)")
fx_chart = alt.Chart(fx_reset).mark_line().encode(
    x="Date:T",
    y=alt.Y("Value:Q", scale=alt.Scale(domain=[80, int(fx_reset["Value"].max().max()+20)])),
    color="Asset:N",
    tooltip=[
        "Date:T",
        "Asset:N",
        alt.Tooltip("Value:Q", title="Rebased Value", format=".2f")
    ]
).properties(width=700, height=400)

st.altair_chart(fx_chart, use_container_width=True)

# ================================
# Footer: UTC + London time
# ================================
utc_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
london_time = datetime.datetime.now(pytz.timezone("Europe/London")).strftime('%Y-%m-%d %H:%M:%S')

st.caption(f"Data last updated: {utc_time} (UTC) | {london_time} (London time)")
