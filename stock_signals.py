"""売買代金と株価チャートをもとに売り時シグナルを計算するモジュール。"""

import re
from dataclasses import dataclass

import pandas as pd
import yfinance as yf

TURNOVER_MA_WINDOW = 20
TURNOVER_SPIKE_RATIO = 2.0  # 当日の売買代金が20日平均の何倍で「急増」とみなすか
HIGH_LOOKBACK = 60
NEAR_HIGH_THRESHOLD = 0.95  # 直近60日高値の95%以上を「高値圏」とみなす
MA_SHORT_WINDOW = 25
MA_LONG_WINDOW = 75

# シグナルレベルの並び順(値が小さいほど強い)。ウォッチリストのソートに使う。
SIGNAL_LEVEL_ORDER = {"強": 0, "中": 1, "弱": 2, "なし": 3, "判定不可": 4}


def parse_watchlist_codes(raw_text: str, max_codes: int = 10) -> list[str]:
    """入力テキストを証券コードのリストに変換する(改行・カンマ区切り対応、重複除去)。"""
    if not raw_text or not raw_text.strip():
        return []

    codes: list[str] = []
    for token in re.split(r"[,\n]+", raw_text):
        code = token.strip().upper()
        if code and code not in codes:
            codes.append(code)

    if len(codes) > max_codes:
        raise ValueError(f"証券コードは最大{max_codes}件までです({len(codes)}件入力されました)")

    return codes


def to_ticker_symbol(code: str) -> str:
    """証券コード(例: "7203")をyfinance用シンボル(例: "7203.T")に変換する。"""
    code = code.strip().upper()
    return code if code.endswith(".T") else f"{code}.T"


def fetch_price_history(code: str, period: str = "1y") -> pd.DataFrame:
    symbol = to_ticker_symbol(code)
    df = yf.Ticker(symbol).history(period=period)
    if df.empty:
        raise ValueError(f"銘柄コード {code} のデータを取得できませんでした")
    return df


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["turnover"] = df["Close"] * df["Volume"]
    df["turnover_ma"] = df["turnover"].rolling(TURNOVER_MA_WINDOW).mean()
    df["turnover_ratio"] = df["turnover"] / df["turnover_ma"]
    df["ma_short"] = df["Close"].rolling(MA_SHORT_WINDOW).mean()
    df["ma_long"] = df["Close"].rolling(MA_LONG_WINDOW).mean()
    df["rolling_high"] = df["Close"].rolling(HIGH_LOOKBACK).max()
    df["near_high"] = df["Close"] >= df["rolling_high"] * NEAR_HIGH_THRESHOLD
    return df


@dataclass
class SellSignal:
    level: str  # "強" | "中" | "弱" | "なし" | "判定不可"
    reasons: list[str]


# 閾値条件はcompute_signal_levelsと同じものを使っている。判定条件を変えるときは両方直すこと。
def evaluate_sell_signal(df: pd.DataFrame) -> SellSignal:
    if len(df) < MA_LONG_WINDOW + 2:
        return SellSignal(level="判定不可", reasons=["データ期間が不足しています"])

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    reasons: list[str] = []
    score = 0

    turnover_spike = bool(latest["turnover_ratio"] >= TURNOVER_SPIKE_RATIO)
    if turnover_spike and bool(latest["near_high"]):
        score += 2
        reasons.append(
            f"売買代金が{TURNOVER_MA_WINDOW}日平均の{TURNOVER_SPIKE_RATIO}倍以上に急増しており、"
            f"かつ高値圏(直近{HIGH_LOOKBACK}日高値の{int(NEAR_HIGH_THRESHOLD * 100)}%以上)にあります"
        )
    elif turnover_spike:
        score += 1
        reasons.append(f"売買代金が{TURNOVER_MA_WINDOW}日平均の{TURNOVER_SPIKE_RATIO}倍以上に急増しています")

    dead_cross = bool(prev["ma_short"] >= prev["ma_long"] and latest["ma_short"] < latest["ma_long"])
    if dead_cross:
        score += 1
        reasons.append(f"{MA_SHORT_WINDOW}日移動平均が{MA_LONG_WINDOW}日移動平均を下回りました(デッドクロス)")

    if score >= 3:
        level = "強"
    elif score == 2:
        level = "中"
    elif score == 1:
        level = "弱"
    else:
        level = "なし"
        reasons.append("現時点で売り検討シグナルはありません")

    return SellSignal(level=level, reasons=reasons)


# 閾値条件はevaluate_sell_signalと同じものを使っている。判定条件を変えるときは両方直すこと。
def compute_signal_levels(df: pd.DataFrame) -> pd.Series:
    """バックテスト用に、全営業日ごとの売り検討シグナルレベルを算出する。"""
    turnover_spike = df["turnover_ratio"] >= TURNOVER_SPIKE_RATIO
    near_high = df["near_high"].fillna(False)
    dead_cross = (df["ma_short"].shift(1) >= df["ma_long"].shift(1)) & (df["ma_short"] < df["ma_long"])

    score = (turnover_spike & near_high).astype(int) * 2
    score += (turnover_spike & ~near_high).astype(int)
    score += dead_cross.fillna(False).astype(int)

    levels = pd.Series("なし", index=df.index)
    levels[score == 1] = "弱"
    levels[score == 2] = "中"
    levels[score >= 3] = "強"
    return levels


@dataclass
class Trade:
    entry_date: pd.Timestamp
    entry_price: float
    exit_date: pd.Timestamp
    exit_price: float
    return_pct: float
    is_open: bool  # True: 期間終了時点でまだ保有中(含み損益)


def simulate_sell_strategy(df: pd.DataFrame, sell_levels: tuple[str, ...] = ("強", "中")) -> list[Trade]:
    """シグナルに従って売買していた場合の簡易シミュレーションを行う(参考値、投資助言ではない)。

    ルール: 期間最初の営業日の終値で買う → シグナルがsell_levelsに該当した日の終値で売る
    → シグナルが「なし」に戻った次の営業日の終値で買い直す → 期間終了時点で保有中なら含み損益として計上する。
    手数料・税金は考慮しない。
    """
    levels = compute_signal_levels(df)

    trades: list[Trade] = []
    holding = True
    waiting_to_reenter = False
    entry_date = df.index[0]
    entry_price = float(df["Close"].iloc[0])

    for date, level in levels.items():
        if date == entry_date:
            continue

        price = float(df.loc[date, "Close"])

        if holding and level in sell_levels:
            return_pct = (price - entry_price) / entry_price * 100
            trades.append(Trade(entry_date, entry_price, date, price, return_pct, is_open=False))
            holding = False
            waiting_to_reenter = True
        elif waiting_to_reenter and level == "なし":
            entry_date = date
            entry_price = price
            holding = True
            waiting_to_reenter = False

    if holding:
        last_date = df.index[-1]
        last_price = float(df["Close"].iloc[-1])
        return_pct = (last_price - entry_price) / entry_price * 100
        trades.append(Trade(entry_date, entry_price, last_date, last_price, return_pct, is_open=True))

    return trades


def buy_and_hold_return(df: pd.DataFrame) -> float:
    """期間最初の終値で買ってからずっと保有し続けた場合の損益率(%)を返す。"""
    first_price = float(df["Close"].iloc[0])
    last_price = float(df["Close"].iloc[-1])
    return (last_price - first_price) / first_price * 100
