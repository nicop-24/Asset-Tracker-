import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime

st.set_page_config(page_title="Asset Tracker + Forecast", layout="wide")
st.title("📊 Asset Tracker + 7-Day Forecast")

# -----------------------------
# Forecasting Function (Linear Trend)
# -----------------------------
def forecast_linear(series: pd.Series, periods=7):
    """Linear regression forecast for next `periods` days"""
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
tickers = {
    "FTSE 100": "^FTSE",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X"
}

# -----------------------------
# Download last 6 months of data
# -----------------------------
data = yf.download(
    list(tickers.values()), 
    period="6mo", 
    interval="1d", 
    group_by='ticker', 
    auto_adjust=True
)

# -----------------------------
# Prepare clean DataFrame
# -----------------------------
clean_data = pd.DataFrame()
for name, ticker in tickers.items():
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
# Display Latest Prices + Daily Change
# -----------------------------
st.subheader("📈 Latest Prices & Daily Change")

latest = clean_data.iloc[-1]
previous = clean_data.iloc[-2]
change = latest - previous
change_pct = (change / previous) * 100

display_df = pd.DataFrame({
    "Latest Price": latest,
    "Change": change,
    "Change %": change_pct
})

st.dataframe(display_df.style.format("{:.4f}").background_gradient(cmap='RdYlGn', subset=["Change", "Change %"]))

# -----------------------------
# Streamlit Controls
# -----------------------------
forecast_days = st.slider("Forecast Days (Equity Indices Only)", 1, 14, 7)

# -----------------------------
# Forecasting for equity indices
# -----------------------------
equity_indices = ["FTSE 100", "S&P 500", "NASDAQ"]
forecast_dict = {}
for asset in equity_indices:
    forecast_dict[asset] = forecast_linear(normalized[asset], periods=forecast_days)

# -----------------------------
# Plot Normalized Performance + Forecast
# -----------------------------
plt.figure(figsize=(12, 6))

# Colors for FX and Equity
fx_colors = ["purple", "brown"]
eq_colors = ["blue", "green", "orange"]

# Plot FX rates
for i, asset in enumerate(["EUR/USD", "GBP/USD"]):
    plt.plot(normalized.index, normalized[asset], label=asset, color=fx_colors[i], linewidth=2)

# Plot Equity Indices + Forecast
for i, asset in enumerate(equity_indices):
    plt.plot(normalized.index, normalized[asset], label=f"{asset} History", color=eq_colors[i], linewidth=2)
    plt.plot(forecast_dict[asset].index, forecast_dict[asset], linestyle="--", color=eq_colors[i], linewidth=2, label=f"{asset} Forecast")

plt.title(f"Asset Tracker - Last 6 Months + {forecast_days}-Day Forecast for Equity Indices")
plt.xlabel("Date")
plt.ylabel("Normalized Value (100 = start)")
plt.legend()
plt.grid(True)

st.pyplot(plt)

# -----------------------------
# Show timestamp of last update
# -----------------------------
st.caption(f"Data last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
