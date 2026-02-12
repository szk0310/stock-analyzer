"""個別銘柄詳細ページ"""
import streamlit as st
import pandas as pd
from data.fetcher import fetch_price_data, fetch_stock_info
from data.universe import get_currency_symbol, get_market_label
from analysis.technical import compute_indicators, generate_signals
from analysis.fundamental import compute_fundamental_score
from analysis.scoring import generate_buy_suggestion
from backtest.engine import run_backtest
from backtest.strategies import get_strategy
from ui.components.charts import create_candlestick_chart, create_equity_curve_chart, create_score_radar_chart
from ui.components.tables import render_metrics_cards, render_trade_log
from config.settings import BACKTEST_INITIAL_CAPITAL


def render_stock_detail(filters: dict) -> None:
    """個別銘柄詳細ページを描画"""
    # 銘柄選択
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker_input = st.text_input(
            "ティッカーシンボル",
            value=st.session_state.get("selected_ticker", "AAPL"),
            placeholder="例: AAPL, 7203.T",
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze = st.button("分析", type="primary")

    if not ticker_input:
        return

    ticker = ticker_input.strip().upper()
    currency = get_currency_symbol(ticker)
    market = get_market_label(ticker)

    # ランキング結果からデータを探す
    ranking_results = st.session_state.get("ranking_results", [])
    cached_result = None
    for r in ranking_results:
        if r["ticker"] == ticker:
            cached_result = r
            break

    if analyze or cached_result:
        with st.spinner(f"{ticker} を分析中..."):
            # データ取得
            price_df = fetch_price_data(ticker)
            if price_df is None:
                st.error(f"{ticker} のデータを取得できませんでした")
                return

            info = fetch_stock_info(ticker)

            # テクニカル分析
            df_tech = compute_indicators(price_df.copy())
            tech_result = generate_signals(df_tech)

            # ファンダメンタル分析
            fund_result = compute_fundamental_score(info) if info else {"score": 0, "details": {}}

            # バックテスト
            strategy = get_strategy(filters["strategy"])
            bt_result = run_backtest(df_tech.copy(), strategy=strategy)

        # --- ヘッダー ---
        st.header(f"{info.get('shortName', ticker) if info else ticker} ({ticker})")

        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            current_price = info.get("currentPrice") if info else price_df["Close"].iloc[-1]
            if current_price:
                fmt = f"{currency}{current_price:,.0f}" if currency == "¥" else f"{currency}{current_price:,.2f}"
                st.metric("現在価格", fmt)
        with col_b:
            st.metric("市場", market)
        with col_c:
            st.metric("セクター", info.get("sector", "N/A") if info else "N/A")
        with col_d:
            composite = (
                tech_result["score"] * filters["weight_technical"]
                + fund_result["score"] * filters["weight_fundamental"]
                + bt_result["score"] * filters["weight_backtest"]
            )
            st.metric("総合スコア", f"{composite:.3f}")

        st.markdown("---")

        # --- チャートタブ ---
        tab_chart, tab_fund, tab_bt, tab_suggest = st.tabs(
            ["チャート", "ファンダメンタル", "バックテスト", "買い条件"]
        )

        with tab_chart:
            fig = create_candlestick_chart(df_tech, ticker)
            st.plotly_chart(fig, width="stretch")

            # テクニカルシグナルまとめ
            st.subheader("テクニカルシグナル")
            signals = tech_result.get("signals", {})
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"- テクニカルスコア: **{tech_result['score']:.2f}**")
                st.markdown(f"- RSI: **{tech_result.get('rsi', 'N/A')}**")
                st.markdown(f"- SMA20: **{tech_result.get('sma_short', 'N/A')}**")
                st.markdown(f"- SMA50: **{tech_result.get('sma_long', 'N/A')}**")
            with col2:
                for name, active in signals.items():
                    icon = "🟢" if active else "⚪"
                    label = {
                        "golden_cross": "ゴールデンクロス",
                        "rsi_oversold": "RSI売られすぎ",
                        "macd_bullish": "MACD強気",
                        "bb_near_lower": "BB下限付近",
                        "bullish_trend": "強気トレンド",
                    }.get(name, name)
                    st.markdown(f"{icon} {label}")

        with tab_fund:
            st.subheader("ファンダメンタル分析")
            details = fund_result["details"]

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                per = details.get("PER")
                st.metric("PER", f"{per}" if per else "N/A",
                          help=details.get("PER_label", ""))
            with col2:
                pbr = details.get("PBR")
                st.metric("PBR", f"{pbr}" if pbr else "N/A",
                          help=details.get("PBR_label", ""))
            with col3:
                div_y = details.get("dividend_yield")
                st.metric("配当利回り", f"{div_y}%" if div_y else "N/A",
                          help=details.get("dividend_label", ""))
            with col4:
                roe = details.get("ROE")
                st.metric("ROE", f"{roe}%" if roe else "N/A",
                          help=details.get("ROE_label", ""))

            st.metric("ファンダメンタルスコア", f"{fund_result['score']:.2f}")

            # レーダーチャート
            fig = create_score_radar_chart(
                tech_result["score"], fund_result["score"], bt_result["score"]
            )
            st.plotly_chart(fig, width="stretch")

        with tab_bt:
            st.subheader(f"バックテスト結果 ({bt_result['strategy_name']})")

            render_metrics_cards(bt_result["metrics"], currency)

            st.markdown("---")

            # エクイティカーブ
            st.subheader("エクイティカーブ")
            eq_fig = create_equity_curve_chart(
                bt_result["equity_curve"], bt_result["trades"],
                BACKTEST_INITIAL_CAPITAL,
            )
            st.plotly_chart(eq_fig, width="stretch")

            # トレードログ
            st.subheader("トレードログ")
            render_trade_log(bt_result["trades"], currency)

        with tab_suggest:
            st.subheader("買い条件サジェスト")
            result_for_suggest = {
                "ticker": ticker,
                "technical_signals": tech_result,
                "fundamental_details": fund_result["details"],
                "backtest_metrics": bt_result["metrics"],
            }
            suggestions = generate_buy_suggestion(result_for_suggest)
            for s in suggestions:
                st.markdown(f"- {s}")
