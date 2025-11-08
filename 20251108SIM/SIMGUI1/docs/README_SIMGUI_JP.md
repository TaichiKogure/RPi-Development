# SIMGUI1: 弾性圧縮（パンチ）解析 GUI（Robust 版）

本ツールは `Calc2_robust.py`（SfePy 解析スクリプト）をバックエンドとして、
- 解析の Dry‑run（領域確認）実行
- 診断結果（region_attempts.csv、TopBandVerts プレビュー）の可視化
- 将来的な自動探索（Auto‑tune）
を行うためのデスクトップ GUI です。

保存先: `G:\RPi-Development\20251108SIM\SIMGUI1`

---

## 1. 前提条件
- Windows 10/11 での動作を想定
- Python 3.9+ を推奨（64bit）
- SfePy/Numpy/Pandas/Matplotlib/PySide6 が必要
  - `requirements.txt` から一括インストール可能です（venv 利用推奨）。
- 解析スクリプト: `G:\RPi-Development\20251108SIM\Calc2_robust.py` が存在していること

> 備考: SfePy は環境依存が大きいため、`pip install sfepy` に時間を要する場合があります。

---

## 2. セットアップと起動
1) コマンドプロンプトで以下を実行（`SIMGUI1` 直下）
```
G:\RPi-Development\20251108SIM\SIMGUI1> run_simgui.bat
```
- 初回は仮想環境 `venv` を作成し、`requirements.txt` をインストールします。
- その後 GUI (`gui/main.py`) が起動します。

> 既に独自の venv をお持ちの場合は、アクティベート後に以下でも起動できます。
```
(venv) G:\RPi-Development\20251108SIM\SIMGUI1> python -u gui\main.py
```

---

## 3. 使い方（Dry‑run 可視化）
1) 左側の「Parameters」で解析条件を入力（既定値のままでもOK）
   - 材料: `E`, `nu`
   - 幾何: `W`, `H`, `D`
   - 解析: `u_max`, `n_steps_load`, `n_steps_unload`
   - メッシュ: `nx`, `ny`
   - 堅牢化: `tol_abs`, `tol_factor`, `safety_growth`, `max_attempts`
2) 「Dry‑run」ボタンを押します。
   - 解析スクリプトが `--dry-run --diag-dir <生成フォルダ>` で実行されます。
   - 実行ログが左ペイン下の `Log` に流れます。
3) 実行終了後、右ペインに診断グラフが描画されます。
   - Attempts: 試行ごとの `tol / D_eff / y_top` と `facets / nodes` の推移
   - Preview: `TopBandVerts`（上部帯域の頂点プレビュー; 先頭~50点）散布図
4) 「Open Last Diag」で直近の診断フォルダをエクスプローラで開けます。

> 成功判定の目安: `nodes > 0`、可能なら `facets > 0`。GUIのグラフでご確認ください。

---

## 4. よくあるエラーと対策
- Solver not found: `Calc2_robust.py`
  - `core/config.py` の `CALC2_ROBUST_PATH` が実在パスを指しているか確認してください。
- Timeout
  - メッシュ/試行回数が重い場合に発生。`nx, ny` や `max_attempts` を適度に調整してください。
- SfePy の導入失敗
  - Visual C++ Build Tools などが必要な場合があります。SfePy の公式ドキュメントを参照してください。

---

## 5. 生成物（既定）
- 診断フォルダ: `SIMGUI1\output\diag_YYYYMMDD_HHMMSS`（自動作成）
  - `region_attempts.csv`: 試行ごとの `attempt, tol, D_eff, y_top, facets, nodes`
  - `topband_verts_preview.csv`: 先頭~50点の (x,y)
  - `topband_verts_indices.txt`: 頂点インデックス（参考）
- GUI ログ: `SIMGUI1\logs\simgui.log`（将来版で導入予定）

---

## 6. 設計メモ（要点）
- バックエンドはサブプロセス実行（確実に停止可能）。
- 解析の標準出力/標準エラーはGUIに転送し、終了後に診断CSVを読み込んで可視化します。
- 今後の拡張予定:
  - Auto‑tune（非収束/領域空時の自動探索）
  - 本解析の可視化（`result_elastic_press_robust.csv` の読取りとグラフ）
  - 設定保存・エクスポート（PNG/CSV/ZIP）

---

## 7. トラブルシュート（解析が失敗する）
- `TopBandVerts nodes == 0` となる場合
  - `tol_factor` を大きく（例: 0.5 → 1.0）
  - `safety_growth` を上げて `D` を拡張（例: 1.10 → 1.15）
  - `nx, ny` を増やす（メッシュを細かく）
- facet が 0 の場合
  - Robust‑3 では段階緩和と頂点フォールバックを実装しています（ログで確認）。

---

## 8. ライセンスと問い合わせ
- 本GUIは社内/個人用途を想定。第三者配布時は依存パッケージのライセンスに注意してください。
- 問い合わせ・改善要望は本プロジェクトのIssueトラッキングへ。