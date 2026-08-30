# タスクリスト: 売り検討シグナルの判定条件を25日移動平均線割れに変更

## 実装タスク
- [ ] `stock_signals.py`: `evaluate_sell_signal` を25日移動平均線割れ判定に置き換え
- [ ] `stock_signals.py`: `compute_signal_levels` を同条件のベクトル演算に置き換え
- [ ] `stock_signals.py`: `SIGNAL_LEVEL_ORDER` を3段階に簡略化
- [ ] `stock_signals.py`: `simulate_sell_strategy` の `sell_levels` デフォルトを `("強",)` に変更
- [ ] `stock_signals.py`: 不要定数(`TURNOVER_SPIKE_RATIO`, `HIGH_LOOKBACK`, `NEAR_HIGH_THRESHOLD`)を削除
- [ ] `app.py`: `LEVEL_ICON` を整理、サイドバーの条件説明文を更新
- [ ] `docs/product-requirements.md`: 機能要件・受け入れ条件を新条件に更新
- [ ] `docs/functional-design.md`: 機能アーキテクチャの説明を新条件に更新
- [ ] `docs/glossary.md`: 用語定義を新条件に更新(不要な用語の削除含む)
- [ ] 単体データでの動作確認

## 進捗状況
未着手(承認後に着手する)

## 完了条件
* `python -m py_compile app.py stock_signals.py` が成功する
* ダミーデータで、終値が25日移動平均線を下回った日に正しく「強」判定になることを確認する
* Streamlitサーバーが正常に起動する
* 変更内容をコミットし、`git-san-934/stock-investing` の `main` ブランチにpushする
