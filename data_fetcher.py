"""
Data fetching module using yfinance API
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_stock_data(ticker, period="1y", interval="1d"):
    """
    Fetch historical stock data using yfinance
    
    Args:
        ticker: Stock symbol
        period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
    
    Returns:
        DataFrame with OHLCV data
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        
        if df.empty:
            st.error(f"No data found for {ticker}")
            return None
        
        # Clean column names
        df.columns = [col.lower() for col in df.columns]
        
        return df
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def fetch_stock_data_range(ticker, start_date, end_date, interval="1d"):
    """
    Fetch historical stock data for a specific date range
    
    Args:
        ticker: Stock symbol
        start_date: Start date (datetime or string)
        end_date: End date (datetime or string)
        interval: Data interval
    
    Returns:
        DataFrame with OHLCV data
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date, interval=interval)
        
        if df.empty:
            st.error(f"No data found for {ticker} in the specified range")
            return None
        
        # Clean column names
        df.columns = [col.lower() for col in df.columns]
        
        return df
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {str(e)}")
        return None

def get_multiple_timeframes(ticker, periods=None):
    """
    Fetch data for multiple timeframes for better ICT analysis
    
    Args:
        ticker: Stock symbol
        periods: Dict of timeframe names to (period, interval) tuples
    
    Returns:
        Dict of timeframe DataFrames
    """
    if periods is None:
        periods = {
            "1h": ("5d", "1h"),
            "4h": ("60d", "1h"),  # We'll resample to 4h
            "daily": ("1y", "1d")
        }
    
    data = {}
    for name, (period, interval) in periods.items():
        df = fetch_stock_data(ticker, period, interval)
        if df is not None:
            # Resample 1h to 4h if needed
            if name == "4h" and interval == "1h":
                df = df.resample('4H').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna()
            data[name] = df
    
    return data

# MAG7 stocks and SPY
MAG7_STOCKS = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet Inc.",
    "AMZN": "Amazon.com Inc.",
    "META": "Meta Platforms Inc.",
    "TSLA": "Tesla Inc.",
    "NVDA": "NVIDIA Corporation",
    "SPY": "SPDR S&P 500 ETF"
}

def get_available_tickers():
    """Return dict of available tickers"""
    return MAG7_STOCKS
