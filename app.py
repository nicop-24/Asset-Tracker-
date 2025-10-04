import yfinance as yf
import pandas as pd
import streamlit as st
import datetime
import pytz
import altair as alt

st.title("📊 Asset Tracker Dashboard")

# ================================
# Tickers
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
# Download data
# ================================
@st.cache_data(ttl=900)  # cache 15 minutes
def get_data():
    daily_data = pd.DataFrame()
    intraday_data = pd.DataFrame()
    for name, symbol in all_tickers.items():
        try:
            # Daily 6mo
            df_daily = yf.download(symbol, period="6mo", interval="1d")[["Close"]].rename(columns={"Close": name})
            daily_data = pd.concat([daily_data, df_daily], axis=1)

            # Intraday 7d, 15min
            df_intraday = yf.download(symbol, period="7d", interval="15m")[["Close"]].rename(columns={"Close": name})
            intraday_data = pd.concat([intraday_data, df_intraday], axis=1)
        except Exception as e:
            st.warning(f"⚠️ Could not download {name}: {e}")

    # Ensure all columns exist
    for name in all_tickers.keys():
        if name not in daily_data.columns:
            daily_data[name] = pd.NA
        if name not in intraday_data.columns:
            intraday_data[name] = pd.NA

    return daily_data.ffill(), intraday_data.ffill()

daily, intraday = get_data()

# ================================
# Latest prices table
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
# Equity Chart (FTSE, S&P 500, NASDAQ)
# ================================
equity_data = daily[list(equity_tickers.keys())].copy()
equity_data = equity_data.ffill()

# Normalize to base 100
normalized = (equity_data / equity_data.iloc[0]) * 100

# Reset index and ensure "Date" exists
normalized_reset = normalized.reset_index()
normalized_reset.rename(columns={normalized_reset.columns[0]: "Date"}, inplace=True)

# Melt safely
if "Date" in normalized_reset.columns:
    normalized_reset = pd.melt(
        normalized_reset,
        id_vars=["Date"],
        var_name="Asset",
        value_name="Value"
    )
else:
    st.error("Date column missing in normalized equity data.")
    normalized_reset = pd.DataFrame(columns=["Date", "Asset", "Value"])

# Compute % change since start for labels
start_values = normalized.iloc[0]
latest_values = normalized.iloc[-1]
percent_change_labels = {asset: ((latest_values[asset] - start_values[asset])/start_values[asset]*100).round(2)
                         for asset in equity_tickers.keys()}

# Y-axis: zoom 80 to max+20
y_lower = 80
y_upper = int(normalized_reset["Value"].max().max() + 20) if not normalized_reset.empty else 150

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

# Add labels for latest % change since start
labels_data = pd.DataFrame({
    "Asset": list(percent_change_labels.keys()),
    "Value": [latest_values[a] for a in percent_change_labels.keys()],
    "Label": [f"{v:+.2f}%" for v in percent_change_labels.values()]
})
label_chart = alt.Chart(labels_data).mark_text(
    align='left',
    dx=5,
    dy=-5,
    fontWeight='bold'
).encode(
    x=alt.value(normalized_reset["Date"].max()),  # place at the far right
    y="Value:Q",
    text="Label:N",
    color="Asset:N"
)

st.altair_chart(equity_chart + label_chart, use_container_width=True)

# ================================
# FX Chart
# ================================
fx_data = daily[list(fx_tickers.keys())].copy()
fx_data = fx_data.ffill()

fx_normalized = (fx_data / fx_data.iloc[0]) * 100
fx_reset = fx_normalized.reset_index()
fx_reset.rename(columns={fx_reset.columns[0]: "Date"}, inplace=True)

if "Date" in fx_reset.columns:
    fx_reset = pd.melt(
        fx_reset,
        id_vars=["Date"],
        var_name="Asset",
        value_name="Value"
    )
else:
    st.error("Date column missing in FX data.")
    fx_reset = pd.DataFrame(columns=["Date", "Asset", "Value"])

st.subheader("💱 Currencies (6 months, normalized to 100)")
fx_chart = alt.Chart(fx_reset).mark_line().encode(
    x="Date:T",
    y=alt.Y("Value:Q", scale=alt.Scale(domain=[80, int(fx_reset["Value"].max().max()+20) if not fx_reset.empty else 120])),
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
