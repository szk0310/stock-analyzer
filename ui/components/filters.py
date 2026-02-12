"""サイドバーフィルター"""
import streamlit as st


def render_sidebar_filters() -> dict:
    """サイドバーフィルターを描画し、設定値を返す"""
    st.sidebar.title("Stock Analyzer")
    st.sidebar.markdown("---")

    # 市場選択
    market = st.sidebar.selectbox(
        "対象市場",
        options=["both", "us", "jp"],
        format_func=lambda x: {"both": "日米両方", "us": "S&P 500 (米国)", "jp": "日経225 (日本)"}[x],
        index=0,
    )

    # 戦略選択
    strategy = st.sidebar.selectbox(
        "バックテスト戦略",
        options=["hybrid", "ma_cross", "rsi"],
        format_func=lambda x: {
            "hybrid": "ハイブリッド（推奨）",
            "ma_cross": "MA クロス",
            "rsi": "RSI 逆張り",
        }[x],
        index=0,
    )

    st.sidebar.markdown("---")

    # スコア重み調整
    st.sidebar.subheader("スコア重み調整")
    w_tech = st.sidebar.slider("テクニカル重み", 0.0, 1.0, 0.5, 0.05)
    w_fund = st.sidebar.slider("ファンダメンタル重み", 0.0, 1.0, 0.3, 0.05)
    w_bt = st.sidebar.slider("バックテスト重み", 0.0, 1.0, 0.2, 0.05)

    # 正規化
    total = w_tech + w_fund + w_bt
    if total > 0:
        w_tech /= total
        w_fund /= total
        w_bt /= total

    st.sidebar.markdown("---")

    # 表示設定
    top_n = st.sidebar.slider("ランキング表示数", 5, 30, 10)
    pre_screen_n = st.sidebar.slider("バックテスト対象数", 10, 100, 50)

    st.sidebar.markdown("---")

    # キャッシュ管理
    if st.sidebar.button("キャッシュクリア"):
        from data.cache_manager import clear_cache
        count = clear_cache()
        st.cache_data.clear()
        st.sidebar.success(f"{count}ファイルのキャッシュをクリアしました")

    return {
        "market": market,
        "strategy": strategy,
        "weight_technical": w_tech,
        "weight_fundamental": w_fund,
        "weight_backtest": w_bt,
        "top_n": top_n,
        "pre_screen_n": pre_screen_n,
    }
