"""テクニカル指標（SMA, RSI, MACD, BB）+ シグナル生成"""
import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from config.settings import (
    SMA_SHORT, SMA_LONG, RSI_PERIOD, RSI_OVERSOLD,
    MACD_FAST, MACD_SLOW, MACD_SIGNAL, BB_PERIOD, BB_STD,
)


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """テクニカル指標を計算してDataFrameに追加"""
    close = df["Close"]

    # SMA
    df["SMA_short"] = SMAIndicator(close, window=SMA_SHORT).sma_indicator()
    df["SMA_long"] = SMAIndicator(close, window=SMA_LONG).sma_indicator()

    # RSI
    df["RSI"] = RSIIndicator(close, window=RSI_PERIOD).rsi()

    # MACD
    macd = MACD(close, window_slow=MACD_SLOW, window_fast=MACD_FAST,
                window_sign=MACD_SIGNAL)
    df["MACD"] = macd.macd()
    df["MACD_signal"] = macd.macd_signal()
    df["MACD_hist"] = macd.macd_diff()

    # Bollinger Bands
    bb = BollingerBands(close, window=BB_PERIOD, window_dev=BB_STD)
    df["BB_upper"] = bb.bollinger_hband()
    df["BB_middle"] = bb.bollinger_mavg()
    df["BB_lower"] = bb.bollinger_lband()

    return df


def generate_signals(df: pd.DataFrame) -> dict:
    """
    最新のテクニカルシグナルを生成

    Returns:
        dict: 各シグナルのbool値とスコア
    """
    if len(df) < SMA_LONG + 5:
        return {"score": 0.0, "signals": {}}

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    signals = {}

    # ゴールデンクロス（SMA20/50）: +0.25
    sma_short_now = latest.get("SMA_short")
    sma_long_now = latest.get("SMA_long")
    sma_short_prev = prev.get("SMA_short")
    sma_long_prev = prev.get("SMA_long")

    golden_cross = False
    if all(pd.notna([sma_short_now, sma_long_now, sma_short_prev, sma_long_prev])):
        golden_cross = (sma_short_prev <= sma_long_prev) and (sma_short_now > sma_long_now)
        # 直近5日以内のクロスも検出
        if not golden_cross:
            for i in range(2, min(6, len(df))):
                p = df.iloc[-i]
                p_prev = df.iloc[-i - 1] if i + 1 <= len(df) else None
                if p_prev is not None:
                    s_s = p.get("SMA_short")
                    s_l = p.get("SMA_long")
                    s_s_p = p_prev.get("SMA_short")
                    s_l_p = p_prev.get("SMA_long")
                    if all(pd.notna([s_s, s_l, s_s_p, s_l_p])):
                        if s_s_p <= s_l_p and s_s > s_l:
                            golden_cross = True
                            break
    signals["golden_cross"] = golden_cross

    # RSI < 30（売られすぎ）: +0.20
    rsi = latest.get("RSI")
    signals["rsi_oversold"] = pd.notna(rsi) and rsi < RSI_OVERSOLD

    # MACD強気クロスオーバー: +0.25
    macd_now = latest.get("MACD")
    macd_sig_now = latest.get("MACD_signal")
    macd_prev = prev.get("MACD")
    macd_sig_prev = prev.get("MACD_signal")

    macd_bullish = False
    if all(pd.notna([macd_now, macd_sig_now, macd_prev, macd_sig_prev])):
        macd_bullish = (macd_prev <= macd_sig_prev) and (macd_now > macd_sig_now)
        # 直近5日以内
        if not macd_bullish:
            for i in range(2, min(6, len(df))):
                p = df.iloc[-i]
                p_prev = df.iloc[-i - 1] if i + 1 <= len(df) else None
                if p_prev is not None:
                    m = p.get("MACD")
                    ms = p.get("MACD_signal")
                    mp = p_prev.get("MACD")
                    msp = p_prev.get("MACD_signal")
                    if all(pd.notna([m, ms, mp, msp])):
                        if mp <= msp and m > ms:
                            macd_bullish = True
                            break
    signals["macd_bullish"] = macd_bullish

    # BBロワーバンド付近: +0.15
    close = latest["Close"]
    bb_lower = latest.get("BB_lower")
    bb_upper = latest.get("BB_upper")
    near_lower = False
    if pd.notna(bb_lower) and pd.notna(bb_upper) and bb_upper != bb_lower:
        bb_position = (close - bb_lower) / (bb_upper - bb_lower)
        near_lower = bb_position < 0.2
    signals["bb_near_lower"] = near_lower

    # トレンド=強気（価格がSMA_longより上）: +0.15
    bullish_trend = False
    if pd.notna(sma_long_now):
        bullish_trend = close > sma_long_now
    signals["bullish_trend"] = bullish_trend

    # スコア算出
    score = 0.0
    if signals["golden_cross"]:
        score += 0.25
    if signals["rsi_oversold"]:
        score += 0.20
    if signals["macd_bullish"]:
        score += 0.25
    if signals["bb_near_lower"]:
        score += 0.15
    if signals["bullish_trend"]:
        score += 0.15

    return {
        "score": round(score, 3),
        "signals": signals,
        "rsi": round(rsi, 1) if pd.notna(rsi) else None,
        "sma_short": round(sma_short_now, 2) if pd.notna(sma_short_now) else None,
        "sma_long": round(sma_long_now, 2) if pd.notna(sma_long_now) else None,
    }
