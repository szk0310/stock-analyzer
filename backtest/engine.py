"""カスタムバックテストエンジン"""
import pandas as pd
import numpy as np
from config.settings import BACKTEST_INITIAL_CAPITAL, BACKTEST_COMMISSION
from analysis.technical import compute_indicators
from backtest.strategies import BaseStrategy, get_strategy
from backtest.metrics import compute_all_metrics, compute_backtest_score


def run_backtest(
    df: pd.DataFrame,
    strategy: BaseStrategy | None = None,
    initial_capital: float = BACKTEST_INITIAL_CAPITAL,
    commission: float = BACKTEST_COMMISSION,
) -> dict:
    """
    バックテストを実行

    Args:
        df: OHLCVデータ（テクニカル指標付き）
        strategy: 戦略オブジェクト（Noneの場合はハイブリッド）
        initial_capital: 初期資金
        commission: 手数料率

    Returns:
        dict: バックテスト結果
    """
    if strategy is None:
        strategy = get_strategy("hybrid")

    # テクニカル指標が無ければ計算
    if "SMA_short" not in df.columns:
        df = compute_indicators(df.copy())

    cash = initial_capital
    position = 0  # 保有株数
    entry_price = 0.0
    equity_history = []
    trades = []
    signals_log = []

    for i in range(len(df)):
        close = df["Close"].iloc[i]
        date = df.index[i]

        signal = strategy.generate_signal(df, i)

        # 買いシグナル（ポジションなし → 買い）
        if signal == 1 and position == 0:
            # 全資金で買い（手数料考慮）
            shares = int(cash * (1 - commission) / close)
            if shares > 0:
                cost = shares * close * (1 + commission)
                cash -= cost
                position = shares
                entry_price = close
                signals_log.append({
                    "date": date, "action": "BUY",
                    "price": close, "shares": shares,
                })

        # 売りシグナル（ポジションあり → 売り）
        elif signal == -1 and position > 0:
            revenue = position * close * (1 - commission)
            pnl = revenue - (position * entry_price * (1 + commission))
            pnl_pct = ((close / entry_price) - 1) * 100

            trades.append({
                "entry_date": signals_log[-1]["date"] if signals_log else date,
                "exit_date": date,
                "entry_price": entry_price,
                "exit_price": close,
                "shares": position,
                "pnl": pnl,
                "pnl_pct": round(pnl_pct, 2),
            })
            signals_log.append({
                "date": date, "action": "SELL",
                "price": close, "shares": position,
            })

            cash += revenue
            position = 0
            entry_price = 0.0

        # エクイティ計算
        equity = cash + position * close
        equity_history.append({"date": date, "equity": equity})

    # 未決済ポジションの評価
    if position > 0:
        final_close = df["Close"].iloc[-1]
        pnl_pct = ((final_close / entry_price) - 1) * 100
        trades.append({
            "entry_date": signals_log[-1]["date"] if signals_log else df.index[-1],
            "exit_date": df.index[-1],
            "entry_price": entry_price,
            "exit_price": final_close,
            "shares": position,
            "pnl": position * final_close * (1 - commission) - position * entry_price * (1 + commission),
            "pnl_pct": round(pnl_pct, 2),
            "open": True,
        })

    equity_df = pd.DataFrame(equity_history).set_index("date")
    equity_curve = equity_df["equity"]

    metrics = compute_all_metrics(equity_curve, trades)
    bt_score = compute_backtest_score(metrics)

    return {
        "metrics": metrics,
        "score": bt_score,
        "equity_curve": equity_curve,
        "trades": trades,
        "signals": signals_log,
        "strategy_name": strategy.name,
    }
