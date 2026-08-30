# タスクリスト: 売り検討シグナルの判定条件を25日移動平均線割れに変更

## 実装タスク
- [x] `stock_signals.py`: `evaluate_sell_signal` を25日移動平均線割れ判定に置き換え
- [x] `stock_signals.py`: `compute_signal_levels` を同条件のベクトル演算に置き換え
- [x] `stock_signals.py`: `SIGNAL_LEVEL_ORDER` を3段階に簡略化
- [x] `stock_signals.py`: `simulate_sell_strategy` の `sell_levels` デフォルトを `("強",)` に変更
- [x] `stock_signals.py`: 不要定数(`TURNOVER_SPIKE_RATIO`, `HIGH_LOOKBACK`, `NEAR_HIGH_THRESHOLD`)を削除
- [x] `app.py`: `LEVEL_ICON` を整理、サイドバーの条件説明文を更新
- [x] `docs/product-requirements.md`: 機能要件・受け入れ条件を新条件に更新
- [x] `docs/functional-design.md`: 確認の結果、旧ロジックの詳細記述がなく変更不要だった
- [x] `docs/glossary.md`: 用語定義を新条件に更新(不要な用語の削除含む)
- [x] `README.md`: シグナルの考え方の説明を新条件に更新(範囲外だが同じ段落内の古い記述も合わせて修正)
- [x] 単体データでの動作確認

## 進捗状況
実装完了。ダミーデータで、終値が25日移動平均線を下回った期間に正しく「強」判定になること、データ不足時に「判定不可」になることを確認済み。Streamlitサーバーの起動確認も実施済み。

このサンドボックス環境ではYahoo Financeへの通信がブロックされているため、実データでの見た目確認は未実施。利用者側の環境での確認が必要。

## 完了条件
* `python -m py_compile app.py stock_signals.py` が成功する
* ダミーデータで、終値が25日移動平均線を下回った日に正しく「強」判定になることを確認する
* Streamlitサーバーが正常に起動する
* 変更内容をコミットし、`git-san-934/stock-investing` の `main` ブランチにpushする
