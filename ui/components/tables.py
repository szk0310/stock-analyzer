"""テーブルコンポーネント"""
import pandas as pd
import streamlit as st
from data.universe import get_currency_symbol, get_market_label


def render_ranking_table(results: list[dict]) -> None:
    """Top10ランキングテーブルを表示"""
    rows = []
    for r in results:
        ticker = r.get("ticker", "")
        currency = get_currency_symbol(ticker)
        market = get_market_label(ticker)
        price = r.get("current_price")
        if price is not None:
            price_str = f"{currency}{price:,.0f}" if currency == "¥" else f"{currency}{price:,.2f}"
        else:
            price_str = "N/A"

        rows.append({
            "順位": r.get("rank", "-"),
            "銘柄": f"{r.get('name', ticker)} ({ticker})",
            "市場": market,
            "現在価格": price_str,
            "総合スコア": f"{r.get('composite_score', 0):.3f}",
            "テクニカル": f"{r.get('technical_score', 0):.2f}",
            "ファンダ": f"{r.get('fundamental_score', 0):.2f}",
            "バックテスト": f"{r.get('backtest_score', 0):.2f}",
        })

    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_config={
            "順位": st.column_config.NumberColumn(width="small"),
            "銘柄": st.column_config.TextColumn(width="large"),
        },
    )


def render_trade_log(trades: list[dict], currency_symbol: str = "$") -> None:
    """トレードログテーブルを表示"""
    if not trades:
        st.info("トレードが発生しませんでした")
        return

    rows = []
    for t in trades:
        fmt = ",.0f" if currency_symbol == "¥" else ",.2f"
        rows.append({
            "エントリー日": t["entry_date"].strftime("%Y-%m-%d") if hasattr(t["entry_date"], "strftime") else str(t["entry_date"]),
            "決済日": t["exit_date"].strftime("%Y-%m-%d") if hasattr(t["exit_date"], "strftime") else str(t["exit_date"]),
            "買値": f"{currency_symbol}{t['entry_price']:{fmt}}",
            "売値": f"{currency_symbol}{t['exit_price']:{fmt}}",
            "株数": t["shares"],
            "損益(%)": f"{t['pnl_pct']:+.1f}%",
            "状態": "未決済" if t.get("open") else "決済済",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, width="stretch", hide_index=True)


def render_metrics_cards(metrics: dict, currency_symbol: str = "$") -> None:
    """パフォーマンス指標カードを表示"""
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("トータルリターン", f"{metrics.get('total_return', 0):+.1f}%")
    with col2:
        st.metric("シャープレシオ", f"{metrics.get('sharpe_ratio', 0):.2f}")
    with col3:
        st.metric("最大ドローダウン", f"{metrics.get('max_drawdown', 0):.1f}%")
    with col4:
        st.metric("勝率", f"{metrics.get('win_rate', 0):.0f}%")

    col5, col6 = st.columns(2)
    with col5:
        st.metric("プロフィットファクター", f"{metrics.get('profit_factor', 0):.2f}")
    with col6:
        st.metric("トレード数", f"{metrics.get('total_trades', 0)}")
