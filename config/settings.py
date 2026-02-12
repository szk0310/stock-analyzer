"""パラメータ設定（閾値、重み、期間）"""

# データ取得設定
DATA_PERIOD = "2y"  # 2年間の価格データ
CACHE_TTL_HOURS = 24  # Parquetキャッシュ有効期間
MEMORY_CACHE_TTL_SECONDS = 3600  # Streamlit in-memoryキャッシュ（1時間）

# テクニカル指標パラメータ
SMA_SHORT = 20
SMA_LONG = 50
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BB_PERIOD = 20
BB_STD = 2

# テクニカルスコア閾値
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

# ファンダメンタルスコア閾値
PER_CHEAP_MAX = 15
PER_VERY_CHEAP_MAX = 5
PER_MODERATE_MAX = 25
PBR_CHEAP_MAX = 1.0
PBR_MODERATE_MAX = 3.0
DIVIDEND_HIGH = 3.0  # %
DIVIDEND_MODERATE = 2.0  # %
ROE_HIGH = 15.0  # %
ROE_MODERATE = 8.0  # %

# 複合スコア重み
WEIGHT_TECHNICAL = 0.5
WEIGHT_FUNDAMENTAL = 0.3
WEIGHT_BACKTEST = 0.2

# スクリーニング設定
PRE_SCREEN_TOP_N = 50  # バックテスト前の絞り込み数
FINAL_TOP_N = 10  # 最終ランキング数

# バックテスト設定
BACKTEST_INITIAL_CAPITAL = 1_000_000  # 初期資金（100万円/ドル）
BACKTEST_COMMISSION = 0.001  # 手数料0.1%
RISK_FREE_RATE = 0.02  # リスクフリーレート（2%）

# バックテストスコア重み
BT_WEIGHT_RETURN = 0.4
BT_WEIGHT_SHARPE = 0.3
BT_WEIGHT_DRAWDOWN = 0.3

# データ取得のレートリミット
RATE_LIMIT_DELAY = 0.2  # 秒（Yahoo Finance対策）
BATCH_SIZE = 10  # バッチ取得サイズ

# キャッシュディレクトリ
import os
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_cache")
