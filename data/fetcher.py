"""yfinanceデータ取得（キャッシュ・レートリミット付）"""
import time
import pandas as pd
import yfinance as yf
import streamlit as st
from config.settings import DATA_PERIOD, RATE_LIMIT_DELAY, MEMORY_CACHE_TTL_SECONDS
from data.cache_manager import (
    save_price_cache, load_price_cache,
    save_info_cache, load_info_cache,
)


@st.cache_data(ttl=MEMORY_CACHE_TTL_SECONDS, show_spinner=False)
def fetch_price_data(ticker: str) -> pd.DataFrame | None:
    """価格データを取得（2層キャッシュ: Streamlit in-memory + Parquet）"""
    # Parquetキャッシュ確認
    cached = load_price_cache(ticker)
    if cached is not None:
        return cached

    # Yahoo Financeから取得
    try:
        time.sleep(RATE_LIMIT_DELAY)
        stock = yf.Ticker(ticker)
        df = stock.history(period=DATA_PERIOD)
        if df.empty:
            return None
        # カラム名を正規化
        df.index.name = "Date"
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.dropna(inplace=True)
        if len(df) < 50:  # 最低限のデータ量
            return None
        save_price_cache(ticker, df)
        return df
    except Exception:
        return None


@st.cache_data(ttl=MEMORY_CACHE_TTL_SECONDS, show_spinner=False)
def fetch_stock_info(ticker: str) -> dict | None:
    """銘柄のファンダメンタル情報を取得"""
    # キャッシュ確認
    cached = load_info_cache(ticker)
    if cached is not None:
        return cached

    try:
        time.sleep(RATE_LIMIT_DELAY)
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info or "symbol" not in info:
            return None

        # 必要なフィールドのみ抽出
        extracted = {
            "symbol": info.get("symbol", ticker),
            "shortName": info.get("shortName", ticker),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "currency": info.get("currency", "USD"),
            "trailingPE": info.get("trailingPE"),
            "forwardPE": info.get("forwardPE"),
            "priceToBook": info.get("priceToBook"),
            "dividendYield": info.get("trailingAnnualDividendYield") or info.get("dividendYield"),
            "returnOnEquity": info.get("returnOnEquity"),
            "marketCap": info.get("marketCap"),
            "currentPrice": info.get("currentPrice") or info.get("regularMarketPrice"),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
            "trailingEps": info.get("trailingEps"),
            "revenueGrowth": info.get("revenueGrowth"),
            "profitMargins": info.get("profitMargins"),
        }
        save_info_cache(ticker, extracted)
        return extracted
    except Exception:
        return None


def fetch_batch_prices(tickers: list[str],
                       progress_callback=None) -> dict[str, pd.DataFrame]:
    """複数銘柄の価格データをバッチ取得"""
    results = {}
    for i, ticker in enumerate(tickers):
        df = fetch_price_data(ticker)
        if df is not None:
            results[ticker] = df
        if progress_callback:
            progress_callback(i + 1, len(tickers), ticker)
    return results


def fetch_batch_info(tickers: list[str],
                     progress_callback=None) -> dict[str, dict]:
    """複数銘柄のファンダメンタル情報をバッチ取得"""
    results = {}
    for i, ticker in enumerate(tickers):
        info = fetch_stock_info(ticker)
        if info is not None:
            results[ticker] = info
        if progress_callback:
            progress_callback(i + 1, len(tickers), ticker)
    return results
