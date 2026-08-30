# 設計: 売り検討シグナルの判定条件を25日移動平均線割れに変更

## 実装アプローチ
1. `stock_signals.py` の `evaluate_sell_signal` を、以下のロジックに置き換える
   * `latest["Close"] < latest["ma_short"]` であれば level="強"、そうでなければ level="なし"
   * データ不足(`len(df) < MA_SHORT_WINDOW + 1`)の場合は level="判定不可"
   * 売買代金急増・高値圏・デッドクロスに関する条件分岐・reasons文言は削除する
2. `compute_signal_levels`(バックテスト用)も同じ条件でベクトル演算に置き換える
   * `df["Close"] < df["ma_short"]` の行を level="強"、それ以外を level="なし" とする
3. `SIGNAL_LEVEL_ORDER` を `{"強": 0, "なし": 1, "判定不可": 2}` に簡略化する(「中」「弱」を削除)
4. `simulate_sell_strategy` の `sell_levels` デフォルト引数を `("強",)` に変更する
5. `app.py` の `LEVEL_ICON` から使わなくなった「中」「弱」のキーを削除する
6. `app.py` サイドバーの「売りと判断する条件」の説明文を、新しい単一条件の説明に書き換える
7. 不要になった定数(`TURNOVER_SPIKE_RATIO`, `HIGH_LOOKBACK`, `NEAR_HIGH_THRESHOLD`)は `stock_signals.py` から削除する。`TURNOVER_MA_WINDOW` と `MA_LONG_WINDOW` はチャート表示(売買代金グラフ・75日移動平均線)に引き続き使うため残す

## 変更するコンポーネント
* `stock_signals.py`: `evaluate_sell_signal` / `compute_signal_levels` / `SIGNAL_LEVEL_ORDER` / 不要定数の削除
* `app.py`: `LEVEL_ICON` の整理、サイドバーの条件説明文、`simulate_sell_strategy` 呼び出し箇所の確認(デフォルト引数変更のため呼び出し側の変更は不要)

## 影響範囲の分析
* シグナルの意味が変わるため、既存のシミュレーション結果・ウォッチリストの表示内容は変わる(想定通りの変更)
* チャート描画(株価チャート・売買代金チャート)自体のロジックは変更しない
* `docs/product-requirements.md`(機能要件・受け入れ条件)、`docs/functional-design.md`(機能アーキテクチャの説明)、`docs/glossary.md`(売り検討シグナル・売買代金急増・高値圏・デッドクロスの定義)を、新しい条件に合わせて更新する必要がある
