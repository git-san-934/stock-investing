"""売買代金と株価チャートをもとに売り時シグナルを計算するモジュール。"""

from dataclasses import dataclass

import pandas as pd
import yfinance as yf

TURNOVER_MA_WINDOW = 20
TURNOVER_SPIKE_RATIO = 2.0  # 当日の売買代金が20日平均の何倍で「急増」とみなすか
HIGH_LOOKBACK = 60
NEAR_HIGH_THRESHOLD = 0.95  # 直近60日高値の95%以上を「高値圏」とみなす
MA_SHORT_WINDOW = 25
MA_LONG_WINDOW = 75


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
