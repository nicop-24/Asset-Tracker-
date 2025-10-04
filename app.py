# app.py
import yfinance as yf
import pandas as pd
import streamlit as st
import datetime
import pytz
import altair as alt
from typing import Tuple, Optional

st.set_page_config(page_title="Asset Tracker", layout="wide")
st.title("📊 Asset Tracker Dashboard")

# -------------------------
# Tickers and fallbacks
# -------------------------
tickers_primary = {
    "FTSE 100": "^FTSE",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
}

# Fallback ETF proxies for US indices (if index tickers fail)
tickers_fallback = {
    "S&P 500": "SPY",
    "NASDAQ": "QQQ",
}

# -------------------------
# Helper functions
# -------------------------
def fetch_intraday_latest_price(ticker: str) -> Tuple[Optional[pd.Timestamp], Optional[float], Optional[pd.Series]]:
    """
    Try to fetch intraday (1m) recent data for the ticker.
    Returns (timestamp_utc, price, minute_series) or (None, None, None) on failure/empty.
    """
    try:
        # get last 7 days of 1m bars (yfinance may return minute bars for recent days)
        hist = yf.Ticker(ticker).history(period="7d", interval="1m", prepost=False)
        if hist is None or hist.empty:
            return None, None, None
        # 'Close' column exists
        last_idx = hist.index[-1]
        # convert to UTC tz-aware timestamp
        if last_idx.tzinfo is None:
            last_idx = last_idx.tz_localize("UTC")
        else:
            last_idx = last_idx.tz_convert("UTC")
        last_price = hist["Close"].iloc[-1]
        # return minute series too (with timezone converted to UTC)
        hist = hist.tz_convert("UTC")
        return last_idx, float(last_price), hist["Close"]
    except Exception:
        return None, None, None

def fetch_daily_series(ticker: str, period: str = "6mo") -> Optional[pd.Series]:
    """
    Fetch daily close series for `period` (e.g., '6mo' or '60d').
    Returns pd.Series indexed by date (tz-naive, normalized to midnight).
    """
    try:
        df = yf.download(ticker, period=period, interval="1d", progress=False)["Close"]
        if isinstance(df, pd.Series):
            s = df.copy()
        else:
            # DataFrame -> Series if single ticker
            s = df
        if s is None or s.empty:
            return None
        # convert index to date-only (keep as Timestamp but timezone-naive)
        s.index = pd.to_datetime(s.index).normalize()
        s.name = ticker
        return s
    except Exception:
        return None

def last_available_and_prev_close(daily_series: pd.Series, reference_date: pd.Timestamp) -> Tuple[pd.Timestamp, float, pd.Timestamp, float]:
    """
    Given a daily series (index = normalized dates) and a reference_date (tz-aware or naive),
    find the latest available date <= reference_date and its close, and the previous trading day's date and close.
    Returns (latest_date, latest_close, prev_date, prev_close).
    Raises KeyError if series empty.
    """
    if daily_series is None or daily_series.empty:
        raise KeyError("Empty daily series")

    # normalize reference_date to date (naive)
    if isinstance(reference_date, pd.Timestamp):
        ref_date = pd.to_datetime(reference_date).normalize()
    elif isinstance(reference_date, (datetime.datetime, datetime.date)):
        ref_date = pd.to_datetime(reference_date).normalize()
    else:
        ref_date = pd.to_datetime(str(reference_date)).normalize()

    # find all dates <= ref_date
    available_dates = daily_series.index[daily_series.index <= ref_date]
    if len(available_dates) == 0:
        # no date <= ref_date, use latest available in series
        latest_date = daily_series.index.max()
    else:
        latest_date = available_dates.max()

    latest_close = float(daily_series.loc[latest_date])

    # previous trading day: the index just before latest_date
    idx_pos = daily_series.index.get_indexer([latest_date])[0]
    if idx_pos <= 0:
        # no previous, use same day for prev (edge-case)
        prev_date = latest_date
        prev_close = latest_close
    else:
        prev_date = daily_series.index[idx_pos - 1]
        prev_close = float(daily_series.loc[prev_date])

    return latest_date, latest_close, prev_date, prev_close

# -------------------------
# Main fetching logic
# -------------------------
st.caption("Fetching latest data (intraday up to 1-min, and daily for historical/prev-close)...")

asset_data = {}  # name -> dict with series/info
errors = []

now_utc = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)

for asset_name, primary_ticker in tickers_primary.items():
    chosen_ticker = primary_ticker
    used_fallback = False

    # 1) Try intraday latest price for primary ticker
    ts, price, minute_series = fetch_intraday_latest_price(primary_ticker)

    # 2) If no intraday found and fallback exists, try fallback
    if (ts is None or price is None) and asset_name in tickers_fallback:
        fb = tickers_fallback[asset_name]
        st.info(f"Trying fallback for {asset_name}: {fb}")
        ts, price, minute_series = fetch_intraday_latest_price(fb)
        if ts is not None:
            chosen_ticker = fb
            used_fallback = True

    # 3) Also fetch daily 6mo series for charts/historical & prev close
    daily_series = fetch_daily_series(chosen_ticker, period="6mo")
    # As a safety: if daily 6mo empty and we used primary, try fallback daily
    if (daily_series is None or daily_series.empty) and asset_name in tickers_fallback and not used_fallback:
        fb = tickers_fallback[asset_name]
        st.info(f"No 6mo daily for {asset_name} with {primary_ticker}, try fallback {fb}")
        daily_series = fetch_daily_series(fb, period="6mo")
        if daily_series is not None and not daily_series.empty:
            chosen_ticker = fb
            used_fallback = True

    # 4) If minute-level data missing, try to derive latest price from daily last available close
    if (ts is None or price is None) and daily_series is not None and not daily_series.empty:
        # use last available daily close as "latest"
        latest_date = daily_series.index.max()
        price = float(daily_series.loc[latest_date])
        # craft a timestamp at market close (00:00 normalized); mark as naive date -> set to UTC midnight to show time
        ts = pd.Timestamp(latest_date).tz_localize(pytz.UTC)
        minute_series = None

    # 5) If still no data, mark as missing
    if price is None or ts is None:
        errors.append(f"No data for {asset_name} (tried {chosen_ticker})")
        continue

    # 6) Determine previous close based on daily_series and ts
    prev_close = None
    prev_date = None
    if daily_series is not None and not daily_series.empty:
        try:
            latest_day, latest_close_daily, prev_day, prev_close_daily = last_available_and_prev_close(daily_series, ts)
            # If our minute-level price exists for a time after daily close, keep minute price but use prev_close_daily
            prev_close = prev_close_daily
            prev_date = prev_day
        except Exception:
            prev_close = None
            prev_date = None

    asset_data[asset_name] = {
        "asset_name": asset_name,
        "ticker": chosen_ticker,
        "used_fallback": used_fallback,
        "latest_ts_utc": ts,  # tz-aware UTC timestamp
        "latest_price": price,
        "minute_series": minute_series,  # pd.Series or None (UTC indexed)
        "daily_series": daily_series,    # pd.Series (date-indexed) or None
        "prev_close": prev_close,
        "prev_close_date": prev_date,
    }

# Show warnings if some assets missing
if errors:
    for e in errors:
        st.warning(e)

# -------------------------
# Build Latest Prices DataFrame
# -------------------------
rows = []
for name, info in asset_data.items():
    latest_ts = info["latest_ts_utc"]
    latest_price = info["latest_price"]
    prev_close = info.get("prev_close", None)

    # If prev_close is None, attempt to fetch a daily 60d fallback
    if prev_close is None:
        ds = fetch_daily_series(info["ticker"], period="60d")
        if ds is not None and not ds.empty:
            try:
                _, _, prev_d, prev_c = last_available_and_prev_close(ds, latest_ts)
                prev_close = prev_c
            except Exception:
                prev_close = None

    pct_change = None
    if prev_close is not None and prev_close != 0:
        pct_change = round((latest_price - prev_close) / prev_close * 100, 2)

    rows.append({
        "Asset": name,
        "Ticker": info["ticker"] + (" (fallback)" if info["used_fallback"] else ""),
        "Latest Price": latest_price,
        "Prev Close": prev_close,
        "% Change vs Prev Close": pct_change,
        "Latest Timestamp (UTC)": latest_ts.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "Latest Timestamp (London)": latest_ts.astimezone(pytz.timezone("Europe/London")).strftime("%Y-%m-%d %H:%M:%S %Z")
    })

prices_df = pd.DataFrame(rows).set_index("Asset")
st.subheader("📈 Latest Prices and Daily Change (most recent available)")
st.dataframe(prices_df)

# Overall last-updated timestamp (max of asset timestamps)
if asset_data:
    overall_last = max([info["latest_ts_utc"] for info in asset_data.values()])
    utc_str = overall_last.strftime("%Y-%m-%d %H:%M:%S %Z")
    london_str = overall_last.astimezone(pytz.timezone("Europe/London")).strftime("%Y-%m-%d %H:%M:%S %Z")
    st.caption(f"Data timestamps are shown per-asset. Latest data point across assets: {utc_str} (UTC) | {london_str} (London time)")

# -------------------------
# Build normalized 6mo charts
# -------------------------
# Prepare a combined daily DataFrame for all assets (use the chosen tickers)
daily_frames = {}
for name, info in asset_data.items():
    ds = info["daily_series"]
    if ds is not None and not ds.empty:
        # rename series to friendly name
        s = ds.copy()
        s.name = name
        daily_frames[name] = s

if len(daily_frames) == 0:
    st.error("No daily series available to build charts.")
    st.stop()

daily_all = pd.concat(daily_frames.values(), axis=1).sort_index()
# Drop any columns entirely NaN
daily_all = daily_all.dropna(how="all", axis=1)

# If after drop nothing remains, stop
if daily_all.empty:
    st.error("No usable daily data for charts.")
    st.stop()

# Ensure we have at least 6 months; if not, we still normalize from first available
# Normalize to base 100 using first available value per series
normalized = daily_all.copy()
for col in normalized.columns:
    first_valid = normalized[col].first_valid_index()
    if first_valid is None:
        normalized[col] = pd.NA
        continue
    normalized[col] = (normalized[col] / normalized[col].loc[first_valid]) * 100

# prepare for altair (reset index -> Date)
normalized_reset = normalized.reset_index().melt("index", var_name="Asset", value_name="Value")
normalized_reset = normalized_reset.rename(columns={"index": "Date"})
# Filter equity vs fx
equity_assets = ["FTSE 100", "S&P 500", "NASDAQ"]
fx_assets = ["EUR/USD", "GBP/USD"]

# Equity chart
available_equities = [a for a in equity_assets if a in normalized.columns]
st.subheader("📊 Equity Indices (6 months, normalized to 100)")
if len(available_equities) == 0:
    st.warning("No equity index data available for plotting.")
else:
    eq_df = normalized_reset[normalized_reset["Asset"].isin(available_equities)].dropna()
    if eq_df.empty:
        st.warning("Equity data is empty after cleaning.")
    else:
        # dynamic y-axis domain
        y_max = eq_df["Value"].max()
        y_min = eq_df["Value"].min()
        y_upper = int(((y_max // 10) + 1) * 10)
        y_lower = int(max(0, ((y_min // 10) - 1) * 10))
        eq_chart = alt.Chart(eq_df).mark_line().encode(
            x=alt.X("Date:T", title="Date"),
            y=alt.Y("Value:Q", title="Indexed (Base 100)", scale=alt.Scale(domain=[y_lower, y_upper])),
            color=alt.Color("Asset:N", title="Asset"),
            tooltip=[alt.Tooltip("Date:T"), alt.Tooltip("Asset:N"), alt.Tooltip("Value:Q", format=".2f")]
        ).properties(width=900, height=400)
        st.altair_chart(eq_chart, use_container_width=True)

# FX chart
available_fx = [a for a in fx_assets if a in normalized.columns]
st.subheader("💱 Currencies (6 months, normalized to 100)")
if len(available_fx) == 0:
    st.warning("No FX data available for plotting.")
else:
    fx_df = normalized_reset[normalized_reset["Asset"].isin(available_fx)].dropna()
    if fx_df.empty:
        st.warning("FX data is empty after cleaning.")
    else:
        y_max = fx_df["Value"].max()
        y_min = fx_df["Value"].min()
        y_upper = int(((y_max // 10) + 1) * 10)
        y_lower = int(max(0, ((y_min // 10) - 1) * 10))
        fx_chart = alt.Chart(fx_df).mark_line().encode(
            x=alt.X("Date:T", title="Date"),
            y=alt.Y("Value:Q", title="Indexed (Base 100)", scale=alt.Scale(domain=[y_lower, y_upper])),
            color=alt.Color("Asset:N", title="Asset"),
            tooltip=[alt.Tooltip("Date:T"), alt.Tooltip("Asset:N"), alt.Tooltip("Value:Q", format=".2f")]
        ).properties(width=900, height=400)
        st.altair_chart(fx_chart, use_container_width=True)

# -------------------------
# Footer: extra diagnostics and tips
# -------------------------
st.markdown("---")
st.markdown("**Notes & behavior**:")
st.markdown("""
- Latest prices are taken from intraday 1-minute bars where available (Yahoo data typically has a short delay, often ~15 minutes).
- If minute-level intraday data is unavailable, the latest available daily close is used.
- If today's data is missing (e.g., asset not traded today), the previous trading day's close is used automatically.
- For U.S. index tickers (like ^GSPC, ^IXIC), Yahoo sometimes restricts index tickers in some regions; the app automatically tries ETF fallbacks (SPY / QQQ) where configured.
- If you need real-time/official exchange data or streaming feeds, consider a paid market data provider / API.
""")
