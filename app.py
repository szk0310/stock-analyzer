"""Stock Analyzer - 株式分析・バックテストWebアプリ"""
import streamlit as st

st.set_page_config(
    page_title="Stock Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui.components.filters import render_sidebar_filters
from ui.pages.dashboard import render_dashboard
from ui.pages.stock_detail import render_stock_detail
from ui.pages.backtest_results import render_backtest_page


def main():
    # サイドバーフィルター
    filters = render_sidebar_filters()

    # ページナビゲーション
    st.sidebar.markdown("---")
    page = st.sidebar.radio(
        "ページ",
        options=["dashboard", "stock_detail", "backtest"],
        format_func=lambda x: {
            "dashboard": "📊 ダッシュボード",
            "stock_detail": "🔍 個別銘柄分析",
            "backtest": "📈 バックテスト結果",
        }[x],
        index=["dashboard", "stock_detail", "backtest"].index(
            st.session_state.get("page", "dashboard")
        ),
    )
    st.session_state["page"] = page

    # ページ描画
    if page == "dashboard":
        render_dashboard(filters)
    elif page == "stock_detail":
        render_stock_detail(filters)
    elif page == "backtest":
        render_backtest_page(filters)


if __name__ == "__main__":
    main()
