# タスクリスト: 過去データでのシミュレーション機能の追加

## 実装タスク
- [ ] `stock_signals.py`: `compute_signal_levels(df)` を追加(日ごとのシグナルレベルをベクトル演算で算出)
- [ ] `stock_signals.py`: `Trade` データクラスを追加
- [ ] `stock_signals.py`: `simulate_sell_strategy(df, sell_levels)` を追加
- [ ] `stock_signals.py`: `buy_and_hold_return(df)` を追加
- [ ] `app.py`: 各銘柄expander内にシミュレーション結果セクションを追加(損益率の比較・取引一覧・注記)
- [ ] 単体データでの動作確認(ダミーDataFrameで `simulate_sell_strategy` の売買タイミングが意図通りか検証)

## 進捗状況
未着手(このタスクリストの承認後に着手する)

## 完了条件
* `.steering/20260830-add-backtest-simulation/requirements.md` に記載した受け入れ条件をすべて満たす
* `python -m py_compile app.py stock_signals.py` が成功する
* ダミーデータ(シグナルが発生するように調整したDataFrame)で `simulate_sell_strategy` を実行し、購入→売却→再購入のサイクルが意図通りに記録されることを確認する
* Streamlitサーバーが正常に起動し、追加した表示ブロックがエラーなく描画されることを確認する(このサンドボックス環境ではYahoo Financeへの通信がブロックされているため、実データでの見た目確認は利用者側の環境で行う)
* 変更内容をコミットし、`git-san-934/stock-investing` の `main` ブランチにpushする
