"""売買代金と株価チャートをもとに売り時シグナルを計算するモジュール。"""

import re
from dataclasses import dataclass

import pandas as pd
import yfinance as yf

TURNOVER_MA_WINDOW = 20
MA_SHORT_WINDOW = 25
MA_LONG_WINDOW = 75

# シグナルレベルの並び順(値が小さいほど強い)。ウォッチリストのソートに使う。
SIGNAL_LEVEL_ORDER = {"強": 0, "なし": 1, "判定不可": 2}


def parse_watchlist_codes(raw_text: str, max_codes: int = 50) -> list[str]:
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


# 主要な東証銘柄の日本語社名。yfinanceの企業名は基本的に英語表記のため、
# 代表的な銘柄のみ静的に保持し、優先的に使う。
TSE_COMPANY_NAMES: dict[str, str] = {
    "7203": "トヨタ自動車",
    "285A": "キオクシアホールディングス",
    "9984": "ソフトバンクグループ",
    "9434": "ソフトバンク",
    "6758": "ソニーグループ",
    "6861": "キーエンス",
    "8306": "三菱UFJフィナンシャル・グループ",
    "9432": "日本電信電話",
    "9433": "KDDI",
    "4063": "信越化学工業",
    "6098": "リクルートホールディングス",
    "6501": "日立製作所",
    "6502": "東芝",
    "6503": "三菱電機",
    "6752": "パナソニックホールディングス",
    "6902": "デンソー",
    "6954": "ファナック",
    "7011": "三菱重工業",
    "7201": "日産自動車",
    "7267": "本田技研工業",
    "7269": "スズキ",
    "7270": "SUBARU",
    "7741": "HOYA",
    "7751": "キヤノン",
    "7974": "任天堂",
    "8001": "伊藤忠商事",
    "8002": "丸紅",
    "8031": "三井物産",
    "8035": "東京エレクトロン",
    "8053": "住友商事",
    "8058": "三菱商事",
    "8113": "ユニ・チャーム",
    "8267": "イオン",
    "8316": "三井住友フィナンシャルグループ",
    "8411": "みずほフィナンシャルグループ",
    "8591": "オリックス",
    "8766": "東京海上ホールディングス",
    "8801": "三井不動産",
    "8802": "三菱地所",
    "9020": "東日本旅客鉄道",
    "9022": "東海旅客鉄道",
    "9101": "日本郵船",
    "9104": "商船三井",
    "9202": "ANAホールディングス",
    "9501": "東京電力ホールディングス",
    "9503": "関西電力",
    "9613": "エヌ・ティ・ティ・データグループ",
    "9843": "ニトリホールディングス",
    "9983": "ファーストリテイリング",
    "4502": "武田薬品工業",
    "4503": "アステラス製薬",
    "4519": "中外製薬",
    "4568": "第一三共",
    "4661": "オリエンタルランド",
    "4689": "LINEヤフー",
    "4901": "富士フイルムホールディングス",
    "4911": "資生堂",
    "5108": "ブリヂストン",
    "5401": "日本製鉄",
    "6178": "日本郵政",
    "6301": "コマツ",
    "6326": "クボタ",
    "6367": "ダイキン工業",
    "6702": "富士通",
    "6723": "ルネサスエレクトロニクス",
    "6971": "京セラ",
    "6981": "村田製作所",
    "6701": "日本電気",
    "6857": "アドバンテスト",
    "6920": "レーザーテック",
}


def fetch_company_name(code: str) -> str:
    """証券コードから銘柄名を取得する。

    既知の主要銘柄はTSE_COMPANY_NAMESの日本語社名を返す。それ以外は
    yfinanceの英語社名、取得できない場合は証券コードをそのまま返す。
    """
    normalized = code.strip().upper().removesuffix(".T")
    if normalized in TSE_COMPANY_NAMES:
        return TSE_COMPANY_NAMES[normalized]

    symbol = to_ticker_symbol(code)
    try:
        info = yf.Ticker(symbol).info
        name = info.get("longName") or info.get("shortName")
    except Exception:
        name = None
    return name or code


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["turnover"] = df["Close"] * df["Volume"]
    df["turnover_ma"] = df["turnover"].rolling(TURNOVER_MA_WINDOW).mean()
    df["turnover_ratio"] = df["turnover"] / df["turnover_ma"]
    df["ma_short"] = df["Close"].rolling(MA_SHORT_WINDOW).mean()
    df["ma_long"] = df["Close"].rolling(MA_LONG_WINDOW).mean()
    return df


@dataclass
class SellSignal:
    level: str  # "強" | "なし" | "判定不可"
    reasons: list[str]


# 判定条件はcompute_signal_levelsと同じものを使っている。判定条件を変えるときは両方直すこと。
def evaluate_sell_signal(df: pd.DataFrame) -> SellSignal:
    if len(df) < MA_SHORT_WINDOW + 1:
        return SellSignal(level="判定不可", reasons=["データ期間が不足しています"])

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    crossed_below = bool(prev["Close"] >= prev["ma_short"] and latest["Close"] < latest["ma_short"])
    if crossed_below:
        return SellSignal(
            level="強",
            reasons=[f"前日は{MA_SHORT_WINDOW}日移動平均線の上にあった株価が、本日下回りました"],
        )

    return SellSignal(level="なし", reasons=["現時点で売り検討シグナルはありません"])


# 判定条件はevaluate_sell_signalと同じものを使っている。判定条件を変えるときは両方直すこと。
def compute_signal_levels(df: pd.DataFrame) -> pd.Series:
    """バックテスト用に、全営業日ごとの売り検討シグナルレベルを算出する。"""
    prev_close = df["Close"].shift(1)
    prev_ma_short = df["ma_short"].shift(1)
    crossed_below = (prev_close >= prev_ma_short) & (df["Close"] < df["ma_short"])

    levels = pd.Series("なし", index=df.index)
    levels[crossed_below.fillna(False)] = "強"
    return levels


@dataclass
class Trade:
    entry_date: pd.Timestamp
    entry_price: float
    exit_date: pd.Timestamp
    exit_price: float
    return_pct: float
    is_open: bool  # True: 期間終了時点でまだ保有中(含み損益)


def simulate_sell_strategy(df: pd.DataFrame, sell_levels: tuple[str, ...] = ("強",)) -> list[Trade]:
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
