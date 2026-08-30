# タスクリスト: 過去データでのシミュレーション機能の追加

## 実装タスク
- [x] `stock_signals.py`: `compute_signal_levels(df)` を追加(日ごとのシグナルレベルをベクトル演算で算出)
- [x] `stock_signals.py`: `Trade` データクラスを追加
- [x] `stock_signals.py`: `simulate_sell_strategy(df, sell_levels)` を追加
- [x] `stock_signals.py`: `buy_and_hold_return(df)` を追加
- [x] `app.py`: 各銘柄expander内にシミュレーション結果セクションを追加(損益率の比較・取引一覧・注記)
- [x] 単体データでの動作確認(ダミーDataFrameで `simulate_sell_strategy` の売買タイミングが意図通りか検証)

## 進捗状況
実装完了。ダミーデータでのシグナル発生→売却→再購入→保有中(含み損益)のサイクル、シグナルが一度も出ないケース、データ不足の短い期間、いずれも意図通り動作することを確認済み。Streamlitサーバーの起動確認も実施済み。

このサンドボックス環境ではYahoo Financeへの通信がブロックされているため、実データでの見た目確認は未実施。利用者側の環境での確認が必要。

## 完了条件
* `.steering/20260830-add-backtest-simulation/requirements.md` に記載した受け入れ条件をすべて満たす
* `python -m py_compile app.py stock_signals.py` が成功する
* ダミーデータ(シグナルが発生するように調整したDataFrame)で `simulate_sell_strategy` を実行し、購入→売却→再購入のサイクルが意図通りに記録されることを確認する
* Streamlitサーバーが正常に起動し、追加した表示ブロックがエラーなく描画されることを確認する(このサンドボックス環境ではYahoo Financeへの通信がブロックされているため、実データでの見た目確認は利用者側の環境で行う)
* 変更内容をコミットし、`git-san-934/stock-investing` の `main` ブランチにpushする
