"""ファンダメンタル指標（PER, PBR, 配当利回り, ROE）"""
import pandas as pd
from config.settings import (
    PER_CHEAP_MAX, PER_VERY_CHEAP_MAX, PER_MODERATE_MAX,
    PBR_CHEAP_MAX, PBR_MODERATE_MAX,
    DIVIDEND_HIGH, DIVIDEND_MODERATE,
    ROE_HIGH, ROE_MODERATE,
)


def compute_fundamental_score(info: dict) -> dict:
    """
    ファンダメンタルスコアを計算

    Args:
        info: yfinanceの銘柄情報dict

    Returns:
        dict: スコアと個別指標の詳細
    """
    score = 0.0
    details = {}

    # PER (Price to Earnings Ratio): max +0.30
    pe = info.get("trailingPE") or info.get("forwardPE")
    if pe is not None and isinstance(pe, (int, float)) and pe > 0:
        details["PER"] = round(pe, 1)
        if PER_VERY_CHEAP_MAX <= pe <= PER_CHEAP_MAX:
            score += 0.30
            details["PER_label"] = "割安"
        elif PER_CHEAP_MAX < pe <= PER_MODERATE_MAX:
            score += 0.15
            details["PER_label"] = "適正"
        else:
            details["PER_label"] = "割高" if pe > PER_MODERATE_MAX else "低すぎ"
    else:
        details["PER"] = None
        details["PER_label"] = "N/A"

    # PBR (Price to Book Ratio): max +0.20
    pbr = info.get("priceToBook")
    if pbr is not None and isinstance(pbr, (int, float)) and pbr > 0:
        details["PBR"] = round(pbr, 2)
        if pbr < PBR_CHEAP_MAX:
            score += 0.20
            details["PBR_label"] = "割安"
        elif pbr <= PBR_MODERATE_MAX:
            score += 0.10
            details["PBR_label"] = "適正"
        else:
            details["PBR_label"] = "割高"
    else:
        details["PBR"] = None
        details["PBR_label"] = "N/A"

    # 配当利回り: max +0.25
    div_yield = info.get("dividendYield")
    if div_yield is not None and isinstance(div_yield, (int, float)):
        div_pct = div_yield * 100  # yfinanceは小数で返す
        # サニティチェック: 20%超は異常値として除外
        if div_pct > 20:
            div_pct = None
    else:
        div_pct = None

    if div_pct is not None:
        details["dividend_yield"] = round(div_pct, 2)
        if div_pct >= DIVIDEND_HIGH:
            score += 0.25
            details["dividend_label"] = "高配当"
        elif div_pct >= DIVIDEND_MODERATE:
            score += 0.15
            details["dividend_label"] = "適正"
        else:
            details["dividend_label"] = "低配当"
    else:
        details["dividend_yield"] = None
        details["dividend_label"] = "N/A"

    # ROE (Return on Equity): max +0.25
    roe = info.get("returnOnEquity")
    if roe is not None and isinstance(roe, (int, float)):
        roe_pct = roe * 100  # yfinanceは小数で返す
        details["ROE"] = round(roe_pct, 1)
        if roe_pct >= ROE_HIGH:
            score += 0.25
            details["ROE_label"] = "優秀"
        elif roe_pct >= ROE_MODERATE:
            score += 0.15
            details["ROE_label"] = "良好"
        else:
            details["ROE_label"] = "低い"
    else:
        details["ROE"] = None
        details["ROE_label"] = "N/A"

    return {
        "score": round(score, 3),
        "details": details,
    }
