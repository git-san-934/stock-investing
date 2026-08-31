# 開発ガイドライン

## コーディング規約

### 命名規則
* 変数・関数名: `snake_case`(例: `fetch_price_history`, `turnover_ratio`)
* 定数: `UPPER_SNAKE_CASE`(例: `TURNOVER_SPIKE_RATIO`, `MA_SHORT_WINDOW`)。マジックナンバーは直接コード中に書かず、モジュール冒頭で定数化する。
* クラス・データクラス: `PascalCase`(例: `BuyZoneStatus`)
* 証券コード関連の変数名は `code`(ユーザー入力の生の証券コード)と `symbol`(yfinance用に変換済みのシンボル、`.T`付き)を区別して使う

### スタイリング規約
* [PEP 8](https://peps.python.org/pep-0008/) に準拠する
* 公開関数(モジュール外から呼ばれる関数)には型ヒントを付ける
* コメントはデフォルトで書かない。書く場合も「なぜそうしたか」(閾値の根拠、既知の制約への対処など)のみを短く記載し、コードを読めば分かる内容は書かない
* docstringは1行程度の簡潔な日本語で、関数の目的のみを書く(引数・戻り値の詳細な列挙はしない)
* UI文言(Streamlitの表示テキスト)は日本語で統一する

### テスト規約
* テストフレームワークには `pytest` を使用する
* テストファイルはルート直下の `tests/` ディレクトリに置き、対象モジュールに対応させる(例: `stock_signals.py` → `tests/test_stock_signals.py`)
* テスト関数名は `test_<対象関数>_<条件・期待結果>` の形式とする(例: `test_evaluate_buy_zone_close_above_ma_returns_buy`)
* ネットワークアクセス(yfinance呼び出し)を伴うテストは、実データではなくダミーのDataFrameを用いて `compute_indicators` / `evaluate_buy_zone` などの純粋なロジック部分を検証する
* 実装当初はテスト未整備の状態からスタートしてよいが、`stock_signals.py` にロジックを追加・変更する際はテストの追加を検討する

### Git規約
* コミットメッセージは日本語で記述する
* 1行目に変更内容の要約、空行を挟んで本文に変更理由・詳細を記述する
* 個人開発かつ小規模リポジトリのため、`main` ブランチへの直接コミット・pushを許容する。ただし影響範囲の大きい変更(既存シグナルロジックの閾値変更など)は、作業前に `.steering/` の設計ドキュメントで合意を得てから進める
* `.venv/`, `__pycache__/`, `.streamlit/`, `.env` 等の生成物・秘密情報はコミットしない(`.gitignore` で除外済み)
