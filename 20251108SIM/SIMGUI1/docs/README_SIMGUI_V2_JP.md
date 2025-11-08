# SIMGUI1 Ver2: パラメータ総当たり（グリッド探索）機能

本ドキュメントは、Calc2_robust.py をバックエンドにした SIMGUI1 の Ver2 機能（パラメータ範囲の分割と総当たり探索）について説明します。

## 概要
- 目的: 領域生成（TopBand/TopBandVerts）が安定して成功するパラメータ組合せを、自動で探索・提示します。
- 実行方式: `Calc2_robust.py` をサブプロセスとして起動し、
  - Region-Only モード: `--dry-run` で領域の非空（nodes>0）を判定。
  - Quick-Solve モード: Region 合格の上位K候補に対し、短縮ステップで本解析を実施（既定 5+5）。
- 出力: 結果テーブル（GUI）と CSV エクスポート、各試行の診断ディレクトリ（region_attempts.csv 等）。

## 既定値
- 振るパラメータ（有効化済）: `tol_factor`, `safety_growth`, `D`, `nx`, `ny`
- グリッド上限 `max_points`: 10000
- 並列数 `n_procs`: 10（初期版は順次実行。今後の並列実行に備えた設定項目として維持）
- Quick-Solve 短縮ステップ: `n_steps_load=5`, `n_steps_unload=5`（GUIで変更可能）
- タイムアウト（既定）: dry 60s, quick 180s
- 時間予算: 60 分（GUIで変更可能）

## 使い方
1. SIMGUI1 を起動（`run_simgui.bat` もしくは `python gui/main.py`）。
2. 右ペインのタブから「Search (Ver2)」を選択。
3. Parameter Ranges
   - 各パラメータの min/max/steps/scale（linear or log）を設定。
   - チェックを外すと探索対象から除外。
4. Search Settings
   - mode: `region`（領域のみ判定）/`quick`（合格候補に短縮本解析）。
   - max_points, n_procs（将来並列対応）, time budget, timeouts を設定。
   - quick steps（load/unload）と topK quick を設定。
5. Start Search で探索開始。
   - 進捗バーと件数（done/total）が表示されます。
   - テーブルに結果が逐次追加されます。
6. Export CSV
   - 現在の結果テーブルを CSV に保存。
7. Apply to Run panel
   - 選択行のパラメータ（tol_factor, safety_growth, D, nx, ny）を左ペイン（Run）に反映。
   - そのまま従来の Dry-run / Run を実行できます。

## 成功判定・順位付け
- 最低成功条件: `nodes > 0`（必要に応じて `facets >= 1` を推奨）。
- 表示列: `success_region, nodes, facets, tol, D_eff, y_top` など。
- Quick-Solve 実行時は、最終 `Fy_N`, `uy_center` などを付加。

## 出力とフォルダ構成
- 出力先の既定ルート: `SIMGUI1/output/`（内部で `diag_YYYYMMDD_HHMMSS` や `search_...` を自動生成）。
- 各試行の診断ディレクトリに `region_attempts.csv` が生成されます（Robust-3 対応列: `attempt, tol, D_eff, y_top, facets, nodes`）。
- Export CSV: 検索結果テーブルをまとめたファイル（columns は GUI に準拠）。

## よくある質問（FAQ）
- 探索が重い / 時間がかかる
  - `max_points` を絞る（例: 1000 以下）。
  - `steps` を減らす、`time_budget` を短くする。
  - まずは `region` モードで広く探索→上位候補のみ `quick`。
- すべて失敗になる
  - レンジの最小/最大を見直し（特に `tol_factor` と `safety_growth`）。
  - `nx, ny` を増やしてメッシュ解像度を上げる。
  - `D` を ±10〜20% 程度振って格子点に載る確率を上げる。
- Quick-Solve の結果が空
  - タイムアウトが短い可能性。`timeout quick [s]` を延ばしてください。

## 既知の制限
- 初期版では `n_procs` は将来拡張用の設定項目です（順次実行）。
- 個別試行のログは標準出力の要約のみをテーブルに反映します。詳細は各 `diag_dir` を参照してください。

## トラブルシュート
- `Solver not found` エラー
  - `core/config.py` の `CALC2_ROBUST_PATH` が実在パスか確認。
- 探索がすぐ停止する
  - `time budget [min]` に達した可能性。値を上げる。
- 結果が空
  - レンジの steps を増やす、範囲を広げる、`tol_factor`/`safety_growth` を大きくする。

## 変更履歴
- 2025-11-08: Ver2 初期版（Search タブ、グリッド探索、Apply/Export、Quick-Solve 5+5 既定）。
