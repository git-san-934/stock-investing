"""売買代金と株価チャートをもとに買い時/様子見シグナルを計算するモジュール。"""

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yfinance as yf

TURNOVER_MA_WINDOW = 20
MA_SHORT_WINDOW = 25
MA_LONG_WINDOW = 75


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
    # "3y"はyfinance/Yahoo Finance側が正式サポートするperiod値(6mo/1y/2y/5y/10y等)に
    # 含まれないため、開始日・終了日を明示的に指定して取得する。
    if period == "3y":
        end = pd.Timestamp.today()
        start = end - pd.DateOffset(years=3)
        df = yf.Ticker(symbol).history(start=start, end=end)
    else:
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
    "6961": "エンプラス",
    "6134": "FUJI",
    "4092": "日本化学工業",
    "4078": "堺化学工業",
    "6965": "浜松ホトニクス",
    "6777": "サンテックホールディングス",
    "4062": "イビデン",
    "5803": "フジクラ",
    "6376": "日機装",
    "485A": "パワーエックス",
    "278A": "テラドローン",
    "1329": "日経平均",
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


BUY_ZONE_ORDER = {"買い時": 0, "様子見": 1, "判定不可": 2}


@dataclass
class BuyZoneStatus:
    level: str  # "買い時" | "様子見" | "判定不可"
    reasons: list[str]


def evaluate_buy_zone(df: pd.DataFrame) -> BuyZoneStatus:
    """最新日について、終値と25日移動平均線の位置関係から「買い時」「様子見」を判定する。

    判定条件はcompute_buy_zone_levelsと同じものを使っている。判定条件を変えるときは両方直すこと。
    """
    if len(df) < MA_SHORT_WINDOW + 1 or pd.isna(df["ma_short"].iloc[-1]):
        return BuyZoneStatus(level="判定不可", reasons=["データ期間が不足しています"])

    latest = df.iloc[-1]
    if latest["Close"] > latest["ma_short"]:
        return BuyZoneStatus(
            level="買い時",
            reasons=[f"終値が{MA_SHORT_WINDOW}日移動平均線より上にあります"],
        )

    return BuyZoneStatus(
        level="様子見",
        reasons=[f"終値が{MA_SHORT_WINDOW}日移動平均線より下にあります"],
    )


@dataclass
class Trade:
    entry_date: pd.Timestamp
    entry_price: float
    exit_date: pd.Timestamp
    exit_price: float
    return_pct: float
    is_open: bool  # True: 期間終了時点でまだ保有中(含み損益)


def simulate_buy_zone_strategy(df: pd.DataFrame) -> list[Trade]:
    """買い時/様子見の状態に従って売買していた場合の簡易シミュレーションを行う(参考値、投資助言ではない)。

    ルール: 「買い時」になった日の終値で買う → 「様子見」になった日の終値で売る、を繰り返す。
    期間終了時点で保有中なら含み損益として計上する。手数料・税金は考慮しない。
    """
    levels = compute_buy_zone_levels(df)

    trades: list[Trade] = []
    holding = False
    entry_date: pd.Timestamp | None = None
    entry_price = 0.0

    for date, level in levels.items():
        if pd.isna(level):
            continue

        price = float(df.loc[date, "Close"])

        if level == "買い時" and not holding:
            holding = True
            entry_date = date
            entry_price = price
        elif level == "様子見" and holding:
            return_pct = (price - entry_price) / entry_price * 100
            trades.append(Trade(entry_date, entry_price, date, price, return_pct, is_open=False))
            holding = False

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


def compute_buy_zone_levels(df: pd.DataFrame) -> pd.Series:
    """終値と25日移動平均線の位置関係から、日ごとの「買い時」「様子見」状態を算出する。

    判定条件はevaluate_buy_zoneと同じものを使っている。判定条件を変えるときは両方直すこと。
    """
    levels = pd.Series(pd.NA, index=df.index, dtype="object")
    valid = df["ma_short"].notna()
    levels[valid & (df["Close"] > df["ma_short"])] = "買い時"
    levels[valid & (df["Close"] <= df["ma_short"])] = "様子見"
    return levels


UNIVERSE_CSV_PATH = Path(__file__).parent / "data" / "tse_universe.csv"


def load_universe() -> pd.DataFrame:
    """AI銘柄選定の対象ユニバース(data/tse_universe.csv)を読み込む。

    東証全銘柄(約3,900件)を網羅したものではなく、主要銘柄を中心とした静的リストである。
    Excelで編集・保存するとShift-JIS(cp932)で保存されることが多いため、
    UTF-8での読み込みに失敗した場合はcp932でフォールバックする。
    """
    try:
        return pd.read_csv(UNIVERSE_CSV_PATH, dtype={"code": str})
    except UnicodeDecodeError:
        return pd.read_csv(UNIVERSE_CSV_PATH, dtype={"code": str}, encoding="cp932")


def fetch_price_history_batch(codes: list[str], period: str = "6mo") -> dict[str, pd.DataFrame]:
    """複数銘柄の株価データをまとめて取得する(1銘柄ずつ取得するより通信回数を抑える)。

    取得できなかった(データが空の)銘柄は結果に含めない。
    """
    symbols = [to_ticker_symbol(code) for code in codes]
    if period == "3y":
        end = pd.Timestamp.today()
        start = end - pd.DateOffset(years=3)
        raw = yf.download(symbols, start=start, end=end, group_by="ticker", progress=False, threads=True)
    else:
        raw = yf.download(symbols, period=period, group_by="ticker", progress=False, threads=True)

    result: dict[str, pd.DataFrame] = {}
    for code, symbol in zip(codes, symbols):
        try:
            df = raw[symbol] if len(symbols) > 1 else raw
        except KeyError:
            continue
        df = df.dropna(how="all")
        if df.empty:
            continue
        result[code] = df
    return result


@dataclass
class PromisingStock:
    code: str
    name: str
    score: float
    reasons: list[str]


def score_stock(df: pd.DataFrame) -> float | None:
    """テクニカル指標を組み合わせて「今買うと有望か」を表すスコアを算出する(参考値、投資助言ではない)。

    スコアが高いほど有望と判定する。データ不足で指標が算出できない場合はNoneを返す。
    構成: 25日移動平均線からの上方乖離率 + ゴールデンクロス状態 + 売買代金の増加度合い + 直近5営業日騰落率。
    """
    if len(df) < MA_LONG_WINDOW + 5:
        return None

    latest = df.iloc[-1]
    if pd.isna(latest["ma_short"]) or pd.isna(latest["ma_long"]):
        return None

    ma_short_deviation = (latest["Close"] - latest["ma_short"]) / latest["ma_short"] * 100
    golden_cross = 1.0 if latest["ma_short"] > latest["ma_long"] else 0.0
    turnover_ratio = float(latest["turnover_ratio"]) if pd.notna(latest["turnover_ratio"]) else 1.0
    recent_return = (latest["Close"] - df["Close"].iloc[-6]) / df["Close"].iloc[-6] * 100

    return float(
        ma_short_deviation * 1.0
        + golden_cross * 5.0
        + (turnover_ratio - 1.0) * 3.0
        + recent_return * 0.5
    )


MARKET_SEGMENTS = ["プライム", "スタンダード", "グロース"]


def select_top_promising_by_market(n_per_market: int = 10, period: str = "6mo") -> dict[str, list[PromisingStock]]:
    """市場区分(プライム/スタンダード/グロース)ごとに、対象ユニバースからスコア上位n_per_market銘柄を算出する。

    参考情報であり投資助言ではない。市場区分の少ない銘柄(スタンダード/グロース)は
    候補数自体が少ないため、n_per_market件に満たない場合がある。
    """
    universe = load_universe()
    codes = universe["code"].tolist()
    names = dict(zip(universe["code"], universe["name"]))
    markets = dict(zip(universe["code"], universe["market"]))

    histories = fetch_price_history_batch(codes, period=period)

    scored_by_market: dict[str, list[PromisingStock]] = {}
    for code, raw_df in histories.items():
        df = compute_indicators(raw_df)
        score = score_stock(df)
        if score is None:
            continue

        latest = df.iloc[-1]
        turnover_text = (
            f"{latest['turnover_ratio']:.2f}倍" if pd.notna(latest["turnover_ratio"]) else "算出不可"
        )
        recent_return = (latest["Close"] - df["Close"].iloc[-6]) / df["Close"].iloc[-6] * 100
        reasons = [
            f"25日移動平均線からの乖離率: {(latest['Close'] - latest['ma_short']) / latest['ma_short'] * 100:+.1f}%",
            f"ゴールデンクロス状態(25日線>75日線): {'はい' if latest['ma_short'] > latest['ma_long'] else 'いいえ'}",
            f"直近の売買代金(20日平均比): {turnover_text}",
            f"直近5営業日騰落率: {recent_return:+.1f}%",
        ]
        stock = PromisingStock(code=code, name=names.get(code, code), score=score, reasons=reasons)
        market = markets.get(code, "不明")
        scored_by_market.setdefault(market, []).append(stock)

    for stocks in scored_by_market.values():
        stocks.sort(key=lambda s: s.score, reverse=True)

    return {market: stocks[:n_per_market] for market, stocks in scored_by_market.items()}
