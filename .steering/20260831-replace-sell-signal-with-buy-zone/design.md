# 設計: シグナル判定基準を「買い時/様子見」に一本化する

## 実装アプローチ

### 1. `stock_signals.py`
* **削除**: `SIGNAL_LEVEL_ORDER`、`SellSignal`、`evaluate_sell_signal`、`compute_signal_levels`、`simulate_sell_strategy`(旧基準前提のため置き換え後は不要)
* **追加**:
  * `BUY_ZONE_ORDER = {"買い時": 0, "様子見": 1, "判定不可": 2}`(一覧の並び替え用。買い時を最上位にする)
  * `BuyZoneStatus` データクラス(`level: str`, `reasons: list[str]`)。`SellSignal` の置き換え。
  * `evaluate_buy_zone(df) -> BuyZoneStatus`: 最新日について、終値が25日移動平均線より上/下かを判定して `"買い時"` / `"様子見"` を返す(データ不足時は `"判定不可"`)。判定条件は既存の `compute_buy_zone_levels`(全期間版)と同じ考え方を最新日のみに適用したもの。
  * `simulate_buy_zone_strategy(df) -> list[Trade]`: 「買い時になったら保有を開始し、様子見になったら手放す」ルールでシミュレーションする。既存の `Trade` データクラスをそのまま使う。ロジックは `compute_buy_zone_levels` の結果を時系列で走査し、状態遷移のタイミングで売買を記録する(未算出区間はスキップ)。手数料・税金は考慮しない。
* **変更なし**: `compute_buy_zone_levels`(既存)、`buy_and_hold_return`、`load_universe` 以降のAI選定関連関数

### 2. `app.py`
* import: `SIGNAL_LEVEL_ORDER` / `compute_signal_levels` / `evaluate_sell_signal` / `simulate_sell_strategy` を削除し、`BUY_ZONE_ORDER` / `evaluate_buy_zone` / `simulate_buy_zone_strategy` に置き換える
* `LEVEL_ICON` / `LEVEL_LABEL` を買い時/様子見/判定不可用に redefine する(アイコン: 買い時=🔴、様子見=🟡、判定不可=⚪。チャート背景の赤/黄色と印象を合わせる)
* ウォッチリスト集計ループ: `evaluate_sell_signal(df)` → `evaluate_buy_zone(df)` に置き換え、並び替えキーも `BUY_ZONE_ORDER` を使う
* 銘柄詳細expanderの見出し: 「売り検討シグナル: なし」→「シグナル: 様子見」のように、ラベルを「シグナル: {買い時/様子見/判定不可}」に変更
* チャート内の▼売りシグナルマーカー(`compute_signal_levels` を使っていたブロック)を削除する。買い時/様子見の背景帯(既存実装、変更なし)のみで状態を表す
* 過去データでのシミュレーション: `simulate_sell_strategy(df)` → `simulate_buy_zone_strategy(df)` に置き換え、説明文(`st.caption`)を新ルールの内容に更新する(「買い時になったら保有し、様子見になったら手放すルールで計算した参考値です」等)
* サイドバーの「売りと判断する条件」ブロックを削除し、「買い時/様子見の条件」のみを残す(見出しも「判定基準」等に整理)
* タイトル直下の説明文(`st.caption`)を、下抜け検知ではなく買い時/様子見の位置関係ベースである旨に更新する
* チャート下の背景色説明キャプションから「売り検討シグナル(▼マーク)とは別の判定です」の一文を削除する(▼マーカー自体が無くなるため)

### 3. 永続ドキュメントの更新(基本設計への影響)
* `docs/product-requirements.md`: 主要な機能一覧・ユーザーストーリー・受け入れ条件・機能要件(FR-5, FR-6)のうち、「売り検討シグナル(強/なし/判定不可、下抜け検知)」に言及している箇所を「買い時/様子見(判定不可を含む)」の表現に更新する
* `docs/functional-design.md`: データモデル定義(`SellSignal` → `BuyZoneStatus`)、機能ごとのアーキテクチャの説明を更新する

## 変更するコンポーネント
* **`stock_signals.py`**: 上記の削除・追加
* **`app.py`**: 上記の置き換え・削除
* **`docs/product-requirements.md`**, **`docs/functional-design.md`**: シグナル関連の記述を更新

## データ構造の変更
* `SellSignal(level, reasons)` を廃止し、`BuyZoneStatus(level, reasons)` に置き換える(フィールド構成は同じ、意味のみ変更)

## 影響範囲の分析
* 「有望銘柄(AI選定)」タブ・スコアリングロジックには影響しない(独立した関数のまま)
* 買い時/様子見の背景帯表示の描画ロジック自体は変更しない(既存の `compute_buy_zone_levels` / `zone_segments` を流用)
* シミュレーション結果の数値は、旧ロジック(下抜け検知による売買)とは異なる新しい売買ルールに基づくため、以前表示されていた損益率とは変わる(利用者の指示通り、旧基準は使わない前提のため想定内の変更)
