"""株の売り時判断ダッシュボード(東証銘柄向け)。"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from stock_signals import (
    MA_LONG_WINDOW,
    MA_SHORT_WINDOW,
    SIGNAL_LEVEL_ORDER,
    TURNOVER_MA_WINDOW,
    compute_indicators,
    evaluate_sell_signal,
    fetch_price_history,
    parse_watchlist_codes,
)

st.set_page_config(page_title="売り時判断ダッシュボード", layout="wide")

st.title("株の売り時判断ダッシュボード")
st.caption("売買代金の急増と株価チャートの動きから売り時の目安を表示します。投資助言ではありません。")

LEVEL_ICON = {"強": "🔴", "中": "🟠", "弱": "🟡", "なし": "🟢", "判定不可": "⚪"}


@st.cache_data(ttl=600)
def load_price_history(code: str, period: str) -> pd.DataFrame:
    return fetch_price_history(code, period=period)


with st.sidebar:
    raw_codes = st.text_area(
        "証券コード(最大10件、改行またはカンマ区切り)",
        value="7203\n9984\n6758",
        help="例: トヨタ自動車なら 7203。複数銘柄はカンマまたは改行で区切ってください。",
    )
    period = st.selectbox("表示期間", ["6mo", "1y", "2y"], index=1)
    st.button("表示する")

try:
    codes = parse_watchlist_codes(raw_codes)
except ValueError as e:
    st.error(str(e))
    st.stop()

if not codes:
    st.info("証券コードを入力してください。")
    st.stop()

summaries = []
details = {}
for code in codes:
    try:
        df = load_price_history(code, period)
        df = compute_indicators(df)
        signal = evaluate_sell_signal(df)
    except Exception as e:
        st.warning(f"{code}: {e}")
        continue

    details[code] = (df, signal)
    summaries.append(
        {
            "証券コード": code,
            "最新終値": round(float(df["Close"].iloc[-1]), 1),
            "シグナル": f"{LEVEL_ICON.get(signal.level, '')} {signal.level}",
            "主な理由": signal.reasons[0] if signal.reasons else "",
            "_order": SIGNAL_LEVEL_ORDER.get(signal.level, 99),
        }
    )

if not summaries:
    st.stop()

summary_df = pd.DataFrame(summaries).sort_values("_order").drop(columns="_order")
st.subheader("ウォッチリスト")
st.dataframe(summary_df, use_container_width=True, hide_index=True)

selected_code = st.selectbox("詳細を表示する銘柄", summary_df["証券コード"].tolist())
df, signal = details[selected_code]

st.subheader(f"{LEVEL_ICON.get(signal.level, '')} {selected_code} の売り検討シグナル: {signal.level}")
for reason in signal.reasons:
    st.write(f"- {reason}")

price_fig = go.Figure()
price_fig.add_trace(
    go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name="株価",
    )
)
price_fig.add_trace(go.Scatter(x=df.index, y=df["ma_short"], name=f"{MA_SHORT_WINDOW}日移動平均", line=dict(width=1)))
price_fig.add_trace(go.Scatter(x=df.index, y=df["ma_long"], name=f"{MA_LONG_WINDOW}日移動平均", line=dict(width=1)))
price_fig.update_layout(title="株価チャート", xaxis_rangeslider_visible=False, height=450)
st.plotly_chart(price_fig, use_container_width=True)

turnover_fig = go.Figure()
turnover_fig.add_trace(go.Bar(x=df.index, y=df["turnover"], name="売買代金"))
turnover_fig.add_trace(
    go.Scatter(x=df.index, y=df["turnover_ma"], name=f"{TURNOVER_MA_WINDOW}日平均売買代金", line=dict(width=1))
)
turnover_fig.update_layout(title="売買代金", height=300)
st.plotly_chart(turnover_fig, use_container_width=True)

display_columns = ["Close", "Volume", "turnover", "turnover_ratio", "ma_short", "ma_long"]
st.dataframe(df.tail(20)[display_columns].sort_index(ascending=False))
