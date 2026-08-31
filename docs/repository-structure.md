# リポジトリ構造定義書

## フォルダ・ファイル構成

```
stock-investing/
├── CLAUDE.md                      # プロジェクトメモリ(開発プロセスの定義)
├── README.md                      # プロジェクト概要・セットアップ手順
├── LICENSE                        # MITライセンス
├── requirements.txt                # Python依存パッケージ一覧
├── .gitignore
│
├── app.py                          # Streamlit UI本体(エントリーポイント)
├── stock_signals.py                # データ取得・指標計算・シグナル判定ロジック
│
├── data/                           # 静的データ(コード管理する参照データ)
│   └── tse_universe.csv            # AI銘柄選定の対象ユニバース(証券コード・銘柄名・市場区分)
│
├── docs/                           # 永続的ドキュメント
│   ├── product-requirements.md     # プロダクト要求定義書
│   ├── functional-design.md        # 機能設計書
│   ├── architecture.md             # 技術仕様書
│   ├── repository-structure.md     # 本ファイル
│   ├── development-guidelines.md   # 開発ガイドライン
│   └── glossary.md                 # ユビキタス言語定義
│
└── .steering/                      # 作業単位のドキュメント(作業ごとにディレクトリを追加)
    └── [YYYYMMDD]-[開発タイトル]/
        ├── requirements.md
        ├── design.md
        └── tasklist.md
```

## ディレクトリの役割
* **ルート直下**: アプリの実行に必要な最小限のファイルのみを置く。UIコード(`app.py`)とロジックコード(`stock_signals.py`)を分離し、それぞれが単一の責務(UI描画 / データ取得・計算)を持つようにする。
* **`data/`**: アプリが参照する静的な参照データ(CSV等)を置く。頻繁に更新しない前提のデータのみを対象とし、実行時に生成される一時データは置かない。
* **`docs/`**: `CLAUDE.md` で定義された6種類の永続的ドキュメントを置く。基本設計や方針が変わらない限り更新しない。
* **`.steering/`**: 機能追加・修正など個別の作業ごとに `[YYYYMMDD]-[開発タイトル]` ディレクトリを作成し、その作業のrequirements/design/tasklistを置く。作業完了後も履歴として保持し、削除しない。

## ファイル配置ルール
* 新しい機能を実装する際、UIに関するコードは `app.py` に、データ取得・指標計算・シグナル判定のロジックは `stock_signals.py` に置く。
* ロジックコードが肥大化してきた場合(目安: 1ファイル300行超、または明確に異なる責務が混在する場合)は、`.steering/` の作業ドキュメント(design.md)で分割方針を検討したうえでモジュールを分割する。現時点(2ファイル構成)では時期尚早な分割は行わない。
* テストコードを追加する場合は、ルート直下に `tests/` ディレクトリを新設し、`tests/test_stock_signals.py` のように対象モジュール名に対応させる。
* 秘密情報(APIキー等)を扱うことになった場合は `.env` に置き、`.gitignore` に含める(現時点ではAPIキー不要のため該当ファイルはない)。
