"""銘柄ユニバース管理（Wikipedia動的取得 + 静的フォールバック）"""
import requests
from bs4 import BeautifulSoup
import streamlit as st
from config.ticker_lists import NIKKEI_225_FALLBACK, SP500_FALLBACK
from config.settings import MEMORY_CACHE_TTL_SECONDS


@st.cache_data(ttl=MEMORY_CACHE_TTL_SECONDS * 24, show_spinner=False)
def fetch_sp500_tickers() -> list[str]:
    """WikipediaからS&P500銘柄リストを取得"""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        table = soup.find("table", {"id": "constituents"})
        if table is None:
            return SP500_FALLBACK

        tickers = []
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if cols:
                ticker = cols[0].text.strip().replace(".", "-")
                tickers.append(ticker)
        return tickers if len(tickers) > 100 else SP500_FALLBACK
    except Exception:
        return SP500_FALLBACK


@st.cache_data(ttl=MEMORY_CACHE_TTL_SECONDS * 24, show_spinner=False)
def fetch_nikkei225_tickers() -> list[str]:
    """WikipediaからNikkei 225銘柄リストを取得"""
    url = "https://en.wikipedia.org/wiki/Nikkei_225"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Nikkei 225のテーブルを探す
        tickers = []
        for table in soup.find_all("table", class_="wikitable"):
            for row in table.find_all("tr")[1:]:
                cols = row.find_all("td")
                for col in cols:
                    text = col.text.strip()
                    # 4桁の数字（日本株コード）を検出
                    if text.isdigit() and len(text) == 4:
                        tickers.append(f"{text}.T")
                        break

        return tickers if len(tickers) > 100 else NIKKEI_225_FALLBACK
    except Exception:
        return NIKKEI_225_FALLBACK


def get_universe(market: str = "both") -> list[str]:
    """
    銘柄ユニバースを取得

    Args:
        market: "jp" (日経225), "us" (S&P500), "both" (両方)

    Returns:
        ティッカーシンボルのリスト
    """
    tickers = []
    if market in ("jp", "both"):
        tickers.extend(fetch_nikkei225_tickers())
    if market in ("us", "both"):
        tickers.extend(fetch_sp500_tickers())
    return list(dict.fromkeys(tickers))  # 重複除去（順序保持）


def get_currency_symbol(ticker: str) -> str:
    """ティッカーから通貨記号を推定"""
    if ticker.endswith(".T"):
        return "¥"
    return "$"


def get_market_label(ticker: str) -> str:
    """ティッカーから市場ラベルを取得"""
    if ticker.endswith(".T"):
        return "JP"
    return "US"
