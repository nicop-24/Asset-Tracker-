import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime
import pytz

st.set_page_config(page_title="Asset Tracker + Forecast", layout="wide")
st.title("📊 Asset Tracker + Forecast")

# -----------------------------
# Forecasting Function (Linear Trend)
# -----------------------------
def forecast_linear(series: pd.Series, periods=7):
    X = np.arange(len(series)).reshape(-1, 1)
    y = series.values
    model = LinearRegression()
    model.fit(X, y)
    future_x = np.arange(len(series), len(series) + periods).reshape(-1, 1)
    preds = model.predict(future_x)
    future_index = pd.date_range(start=series.index[-1], periods=periods + 1, freq="D")[1:]
    return pd.Series(preds, index=future_index)

# -----------------------------
# Define tickers
# -----------------------------
equity_indices = {
    "FTSE 100": "^FTSE",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC"
}
fx_rates = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X"
}
all_tickers = {**equity_indices, **fx_rates}

# -----------------------------
# Download last 6 months of data
# -----------------------------
data = yf.download(
    list(all_tickers.values()), 
    period="6mo", 
    interval="1d", 
    group_by='ticker', 
    auto_adjust=True
)

# -----------------------------
# Prepare clean DataFrame
# -----------------------------
clean_data = pd.DataFrame()
for name, ticker in all_tickers.items():
    ticker_data = data[ticker]
    if isinstance(ticker_data, pd.DataFrame):
        if 'Close' in ticker_data.columns:
            clean_data[name] = ticker_data['Close']
        else:
            clean_data[name] = ticker_data.iloc[:, 0]
    else:
        clean_data[name] = ticker_data
clean_data.dropna(inplace=True)

# -----------------------------
# Normalize to 100 at start
# -----------------------------
normalized = clean_data / clean_data.iloc[0] * 100

# -----------------------------
# Equity table toggle
# -----------------------------
show_equity_table = st.checkbox("Show Equity Tracker Table", value=True)
if show_equity_table:
    latest = clean_data[equity_indices.keys()].iloc[-1]
    previous = clean_data[equity_indices.keys()].iloc[-2]
    change = latest - previous
    change_pct = (change / previous) * 100

    display_df = pd.DataFrame({
        "Latest Price": latest,
        "Change": change,
        "Change %": change_pct
    })

    # Apply light green/red coloring
    def color_change(val):
        color = "#98FB98" if val >= 0 else "#FFCCCB"
        return f"background-color: {color}"

    st.subheader("📈 Equity Latest Prices & Daily Change")
    st.dataframe(display_df.style.format("{:.4f}")
                                .applymap(color_change, subset=["Change", "Change %"]))

# -----------------------------
# Forecast controls
# -----------------------------
forecast_days = st.slider("Forecast Days (Equity Indices Only)", 1, 14, 7)

# -----------------------------
# Forecasting for equity indices
# -----------------------------
forecast_dict = {}
for asset in equity_indices.keys():
    forecast_dict[asset] = forecast_linear(normalized[asset], periods=forecast_days)

# -----------------------------
# Plot Equity Indices + Forecast
# -----------------------------
plt.figure(figsize=(12, 6))
eq_colors = ["blue", "green", "orange"]
for i, asset in enumerate(equity_indices.keys()):
    plt.plot(normalized.index, normalized[asset], label=f"{asset} History", color=eq_colors[i], linewidth=2)
    plt.plot(forecast_dict[asset].index, forecast_dict[asset], linestyle="--", color=eq_colors[i], linewidth=2, label=f"{asset} Forecast")

plt.title(f"Equity Indices - Last 6 Months + {forecast_days}-Day Forecast")
plt.xlabel("Date")
plt.ylabel("Normalized Value (100 = start)")
plt.legend()
plt.grid(True)
st.pyplot(plt)

# -----------------------------
# Plot FX rates (no forecast)
# -----------------------------
plt.figure(figsize=(12, 6))
fx_colors = ["purple", "brown"]
for i, asset in enumerate(fx_rates.keys()):
    plt.plot(normalized.index, normalized[asset], label=asset, color=fx_colors[i], linewidth=2)

plt.title("FX Rates - Last 6 Months")
plt.xlabel("Date")
plt.ylabel("Normalized Value (100 = start)")
plt.legend()
plt.grid(True)
st.pyplot(plt)

# -----------------------------
# Show timestamps in London & Paris time
# -----------------------------
london_tz = pytz.timezone("Europe/London")
paris_tz = pytz.timezone("Europe/Paris")
now_utc = datetime.utcnow().replace(tzinfo=pytz.UTC)
st.caption(f"Data last updated (London): {now_utc.astimezone(london_tz).strftime('%Y-%m-%d %H:%M:%S')}")
st.caption(f"Data last updated (Paris): {now_utc.astimezone(paris_tz).strftime('%Y-%m-%d %H:%M:%S')}")
