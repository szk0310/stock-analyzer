"""Plotlyチャートビルダー"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from data.universe import get_currency_symbol


def create_candlestick_chart(df: pd.DataFrame, ticker: str, show_bb: bool = True, show_sma: bool = True) -> go.Figure:
    """ローソク足チャート（テクニカル指標オーバーレイ付き）"""
    currency = get_currency_symbol(ticker)

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=("Price", "RSI", "MACD"),
    )

    # ローソク足
    fig.add_trace(
        go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"], name="Price",
        ),
        row=1, col=1,
    )

    # SMA
    if show_sma and "SMA_short" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["SMA_short"], name="SMA20",
                       line=dict(color="orange", width=1)),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df["SMA_long"], name="SMA50",
                       line=dict(color="blue", width=1)),
            row=1, col=1,
        )

    # Bollinger Bands
    if show_bb and "BB_upper" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["BB_upper"], name="BB Upper",
                       line=dict(color="gray", width=0.5, dash="dash"),
                       showlegend=False),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df["BB_lower"], name="BB Lower",
                       line=dict(color="gray", width=0.5, dash="dash"),
                       fill="tonexty", fillcolor="rgba(128,128,128,0.1)",
                       showlegend=False),
            row=1, col=1,
        )

    # RSI
    if "RSI" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["RSI"], name="RSI",
                       line=dict(color="purple", width=1)),
            row=2, col=1,
        )
        fig.add_hline(y=70, line_dash="dash", line_color="red",
                      opacity=0.5, row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green",
                      opacity=0.5, row=2, col=1)

    # MACD
    if "MACD" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["MACD"], name="MACD",
                       line=dict(color="blue", width=1)),
            row=3, col=1,
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df["MACD_signal"], name="Signal",
                       line=dict(color="red", width=1)),
            row=3, col=1,
        )
        colors = ["green" if v >= 0 else "red" for v in df["MACD_hist"].fillna(0)]
        fig.add_trace(
            go.Bar(x=df.index, y=df["MACD_hist"], name="Histogram",
                   marker_color=colors, showlegend=False),
            row=3, col=1,
        )

    fig.update_layout(
        height=700,
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=20, t=40, b=20),
    )
    fig.update_yaxes(title_text=f"Price ({currency})", row=1, col=1)
    fig.update_yaxes(title_text="RSI", row=2, col=1)
    fig.update_yaxes(title_text="MACD", row=3, col=1)

    return fig


def create_equity_curve_chart(equity_curve: pd.Series, trades: list[dict],
                              initial_capital: float) -> go.Figure:
    """エクイティカーブチャート"""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=equity_curve.index, y=equity_curve.values,
            name="Portfolio Value",
            line=dict(color="blue", width=2),
            fill="tozeroy", fillcolor="rgba(0,100,255,0.1)",
        )
    )

    # 初期資金ライン
    fig.add_hline(
        y=initial_capital, line_dash="dash", line_color="gray",
        annotation_text=f"Initial: {initial_capital:,.0f}",
    )

    # トレードマーカー
    for trade in trades:
        fig.add_trace(
            go.Scatter(
                x=[trade["entry_date"]], y=[initial_capital],
                mode="markers", name="Buy",
                marker=dict(symbol="triangle-up", size=10, color="green"),
                showlegend=False,
            )
        )
        if not trade.get("open", False):
            fig.add_trace(
                go.Scatter(
                    x=[trade["exit_date"]], y=[initial_capital],
                    mode="markers", name="Sell",
                    marker=dict(symbol="triangle-down", size=10, color="red"),
                    showlegend=False,
                )
            )

    fig.update_layout(
        height=400,
        template="plotly_white",
        yaxis_title="Portfolio Value",
        margin=dict(l=50, r=20, t=20, b=20),
    )

    return fig


def create_score_radar_chart(technical: float, fundamental: float,
                             backtest: float) -> go.Figure:
    """スコアレーダーチャート"""
    categories = ["テクニカル", "ファンダメンタル", "バックテスト"]
    values = [technical, fundamental, backtest]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            fillcolor="rgba(0,100,255,0.2)",
            line=dict(color="blue"),
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=False,
        height=300,
        margin=dict(l=40, r=40, t=20, b=20),
    )
    return fig
