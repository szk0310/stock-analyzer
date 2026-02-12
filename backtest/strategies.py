"""売買戦略（MA Cross, RSI, ハイブリッド）"""
import pandas as pd
import numpy as np
from config.settings import SMA_SHORT, SMA_LONG, RSI_OVERSOLD, RSI_OVERBOUGHT


class BaseStrategy:
    """戦略の基底クラス"""
    name = "base"

    def generate_signal(self, df: pd.DataFrame, i: int) -> int:
        """
        シグナル生成: 1=買い, -1=売り, 0=ホールド
        """
        raise NotImplementedError


class MACrossStrategy(BaseStrategy):
    """移動平均クロス戦略"""
    name = "MA Cross"

    def generate_signal(self, df: pd.DataFrame, i: int) -> int:
        if i < 1:
            return 0
        sma_s = df["SMA_short"].iloc[i]
        sma_l = df["SMA_long"].iloc[i]
        sma_s_prev = df["SMA_short"].iloc[i - 1]
        sma_l_prev = df["SMA_long"].iloc[i - 1]

        if any(pd.isna([sma_s, sma_l, sma_s_prev, sma_l_prev])):
            return 0

        # ゴールデンクロス → 買い
        if sma_s_prev <= sma_l_prev and sma_s > sma_l:
            return 1
        # デッドクロス → 売り
        if sma_s_prev >= sma_l_prev and sma_s < sma_l:
            return -1
        return 0


class RSIStrategy(BaseStrategy):
    """RSI逆張り戦略"""
    name = "RSI"

    def generate_signal(self, df: pd.DataFrame, i: int) -> int:
        rsi = df["RSI"].iloc[i]
        if pd.isna(rsi):
            return 0
        if rsi < RSI_OVERSOLD:
            return 1  # 売られすぎ → 買い
        if rsi > RSI_OVERBOUGHT:
            return -1  # 買われすぎ → 売り
        return 0


class HybridStrategy(BaseStrategy):
    """
    ハイブリッド戦略（MA Cross + RSI + MACD + BB）

    買いシグナル: 以下の条件のうち2つ以上が成立
    - SMAゴールデンクロス or 価格>SMA_long
    - RSI < 40 (やや売られすぎ)
    - MACDが強気クロス or MACDヒストグラム>0
    - ボリンジャーバンド下限付近

    売りシグナル: 以下の条件のうち2つ以上が成立
    - SMAデッドクロス or 価格<SMA_long
    - RSI > 60
    - MACDが弱気クロス or MACDヒストグラム<0
    """
    name = "Hybrid"

    def generate_signal(self, df: pd.DataFrame, i: int) -> int:
        if i < 1:
            return 0

        row = df.iloc[i]
        prev = df.iloc[i - 1]

        buy_signals = 0
        sell_signals = 0

        # SMA条件
        sma_s = row.get("SMA_short")
        sma_l = row.get("SMA_long")
        sma_s_p = prev.get("SMA_short")
        sma_l_p = prev.get("SMA_long")
        close = row["Close"]

        if all(pd.notna([sma_s, sma_l, sma_s_p, sma_l_p])):
            if sma_s_p <= sma_l_p and sma_s > sma_l:
                buy_signals += 1
            elif close > sma_l:
                buy_signals += 0.5

            if sma_s_p >= sma_l_p and sma_s < sma_l:
                sell_signals += 1
            elif close < sma_l:
                sell_signals += 0.5

        # RSI条件
        rsi = row.get("RSI")
        if pd.notna(rsi):
            if rsi < 40:
                buy_signals += 1
            if rsi > 60:
                sell_signals += 1

        # MACD条件
        macd = row.get("MACD")
        macd_sig = row.get("MACD_signal")
        macd_p = prev.get("MACD")
        macd_sig_p = prev.get("MACD_signal")
        macd_hist = row.get("MACD_hist")

        if all(pd.notna([macd, macd_sig, macd_p, macd_sig_p])):
            if macd_p <= macd_sig_p and macd > macd_sig:
                buy_signals += 1
            elif pd.notna(macd_hist) and macd_hist > 0:
                buy_signals += 0.5

            if macd_p >= macd_sig_p and macd < macd_sig:
                sell_signals += 1
            elif pd.notna(macd_hist) and macd_hist < 0:
                sell_signals += 0.5

        # BB条件
        bb_lower = row.get("BB_lower")
        bb_upper = row.get("BB_upper")
        if pd.notna(bb_lower) and pd.notna(bb_upper) and bb_upper != bb_lower:
            bb_pos = (close - bb_lower) / (bb_upper - bb_lower)
            if bb_pos < 0.2:
                buy_signals += 1
            elif bb_pos > 0.8:
                sell_signals += 1

        # 判定
        if buy_signals >= 2 and buy_signals > sell_signals:
            return 1
        if sell_signals >= 2 and sell_signals > buy_signals:
            return -1
        return 0


def get_strategy(name: str = "hybrid") -> BaseStrategy:
    """戦略名から戦略インスタンスを取得"""
    strategies = {
        "ma_cross": MACrossStrategy,
        "rsi": RSIStrategy,
        "hybrid": HybridStrategy,
    }
    cls = strategies.get(name.lower(), HybridStrategy)
    return cls()
