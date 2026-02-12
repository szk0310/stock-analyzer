"""バックテスト結果ページ"""
import streamlit as st
import pandas as pd
from data.fetcher import fetch_price_data
from analysis.technical import compute_indicators
from backtest.engine import run_backtest
from backtest.strategies import get_strategy
from ui.components.charts import create_candlestick_chart, create_equity_curve_chart
from ui.components.tables import render_metrics_cards, render_trade_log
from data.universe import get_currency_symbol
from config.settings import BACKTEST_INITIAL_CAPITAL


def render_backtest_page(filters: dict) -> None:
    """バックテスト結果ページを描画"""
    st.header("バックテスト比較")

    # 入力
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker = st.text_input(
            "ティッカーシンボル",
            value=st.session_state.get("selected_ticker", "AAPL"),
            key="bt_ticker",
            placeholder="例: AAPL, 7203.T",
        ).strip().upper()
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        run = st.button("バックテスト実行", type="primary")

    if not ticker or not run:
        # ランキング結果からのバックテスト一覧を表示
        _render_ranking_backtest_summary()
        return

    currency = get_currency_symbol(ticker)

    with st.spinner(f"{ticker} のバックテストを実行中..."):
        price_df = fetch_price_data(ticker)
        if price_df is None:
            st.error(f"{ticker} のデータを取得できませんでした")
            return

        df_tech = compute_indicators(price_df.copy())

        # 3戦略を比較
        strategies = ["hybrid", "ma_cross", "rsi"]
        results = {}
        for s_name in strategies:
            strategy = get_strategy(s_name)
            results[s_name] = run_backtest(df_tech.copy(), strategy=strategy)

    # 戦略比較テーブル
    st.subheader("戦略比較")
    comparison_rows = []
    for s_name, bt in results.items():
        m = bt["metrics"]
        comparison_rows.append({
            "戦略": bt["strategy_name"],
            "リターン(%)": f"{m['total_return']:+.1f}",
            "シャープレシオ": f"{m['sharpe_ratio']:.2f}",
            "最大DD(%)": f"{m['max_drawdown']:.1f}",
            "勝率(%)": f"{m['win_rate']:.0f}",
            "PF": f"{m['profit_factor']:.2f}",
            "トレード数": m["total_trades"],
            "スコア": f"{bt['score']:.3f}",
        })
    st.dataframe(pd.DataFrame(comparison_rows), width="stretch", hide_index=True)

    st.markdown("---")

    # 各戦略の詳細タブ
    tab_names = [results[s]["strategy_name"] for s in strategies]
    tabs = st.tabs(tab_names)

    for tab, s_name in zip(tabs, strategies):
        bt = results[s_name]
        with tab:
            render_metrics_cards(bt["metrics"], currency)

            st.subheader("エクイティカーブ")
            eq_fig = create_equity_curve_chart(
                bt["equity_curve"], bt["trades"], BACKTEST_INITIAL_CAPITAL,
            )
            st.plotly_chart(eq_fig, width="stretch")

            st.subheader("トレードログ")
            render_trade_log(bt["trades"], currency)


def _render_ranking_backtest_summary() -> None:
    """ランキング結果のバックテストサマリーを表示"""
    results = st.session_state.get("ranking_results", [])
    if not results:
        st.markdown(
            """
            **使い方:**
            1. ティッカーシンボルを入力して「バックテスト実行」をクリック
            2. 3つの戦略（ハイブリッド、MAクロス、RSI）を自動比較
            3. または、ダッシュボードで分析を実行すると、ランキング結果のバックテスト一覧がここに表示されます
            """
        )
        return

    st.subheader("ランキング銘柄のバックテスト結果")
    rows = []
    for r in results:
        bt = r.get("backtest_metrics", {})
        rows.append({
            "順位": r.get("rank", "-"),
            "銘柄": f"{r.get('name', r['ticker'])} ({r['ticker']})",
            "リターン(%)": f"{bt.get('total_return', 0):+.1f}",
            "シャープレシオ": f"{bt.get('sharpe_ratio', 0):.2f}",
            "最大DD(%)": f"{bt.get('max_drawdown', 0):.1f}",
            "勝率(%)": f"{bt.get('win_rate', 0):.0f}",
            "BTスコア": f"{r.get('backtest_score', 0):.3f}",
        })

    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
