# タスクリスト: 買い時/様子見の帯表示 と AIによる有望10銘柄選定機能の追加

## 実装タスク

### 機能1: 買い時/様子見の帯表示
- [x] `stock_signals.py`: `compute_buy_zone_levels(df)` を追加(終値とma_shortの位置関係から「買い時」「様子見」を算出)
- [x] `app.py`: 状態の連続区間を求めるヘルパーを追加し、`add_vrect` で株価チャート背景に帯を描画
- [x] `app.py`: 凡例用のダミートレース(買い時/様子見)を追加
- [x] `app.py`: 帯の意味を説明する注記(`st.caption`)を追加

### 機能2: AIによる有望10銘柄選定
- [x] `data/tse_universe.csv` を新規作成(東証上場銘柄の証券コード・銘柄名・市場区分)
- [x] `stock_signals.py`: `load_universe()` を追加
- [x] `stock_signals.py`: `fetch_price_history_batch(codes, period)` を追加(`yfinance.download` によるバッチ取得)
- [x] `stock_signals.py`: `score_stock(df)` を追加(乖離率・ゴールデンクロス・売買代金増加度・直近騰落率によるスコアリング)
- [x] `stock_signals.py`: `select_top_promising(n=10)` を追加(キャッシュ対応)
- [x] `app.py`: `st.tabs` で「ウォッチリスト」「有望銘柄(AI選定)」の2タブ構成に変更(既存ウォッチリスト表示は1つ目のタブへ移動、ロジック変更なし)
- [x] `app.py`: 「有望銘柄(AI選定)」タブに実行ボタン・進捗表示・結果テーブル(スコア根拠付き)・注記(投資助言でない旨/ユニバースが完全でない可能性がある旨)を追加
- [x] `docs/repository-structure.md` に `data/` ディレクトリの用途を追記

### 共通
- [x] 単体データ(ダミーDataFrame)で `compute_buy_zone_levels` / `score_stock` の算出結果が意図通りか検証
- [x] `python -m py_compile app.py stock_signals.py` が成功することを確認
- [x] Streamlitサーバーの起動確認(このサンドボックス環境ではYahoo Financeへの通信がブロックされているため、実データでの見た目確認は利用者側の環境で行う)

## 進捗状況
実装完了。

* ダミーデータで `compute_buy_zone_levels`(買い時/様子見の判定)、`score_stock`、`load_universe`、`zone_segments`(区間分割ロジック)の動作を確認済み。
* `fetch_price_history_batch` の複数銘柄抽出ロジック(yfinanceのマルチティッカーMultiIndex出力からの銘柄ごとの切り出し、データ取得不可銘柄の除外)は、`yf.download` の戻り値を模したダミーDataFrameで検証済み。
* Streamlitサーバーを実際に起動し、ヘッドレスブラウザ(Playwright)で「ウォッチリスト」「有望銘柄(AI選定)」両タブが正常に描画されること、「有望銘柄を探索する」ボタン押下でエラーにならないことを確認済み。
* **実装時に発見・修正したバグ**: タブ化にあたり、ウォッチリストタブ内で使っていた `st.stop()` がスクリプト全体を停止させてしまい、ウォッチリストの取得結果が空の場合に「有望銘柄(AI選定)」タブが一切描画されない不具合があった。各タブの描画処理を関数化し、`st.stop()` を早期`return`に置き換えて修正した。
* このサンドボックス環境ではYahoo Financeへの通信がブロックされているため(前回のバックテスト機能追加時と同様)、実際の株価データでの見た目・スコアリング結果の確認は未実施。利用者側の環境での確認が必要。
* 対象ユニバース(`data/tse_universe.csv`)は、外部データ取得手段の制約により東証全銘柄(約3,900件)ではなく、既存の主要銘柄リスト(81銘柄、プライム市場中心)を流用している。設計時に合意した代替方針(design.md記載)に沿った対応。

## 完了条件
* `.steering/20260831-buy-sell-zone-and-ai-top10-picks/requirements.md` に記載した受け入れ条件をすべて満たす
* `python -m py_compile app.py stock_signals.py` が成功する
* ダミーデータで `compute_buy_zone_levels` と `score_stock` の算出結果を検証する
* Streamlitサーバーが正常に起動し、追加した表示(帯・タブ・有望銘柄一覧)がエラーなく描画されることを確認する
* 変更内容をコミットし、`git-san-934/stock-investing` の `main` ブランチにpushする
