import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

tickers = {
    "FTSE 100": "^FTSE",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X"
}

data = yf.download(list(tickers.values()), period="6mo")['Adj Close']


data = data.rename(columns={v: k for k, v in tickers.items()})


(data / data.iloc[0] * 100).plot(figsize=(10,6))
plt.title("Asset Tracker - Normalized Performance (100 = start)")
plt.ylabel("Index / FX Value (normalized)")
plt.xlabel("Date")
plt.grid(True)
plt.show()
