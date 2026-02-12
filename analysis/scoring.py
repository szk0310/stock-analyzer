"""複合スコアリング・ランキングエンジン"""
import pandas as pd
from config.settings import (
    WEIGHT_TECHNICAL, WEIGHT_FUNDAMENTAL, WEIGHT_BACKTEST,
    PRE_SCREEN_TOP_N, FINAL_TOP_N,
)
from data.universe import get_currency_symbol


def compute_composite_score(
    technical_score: float,
    fundamental_score: float,
    backtest_score: float = 0.0,
) -> float:
    """
    複合スコア算出:
    テクニカル×0.5 + ファンダメンタル×0.3 + バックテスト×0.2
    """
    return round(
        technical_score * WEIGHT_TECHNICAL
        + fundamental_score * WEIGHT_FUNDAMENTAL
        + backtest_score * WEIGHT_BACKTEST,
        4,
    )


def pre_screen(results: list[dict], top_n: int = PRE_SCREEN_TOP_N) -> list[dict]:
    """
    テクニカル+ファンダメンタルで上位N銘柄に絞り込み
    （バックテスト前のフィルタリング）
    """
    for r in results:
        r["pre_score"] = (
            r.get("technical_score", 0) * WEIGHT_TECHNICAL
            + r.get("fundamental_score", 0) * WEIGHT_FUNDAMENTAL
        ) / (WEIGHT_TECHNICAL + WEIGHT_FUNDAMENTAL)

    sorted_results = sorted(results, key=lambda x: x["pre_score"], reverse=True)
    return sorted_results[:top_n]


def final_ranking(results: list[dict], top_n: int = FINAL_TOP_N) -> list[dict]:
    """
    最終ランキング（バックテスト込み）
    """
    for r in results:
        r["composite_score"] = compute_composite_score(
            r.get("technical_score", 0),
            r.get("fundamental_score", 0),
            r.get("backtest_score", 0),
        )

    sorted_results = sorted(
        results, key=lambda x: x["composite_score"], reverse=True
    )
    # ランク付与
    for i, r in enumerate(sorted_results[:top_n], 1):
        r["rank"] = i

    return sorted_results[:top_n]


def generate_buy_suggestion(result: dict) -> list[str]:
    """
    買い条件サジェストテキストを生成

    Args:
        result: スコアリング結果の辞書

    Returns:
        list[str]: サジェストテキストのリスト
    """
    suggestions = []
    ticker = result.get("ticker", "")
    currency = get_currency_symbol(ticker)
    fund = result.get("fundamental_details", {})
    tech = result.get("technical_signals", {})
    signals = tech.get("signals", {})

    # ファンダメンタル系
    per = fund.get("PER")
    if per is not None:
        if per <= 15:
            suggestions.append(f"PERは{per}（15以下で割安）")
        else:
            suggestions.append(f"PERは{per}")

    pbr = fund.get("PBR")
    if pbr is not None:
        if pbr < 1.0:
            suggestions.append(f"PBRは{pbr}（1.0以下で資産価値に対して割安）")

    div = fund.get("dividend_yield")
    if div is not None and div >= 2.0:
        suggestions.append(f"配当利回り{div}%（魅力的な水準）")

    roe = fund.get("ROE")
    if roe is not None and roe >= 15.0:
        suggestions.append(f"ROE {roe}%（高い資本効率）")

    # テクニカル系
    rsi = tech.get("rsi")
    if rsi is not None and rsi < 30:
        suggestions.append(f"RSI {rsi}で売られすぎ → 反発の可能性")

    if signals.get("golden_cross"):
        suggestions.append("ゴールデンクロス検出（SMA20がSMA50を上抜け）")

    if signals.get("macd_bullish"):
        suggestions.append("MACDが強気シグナル（買いサイン）")

    if signals.get("bb_near_lower"):
        suggestions.append("ボリンジャーバンド下限付近（反発の可能性）")

    # エントリーポイント
    sma_long = tech.get("sma_long")
    if sma_long is not None:
        if currency == "¥":
            price_str = f"{currency}{sma_long:,.0f}"
        else:
            price_str = f"{currency}{sma_long:,.2f}"
        suggestions.append(f"推奨エントリー: SMA50サポート（{price_str}）への押し目で買い")

    # バックテスト結果
    bt = result.get("backtest_metrics", {})
    total_return = bt.get("total_return")
    if total_return is not None:
        suggestions.append(
            f"バックテスト2年リターン: {total_return:+.1f}%"
        )

    return suggestions if suggestions else ["現時点で特筆すべきシグナルなし"]
