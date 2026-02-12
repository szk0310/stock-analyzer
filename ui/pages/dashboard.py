"""メインダッシュボード（Top10表示）"""
import streamlit as st
import pandas as pd
from data.universe import get_universe, get_currency_symbol
from data.fetcher import fetch_price_data, fetch_stock_info
from analysis.technical import compute_indicators, generate_signals
from analysis.fundamental import compute_fundamental_score
from analysis.scoring import pre_screen, final_ranking, generate_buy_suggestion
from backtest.engine import run_backtest
from backtest.strategies import get_strategy
from ui.components.tables import render_ranking_table
from ui.components.charts import create_score_radar_chart


def run_analysis_pipeline(filters: dict) -> list[dict]:
    """分析パイプラインを実行"""
    market = filters["market"]
    strategy_name = filters["strategy"]
    pre_screen_n = filters["pre_screen_n"]
    top_n = filters["top_n"]

    # [1] 銘柄ユニバース取得
    tickers = get_universe(market)
    st.info(f"対象銘柄数: {len(tickers)}")

    # [2-4] データ取得 + テクニカル + ファンダメンタル分析
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, ticker in enumerate(tickers):
        progress_bar.progress((i + 1) / len(tickers))
        status_text.text(f"分析中: {ticker} ({i+1}/{len(tickers)})")

        # 価格データ取得
        price_df = fetch_price_data(ticker)
        if price_df is None:
            continue

        # ファンダメンタル情報取得
        info = fetch_stock_info(ticker)
        if info is None:
            continue

        # テクニカル分析
        df_tech = compute_indicators(price_df.copy())
        tech_result = generate_signals(df_tech)

        # ファンダメンタル分析
        fund_result = compute_fundamental_score(info)

        results.append({
            "ticker": ticker,
            "name": info.get("shortName", ticker),
            "current_price": info.get("currentPrice"),
            "currency": info.get("currency", "USD"),
            "sector": info.get("sector", "N/A"),
            "technical_score": tech_result["score"],
            "fundamental_score": fund_result["score"],
            "technical_signals": tech_result,
            "fundamental_details": fund_result["details"],
            "price_df": df_tech,
        })

    progress_bar.empty()
    status_text.empty()

    if not results:
        st.error("データを取得できませんでした。ネットワーク接続を確認してください。")
        return []

    # [5] 上位N銘柄に絞り込み
    screened = pre_screen(results, top_n=pre_screen_n)
    st.info(f"プレスクリーニング完了: {len(screened)}銘柄をバックテスト対象に選定")

    # [6] バックテスト実行
    strategy = get_strategy(strategy_name)
    bt_progress = st.progress(0)
    bt_status = st.empty()

    for i, r in enumerate(screened):
        bt_progress.progress((i + 1) / len(screened))
        bt_status.text(f"バックテスト中: {r['ticker']} ({i+1}/{len(screened)})")

        bt_result = run_backtest(r["price_df"].copy(), strategy=strategy)
        r["backtest_score"] = bt_result["score"]
        r["backtest_metrics"] = bt_result["metrics"]
        r["backtest_result"] = bt_result

    bt_progress.empty()
    bt_status.empty()

    # [7-8] 最終ランキング + 買い条件サジェスト
    ranked = final_ranking(screened, top_n=top_n)

    for r in ranked:
        r["suggestions"] = generate_buy_suggestion(r)

    return ranked


def render_dashboard(filters: dict) -> None:
    """ダッシュボードページを描画"""
    st.header("Top 銘柄ランキング")

    # セッション状態で結果を保持
    if st.button("分析を実行", type="primary"):
        with st.spinner("分析パイプラインを実行中..."):
            results = run_analysis_pipeline(filters)
            st.session_state["ranking_results"] = results

    results = st.session_state.get("ranking_results", [])

    if not results:
        st.markdown(
            """
            **使い方:**
            1. サイドバーで市場と戦略を選択
            2. 「分析を実行」ボタンをクリック
            3. 分析完了後、ランキングが表示されます

            > 初回実行はデータ取得に時間がかかります（キャッシュ後は高速化されます）
            """
        )
        return

    # ランキングテーブル
    render_ranking_table(results)

    st.markdown("---")

    # 各銘柄の買い条件サジェスト
    st.subheader("買い条件サジェスト")
    for r in results:
        ticker = r["ticker"]
        name = r.get("name", ticker)
        rank = r.get("rank", "-")

        with st.expander(f"#{rank} {name} ({ticker}) - スコア: {r.get('composite_score', 0):.3f}"):
            col1, col2 = st.columns([2, 1])

            with col1:
                suggestions = r.get("suggestions", [])
                for s in suggestions:
                    st.markdown(f"- {s}")

            with col2:
                fig = create_score_radar_chart(
                    r.get("technical_score", 0),
                    r.get("fundamental_score", 0),
                    r.get("backtest_score", 0),
                )
                st.plotly_chart(fig, width="stretch")

            # 詳細ボタン
            if st.button(f"詳細を見る", key=f"detail_{ticker}"):
                st.session_state["selected_ticker"] = ticker
                st.session_state["page"] = "stock_detail"
                st.rerun()
