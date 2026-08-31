"""株の売り時・買い時判断ダッシュボード(東証銘柄向け)。"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from stock_signals import (
    BUY_ZONE_ORDER,
    MA_LONG_WINDOW,
    MA_SHORT_WINDOW,
    MARKET_SEGMENTS,
    TURNOVER_MA_WINDOW,
    buy_and_hold_return,
    compute_buy_zone_levels,
    compute_indicators,
    evaluate_buy_zone,
    fetch_company_name,
    fetch_price_history,
    parse_watchlist_codes,
    select_top_promising_by_market,
    simulate_buy_zone_strategy,
)

ZONE_COLOR = {"買い時": "rgba(220, 53, 69, 0.18)", "様子見": "rgba(255, 193, 7, 0.18)"}


def zone_segments(levels: pd.Series) -> list[tuple]:
    """状態が連続する区間ごとに (開始日, 終了日, 状態) のタプルを返す(未算出の区間は除く)。"""
    valid = levels.dropna()
    if valid.empty:
        return []
    group_id = valid.ne(valid.shift()).cumsum()
    return [(group.index[0], group.index[-1], group.iloc[0]) for _, group in valid.groupby(group_id)]


def render_price_chart(df: pd.DataFrame, key: str) -> None:
    """株価チャート(ローソク足 + 移動平均線 + 買い時/様子見の背景帯)を描画する。

    ウォッチリスト・有望銘柄(AI選定)の両タブから共通で使う。
    """
    price_fig = go.Figure()
    price_fig.add_trace(
        go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
            name="株価",
        )
    )
    price_fig.add_trace(
        go.Scatter(x=df.index, y=df["ma_short"], name=f"{MA_SHORT_WINDOW}日移動平均", line=dict(width=1))
    )
    price_fig.add_trace(
        go.Scatter(x=df.index, y=df["ma_long"], name=f"{MA_LONG_WINDOW}日移動平均", line=dict(width=1))
    )

    buy_zone_levels = compute_buy_zone_levels(df)
    for start, end, state in zone_segments(buy_zone_levels):
        price_fig.add_vrect(
            x0=start,
            x1=end + pd.Timedelta(days=1),
            fillcolor=ZONE_COLOR[state],
            line_width=0,
            layer="below",
        )
    for state, color in ZONE_COLOR.items():
        price_fig.add_trace(
            go.Scatter(
                x=[None], y=[None], mode="markers",
                marker=dict(size=10, color=color, symbol="square"),
                name=state,
            )
        )

    price_fig.update_layout(title="株価チャート", xaxis_rangeslider_visible=False, height=450)
    st.plotly_chart(price_fig, width="stretch", key=key)
    st.caption(
        f"背景色は終値と{MA_SHORT_WINDOW}日移動平均線の位置関係を表します"
        "(買い時=赤、様子見=黄色)。"
    )


st.set_page_config(page_title="売り時・買い時判断ダッシュボード", layout="wide")

st.title("株の売り時・買い時判断ダッシュボード")
st.caption(f"株価が{MA_SHORT_WINDOW}日移動平均線より上か下かをもとに、買い時/様子見の目安を表示します。投資助言ではありません。")

LEVEL_ICON = {"買い時": "🔴", "様子見": "🟡", "判定不可": "⚪"}
LEVEL_LABEL = {"買い時": "買い時", "様子見": "様子見", "判定不可": "判定不可"}


@st.cache_data(ttl=600)
def load_price_history(code: str, period: str) -> pd.DataFrame:
    return fetch_price_history(code, period=period)


@st.cache_data(ttl=3600)
def load_company_name(code: str) -> str:
    return fetch_company_name(code)


@st.cache_data(ttl=86400)
def load_top_promising_by_market(n_per_market: int, period: str):
    return select_top_promising_by_market(n_per_market=n_per_market, period=period)


with st.sidebar:
    raw_codes = st.text_area(
        "証券コード(最大50件、改行またはカンマ区切り)",
        value="285A,7974,6981,6961,6134,4092,4078,6965,6777,6857,6920,4062,5803,6376,485A,278A,6702,6701,1329",
        help="例: トヨタ自動車なら 7203。複数銘柄はカンマまたは改行で区切ってください。",
    )
    period = st.selectbox("表示期間", ["6mo", "1y", "2y", "3y", "10y"], index=1)
    st.button("表示する")

    st.markdown("---")
    st.markdown("**買い時/様子見の条件**")
    st.markdown(f"- 終値が{MA_SHORT_WINDOW}日移動平均線より上: 買い時(チャート背景:赤)")
    st.markdown(f"- 終値が{MA_SHORT_WINDOW}日移動平均線より下: 様子見(チャート背景:黄色)")


def render_watchlist_tab(raw_codes: str, period: str) -> None:
    """「ウォッチリスト」タブの内容を描画する。

    st.stop()はスクリプト全体を止めてしまい他のタブが描画されなくなるため使わず、
    早期returnで打ち切る(このタブの描画のみをスキップする)。
    """
    try:
        codes = parse_watchlist_codes(raw_codes)
    except ValueError as e:
        st.error(str(e))
        return

    if not codes:
        st.info("証券コードを入力してください。")
        return

    summaries = []
    details = {}
    names = {}
    for code in codes:
        try:
            df = load_price_history(code, period)
            df = compute_indicators(df)
            signal = evaluate_buy_zone(df)
        except Exception as e:
            st.warning(f"{code}: {e}")
            continue

        name = load_company_name(code)
        details[code] = (df, signal)
        names[code] = name

        latest_close = float(df["Close"].iloc[-1])
        if len(df) >= 2:
            prev_close = float(df["Close"].iloc[-2])
            change_pct_text = f"{(latest_close - prev_close) / prev_close * 100:+.1f}%"
        else:
            change_pct_text = "-"

        summaries.append(
            {
                "証券コード": code,
                "銘柄名": name,
                "最新終値日": df.index[-1].strftime("%Y-%m-%d"),
                "最新終値": round(latest_close, 1),
                "前日比": change_pct_text,
                "シグナル": f"{LEVEL_ICON.get(signal.level, '')} {LEVEL_LABEL.get(signal.level, signal.level)}",
                "主な理由": signal.reasons[0] if signal.reasons else "",
                "_order": BUY_ZONE_ORDER.get(signal.level, 99),
            }
        )

    if not summaries:
        return

    summary_df = pd.DataFrame(summaries).sort_values("_order").drop(columns="_order")
    st.subheader("ウォッチリスト")
    st.dataframe(summary_df, width="stretch", hide_index=True)

    st.subheader("銘柄ごとの詳細")
    for i, code in enumerate(summary_df["証券コード"].tolist()):
        df, signal = details[code]
        header = f"{LEVEL_ICON.get(signal.level, '')} {code} {names[code]}  シグナル: {LEVEL_LABEL.get(signal.level, signal.level)}"
        with st.expander(header, expanded=(i == 0)):
            for reason in signal.reasons:
                st.write(f"- {reason}")

            render_price_chart(df, key=f"price_{code}")

            turnover_fig = go.Figure()
            turnover_fig.add_trace(go.Bar(x=df.index, y=df["turnover"], name="売買代金"))
            turnover_fig.add_trace(
                go.Scatter(x=df.index, y=df["turnover_ma"], name=f"{TURNOVER_MA_WINDOW}日平均売買代金", line=dict(width=1))
            )
            turnover_fig.update_layout(title="売買代金", height=300)
            st.plotly_chart(turnover_fig, width="stretch", key=f"turnover_{code}")

            display_columns = ["Close", "Volume", "turnover", "turnover_ratio", "ma_short", "ma_long"]
            st.dataframe(
                df.tail(20)[display_columns].sort_index(ascending=False),
                width="stretch",
                key=f"table_{code}",
            )

            st.markdown("**過去データでのシミュレーション**")
            st.caption(
                "「買い時」になった日に買い、「様子見」になった日に売るルールで計算した"
                "参考値です。手数料・税金は考慮しておらず、将来の成果を保証するものではありません。"
            )

            trades = simulate_buy_zone_strategy(df)
            hold_return = buy_and_hold_return(df)

            sim_multiplier = 1.0
            for trade in trades:
                sim_multiplier *= 1 + trade.return_pct / 100
            sim_return = (sim_multiplier - 1) * 100

            col1, col2 = st.columns(2)
            col1.metric("シグナル通り売買した場合", f"{sim_return:+.1f}%")
            col2.metric("ずっと保有し続けた場合(買い持ち)", f"{hold_return:+.1f}%")

            trades_rows = [
                {
                    "購入日": trade.entry_date.strftime("%Y-%m-%d"),
                    "購入価格": round(trade.entry_price, 1),
                    "売却日": "保有中" if trade.is_open else trade.exit_date.strftime("%Y-%m-%d"),
                    "売却価格": round(trade.exit_price, 1),
                    "損益率": f"{trade.return_pct:+.1f}%",
                    "状態": "含み損益" if trade.is_open else "確定",
                }
                for trade in trades
            ]
            st.dataframe(pd.DataFrame(trades_rows), width="stretch", hide_index=True, key=f"trades_{code}")


def render_promising_tab(period: str) -> None:
    """「有望銘柄(AI選定)」タブの内容を描画する。"""
    st.subheader("有望銘柄(AI選定)")
    st.caption(
        "対象ユニバース内の銘柄を独自のルールベースでスコアリングし、"
        "プライム/スタンダード/グロースの市場区分ごとに上位10銘柄を表示します。"
        "外部AI/LLMは使用していません。投資助言ではなく、あくまで参考情報です。"
    )
    st.caption(
        "対象ユニバースは東証全銘柄(約3,900件)を網羅したものではなく、主要銘柄を中心とした静的リストです。"
        "特にスタンダード・グロース市場の候補は、公式データを直接参照できない制約のもとで作成した一覧のため、"
        "件数が少なく、市場区分に誤りが含まれる可能性があります。"
    )

    if st.button("有望銘柄を探索する"):
        progress = st.progress(0, text="対象銘柄のデータを取得・スコアリング中です…")
        results: dict = {}
        try:
            results = load_top_promising_by_market(10, period)
        except Exception as e:
            st.error(f"有望銘柄の算出中にエラーが発生しました: {e}")
        finally:
            progress.progress(100, text="完了しました")
            progress.empty()

        if not results:
            st.warning("有望銘柄を算出できませんでした。データ取得状況をご確認ください。")
        else:
            for market in MARKET_SEGMENTS:
                top_stocks = results.get(market, [])
                st.markdown(f"### {market}市場")
                if not top_stocks:
                    st.info(f"{market}市場の候補からは有望銘柄を算出できませんでした。")
                    continue

                ranking_df = pd.DataFrame(
                    [
                        {"順位": i + 1, "証券コード": s.code, "銘柄名": s.name, "スコア": round(s.score, 2)}
                        for i, s in enumerate(top_stocks)
                    ]
                )
                st.dataframe(ranking_df, width="stretch", hide_index=True)

                for i, s in enumerate(top_stocks):
                    with st.expander(f"{i + 1}位 {s.code} {s.name}(スコア: {s.score:.2f})"):
                        for reason in s.reasons:
                            st.write(f"- {reason}")

                        render_price_chart(s.price_history, key=f"promising_price_{market}_{s.code}")
    else:
        st.info("ボタンを押すと、対象ユニバース内のデータを取得してスコアリングを実行します(数十秒〜数分かかる場合があります)。")


tab_watchlist, tab_promising = st.tabs(["ウォッチリスト", "有望銘柄(AI選定)"])

with tab_watchlist:
    render_watchlist_tab(raw_codes, period)

with tab_promising:
    render_promising_tab(period)
