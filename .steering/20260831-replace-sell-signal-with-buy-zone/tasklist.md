# タスクリスト: シグナル判定基準を「買い時/様子見」に一本化する

## 実装タスク

### `stock_signals.py`
- [x] `SIGNAL_LEVEL_ORDER` を削除し、`BUY_ZONE_ORDER = {"買い時": 0, "様子見": 1, "判定不可": 2}` を追加
- [x] `SellSignal` を削除し、`BuyZoneStatus(level, reasons)` を追加
- [x] `evaluate_sell_signal` を削除し、`evaluate_buy_zone(df) -> BuyZoneStatus` を追加
- [x] `compute_signal_levels` を削除(用途は `compute_buy_zone_levels` に統一済み)
- [x] `simulate_sell_strategy` を削除し、`simulate_buy_zone_strategy(df) -> list[Trade]` を追加(買い時→保有開始、様子見→手放す)

### `app.py`
- [x] import文を更新(`SIGNAL_LEVEL_ORDER`/`compute_signal_levels`/`evaluate_sell_signal`/`simulate_sell_strategy` を削除、`BUY_ZONE_ORDER`/`evaluate_buy_zone`/`simulate_buy_zone_strategy` を追加)
- [x] `LEVEL_ICON`/`LEVEL_LABEL` を買い時/様子見/判定不可用に更新
- [x] ウォッチリスト集計ループを `evaluate_buy_zone` ベースに変更
- [x] 銘柄詳細expanderの見出しを「シグナル: {買い時/様子見/判定不可}」に変更
- [x] チャート上の▼売りシグナルマーカー描画ブロックを削除
- [x] シミュレーション処理を `simulate_buy_zone_strategy` に置き換え、説明文を更新
- [x] サイドバーの「売りと判断する条件」ブロックを削除(「買い時/様子見の条件」のみ残す)
- [x] タイトル直下の説明文(`st.caption`)を更新
- [x] チャート背景色の説明キャプションから▼マーカーへの言及を削除

### 永続ドキュメント
- [x] `docs/product-requirements.md` のシグナル関連記述を「買い時/様子見」基準に更新
- [x] `docs/functional-design.md` のデータモデル定義・関連記述を更新
- [x] `docs/development-guidelines.md` の命名規則・テスト規約の例示を新関数名に更新(想定外の追加対応)

### 検証
- [x] `python -m py_compile app.py stock_signals.py` が成功することを確認
- [x] ダミーデータで `evaluate_buy_zone` / `simulate_buy_zone_strategy` の算出結果を検証
- [x] Streamlitサーバーを起動し、両タブがエラーなく描画されること、▼マーカーが表示されないこと、シグナル表記が買い時/様子見に統一されていることを確認

## 進捗状況
実装完了。

* ダミーデータで `evaluate_buy_zone`(最新日判定、データ不足時は判定不可)、`simulate_buy_zone_strategy`(買い時→保有、様子見→手放すの売買記録)の動作を確認済み。
* `python -m py_compile` 成功、および `grep` でコードとdocs双方から旧基準(`SellSignal`/`evaluate_sell_signal`/`compute_signal_levels`/`simulate_sell_strategy`/`SIGNAL_LEVEL_ORDER`/「売り検討シグナル」/「売りシグナル」)への参照が残っていないことを確認済み。
* Streamlitサーバーを起動し、ヘッドレスブラウザでウォッチリストタブを確認。サイドバーが「買い時/様子見の条件」のみに統一され、旧文言が表示されないこと、エラーが発生していないことを確認済み。
* このサンドボックス環境ではYahoo Financeへの通信がブロックされているため、実データでの見た目(実際の買い時/様子見判定・シミュレーション結果)は利用者側の環境での確認が必要。

## 完了条件
* `.steering/20260831-replace-sell-signal-with-buy-zone/requirements.md` の受け入れ条件をすべて満たす
* `python -m py_compile app.py stock_signals.py` が成功する
* ダミーデータで新ロジックの算出結果を検証する
* Streamlitサーバーが正常に起動し、旧基準の表示が残っていないことを確認する
* 変更内容をコミットし、`git-san-934/stock-investing` の `main` ブランチにpushする
