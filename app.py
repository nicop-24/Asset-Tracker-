import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Asset Tracker", layout="wide")
st.title("Asset Tracker - Daily Performance")

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
    if isinstance(ticker_data, pd.DataFrame):
        if 'Close' in ticker_data.columns:
            clean_data[name] = ticker_data['Close']
        else:
            clean_data[name] = ticker_data.iloc[:, 0]
    else:
        clean_data[name] = ticker_data

clean_data.dropna(inplace=True)

# Normalize to 100 at start
normalized = clean_data / clean_data.iloc[0] * 100

# Display the normalized chart
st.line_chart(normalized)

# Display the last available prices in a table
st.subheader("Latest Prices")
st.dataframe(clean_data.tail(1).T.rename(columns={clean_data.tail(1).columns[0]: "Price"}))
