"""パフォーマンス指標（シャープレシオ, ドローダウン等）"""
import numpy as np
import pandas as pd
from config.settings import RISK_FREE_RATE, BT_WEIGHT_RETURN, BT_WEIGHT_SHARPE, BT_WEIGHT_DRAWDOWN


def compute_total_return(equity_curve: pd.Series) -> float:
    """トータルリターン（%）"""
    if len(equity_curve) < 2 or equity_curve.iloc[0] == 0:
        return 0.0
    return ((equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1) * 100


def compute_sharpe_ratio(equity_curve: pd.Series, risk_free_rate: float = RISK_FREE_RATE) -> float:
    """年率シャープレシオ"""
    if len(equity_curve) < 2:
        return 0.0
    daily_returns = equity_curve.pct_change().dropna()
    if len(daily_returns) == 0 or daily_returns.std() == 0:
        return 0.0
    daily_rf = risk_free_rate / 252
    excess = daily_returns - daily_rf
    return float(excess.mean() / excess.std() * np.sqrt(252))


def compute_max_drawdown(equity_curve: pd.Series) -> float:
    """最大ドローダウン（%、負の値）"""
    if len(equity_curve) < 2:
        return 0.0
    peak = equity_curve.cummax()
    drawdown = (equity_curve - peak) / peak * 100
    return float(drawdown.min())


def compute_win_rate(trades: list[dict]) -> float:
    """勝率"""
    if not trades:
        return 0.0
    wins = sum(1 for t in trades if t.get("pnl", 0) > 0)
    return wins / len(trades) * 100


def compute_profit_factor(trades: list[dict]) -> float:
    """プロフィットファクター"""
    if not trades:
        return 0.0
    gross_profit = sum(t["pnl"] for t in trades if t.get("pnl", 0) > 0)
    gross_loss = abs(sum(t["pnl"] for t in trades if t.get("pnl", 0) < 0))
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def compute_all_metrics(equity_curve: pd.Series, trades: list[dict]) -> dict:
    """全指標を一括計算"""
    return {
        "total_return": round(compute_total_return(equity_curve), 2),
        "sharpe_ratio": round(compute_sharpe_ratio(equity_curve), 2),
        "max_drawdown": round(compute_max_drawdown(equity_curve), 2),
        "win_rate": round(compute_win_rate(trades), 1),
        "profit_factor": round(compute_profit_factor(trades), 2),
        "total_trades": len(trades),
    }


def compute_backtest_score(metrics: dict) -> float:
    """
    バックテストスコア (0.0-1.0)
    - トータルリターン: 40%ウェイト
    - シャープレシオ: 30%ウェイト
    - 最大ドローダウン（ペナルティ）: 30%ウェイト
    """
    # リターンスコア: -20%~+100% → 0~1
    total_return = metrics.get("total_return", 0)
    return_score = np.clip((total_return + 20) / 120, 0, 1)

    # シャープスコア: -1~+3 → 0~1
    sharpe = metrics.get("sharpe_ratio", 0)
    sharpe_score = np.clip((sharpe + 1) / 4, 0, 1)

    # ドローダウンスコア: -50%~0% → 0~1（ドローダウンが小さいほど高スコア）
    max_dd = metrics.get("max_drawdown", 0)  # 負の値
    dd_score = np.clip(1 + max_dd / 50, 0, 1)

    score = (
        return_score * BT_WEIGHT_RETURN
        + sharpe_score * BT_WEIGHT_SHARPE
        + dd_score * BT_WEIGHT_DRAWDOWN
    )
    return round(float(score), 3)
