"""株の売り時判断ダッシュボード(東証銘柄向け)。"""

import plotly.graph_objects as go
import streamlit as st

from stock_signals import (
    MA_LONG_WINDOW,
    MA_SHORT_WINDOW,
    TURNOVER_MA_WINDOW,
    compute_indicators,
    evaluate_sell_signal,
    fetch_price_history,
)

st.set_page_config(page_title="売り時判断ダッシュボード", layout="wide")

st.title("株の売り時判断ダッシュボード")
st.caption("売買代金の急増と株価チャートの動きから売り時の目安を表示します。投資助言ではありません。")

with st.sidebar:
    code = st.text_input("証券コード", value="7203", help="例: トヨタ自動車なら 7203")
    period = st.selectbox("表示期間", ["6mo", "1y", "2y"], index=1)
    run = st.button("表示する")

if run or code:
    try:
        df = fetch_price_history(code, period=period)
        df = compute_indicators(df)
        signal = evaluate_sell_signal(df)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    level_icon = {"強": "🔴", "中": "🟠", "弱": "🟡", "なし": "🟢", "判定不可": "⚪"}
    st.subheader(f"{level_icon.get(signal.level, '')} 売り検討シグナル: {signal.level}")
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
