import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Asset Tracker", layout="wide")
st.title("Asset Tracker - Daily Performance")

tickers = {
    "FTSE 100": "^FTSE",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X"
}

data = yf.download(list(tickers.values()), period="6mo", interval="1d", group_by='ticker', auto_adjust=True)

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

# Normalize for performance chart
normalized = clean_data / clean_data.iloc[0] * 100
st.line_chart(normalized)

# Latest prices
st.subheader("Latest Prices")
st.dataframe(clean_data.tail(1).T.rename(columns={clean_data.tail(1).columns[0]: "Price"}))

# Daily % change
daily_change = clean_data.pct_change() * 100
daily_change = daily_change.round(2)
st.subheader("Daily % Change")
st.dataframe(daily_change.tail(1).T.rename(columns={daily_change.columns[0]: "Daily Change (%)"}))

# Last data date
last_date = clean_data.index[-1].strftime("%Y-%m-%d")
st.write(f"Last data update: {last_date}")
