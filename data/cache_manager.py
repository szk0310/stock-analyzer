"""Parquetファイルキャッシュ（TTL=24時間）"""
import os
import time
import pandas as pd
from config.settings import CACHE_DIR, CACHE_TTL_HOURS


def _cache_path(ticker: str, data_type: str = "price") -> str:
    """キャッシュファイルパスを生成"""
    safe_ticker = ticker.replace(".", "_").replace("-", "_")
    return os.path.join(CACHE_DIR, f"{safe_ticker}_{data_type}.parquet")


def _info_cache_path(ticker: str) -> str:
    """銘柄情報キャッシュファイルパスを生成"""
    safe_ticker = ticker.replace(".", "_").replace("-", "_")
    return os.path.join(CACHE_DIR, f"{safe_ticker}_info.parquet")


def is_cache_valid(ticker: str, data_type: str = "price") -> bool:
    """キャッシュが有効期間内か確認"""
    path = _cache_path(ticker, data_type)
    if not os.path.exists(path):
        return False
    age_hours = (time.time() - os.path.getmtime(path)) / 3600
    return age_hours < CACHE_TTL_HOURS


def save_price_cache(ticker: str, df: pd.DataFrame) -> None:
    """価格データをParquetキャッシュに保存"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = _cache_path(ticker, "price")
    df.to_parquet(path)


def load_price_cache(ticker: str) -> pd.DataFrame | None:
    """価格データをParquetキャッシュから読み込み"""
    if not is_cache_valid(ticker, "price"):
        return None
    path = _cache_path(ticker, "price")
    try:
        return pd.read_parquet(path)
    except Exception:
        return None


def save_info_cache(ticker: str, info: dict) -> None:
    """銘柄情報をキャッシュに保存（dictをDataFrameに変換）"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = _info_cache_path(ticker)
    df = pd.DataFrame([info])
    df.to_parquet(path)


def load_info_cache(ticker: str) -> dict | None:
    """銘柄情報をキャッシュから読み込み"""
    path = _info_cache_path(ticker)
    if not os.path.exists(path):
        return None
    age_hours = (time.time() - os.path.getmtime(path)) / 3600
    if age_hours >= CACHE_TTL_HOURS:
        return None
    try:
        df = pd.read_parquet(path)
        return df.iloc[0].to_dict()
    except Exception:
        return None


def clear_cache() -> int:
    """全キャッシュファイルを削除。削除数を返す"""
    count = 0
    if os.path.exists(CACHE_DIR):
        for f in os.listdir(CACHE_DIR):
            if f.endswith(".parquet"):
                os.remove(os.path.join(CACHE_DIR, f))
                count += 1
    return count
