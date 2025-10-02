import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Define tickers
tickers = {
    "FTSE 100": "^FTSE",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X"
}

# Download last 6 months of data
data = yf.download(list(tickers.values()), period="6mo", interval="1d", group_by='ticker', auto_adjust=True)

# Prepare a clean DataFrame
clean_data = pd.DataFrame()

for name, ticker in tickers.items():
    ticker_data = data[ticker]
    
    # If multi-column (indices), select 'Close'
    if isinstance(ticker_data, pd.DataFrame):
        if 'Close' in ticker_data.columns:
            clean_data[name] = ticker_data['Close']
        else:
            # fallback: take first column
            clean_data[name] = ticker_data.iloc[:, 0]
    else:
        # FX: usually a Series
        clean_data[name] = ticker_data

# Drop rows with missing data
clean_data.dropna(inplace=True)

# Normalize to 100 at the start
normalized = clean_data / clean_data.iloc[0] * 100

# Plot
plt.figure(figsize=(10,6))
for col in normalized.columns:
    plt.plot(normalized.index, normalized[col], label=col)

plt.title("Asset Tracker - Normalized Performance (100 = start)")
plt.ylabel("Normalized Value")
plt.xlabel("Date")
plt.legend()
plt.grid(True)
plt.show()
