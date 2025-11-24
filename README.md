Asset Tracker Dashboard

A lightweight, Streamlit-powered dashboard to monitor global markets.
The app fetches data from Yahoo Finance and shows both daily price changes and historical trends for selected indices and currencies, with simple short-term forecasting for equity indices.

Features

📈 Live tracking of stock indices and FX pairs.

🔄 Automatic update of latest available prices (with fallback to yesterday’s close if today is incomplete).

📊 Visual charts of the past 6 months of data.

📉 7-day forecast for equity indices (FTSE 100, S&P 500, NASDAQ) with dotted lines for clear distinction.

💹 Daily change coloring: light green (#98FB98) for positive change, light red (#FFCCCB) for negative change.

🌍 Timezone support: shows last update in both London and Paris time.

✅ Interactive controls: toggle to show/hide the equity tracker table, and adjust forecast length.

Assets Tracked
Equity Indices

FTSE 100

S&P 500

NASDAQ

FX Rates

EUR/USD

GBP/USD

Technologies Used

Python

Streamlit – interactive dashboard

yfinance – financial data fetching

pandas – data manipulation

matplotlib – charting

pytz – timezone handling

scikit-learn – linear regression forecasting

License

This project is licensed under the MIT License.
You are free to use, modify, and distribute this software, provided the copyright notice is included.
