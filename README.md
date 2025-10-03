# Asset Tracker

Asset Tracker is a Python-based dashboard that tracks the daily performance of major financial indices and FX pairs. It allows users to visualize normalized performance over time and serves as a foundation for portfolio tracking and risk analysis projects.

## Assets / Currencies Tracked
- **FTSE 100** (UK large-cap index)
- **S&P 500** (US large-cap index)
- **NASDAQ** (US tech-heavy index)
- **EUR/USD** (Euro vs US Dollar)
- **GBP/USD** (British Pound vs US Dollar)

## Features
- Fetches historical daily data for the last 6 months using `yfinance`.
- Handles both multi-column indices (OHLCV) and single-column FX pairs.
- Normalizes all assets to 100 at the start date for easy comparison.
- Plots performance trends over time using `matplotlib`.
- Designed to be extended for portfolio weights, cumulative returns, and risk metrics.

## Technologies Used
- Python 3
- [yfinance](https://pypi.org/project/yfinance/)
- [pandas](https://pandas.pydata.org/)
- [matplotlib](https://matplotlib.org/)
- [Streamlit](https://streamlit.io/) (for future interactive dashboards)

## Roadmap / Future Work
- Add portfolio weighting and cumulative performance tracking.
- Include risk metrics such as volatility and Sharpe ratio.
- Deploy as an interactive Streamlit dashboard for live updates.
- Extend to more indices, commodities, and currencies.

## License
MIT License
