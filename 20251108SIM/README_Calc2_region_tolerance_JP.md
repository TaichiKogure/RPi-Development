# Calc2_robust: TopBandVerts が空になる問題の恒久対策と使い方

本書は SfePy を用いた 2D 弾性圧縮（パンチ）解析において、上部パンチ帯域の頂点集合 `TopBandVerts` が空になり、境界条件や反力集計が機能しない問題に対する恒久対策をまとめたものです。合わせて、新規スクリプト `Calc2_robust.py` の使い方とトラブルシュートを記載します。

---

## 問題の核心（再整理）
- トップ境界 y = max_y の取り扱いが厳しすぎる（`y > max_y - ε` 等）
- メッシュ刻みよりも小さいトレランスで境界頂点が含まれない
- `facet`（面領域）と **頂点集合** を混在使用
- パンチ幅 D の左右端が格子点に合わず、端部の頂点が漏れる

これらが重なると、`TopBandVerts` のエンティティ数が 0 となり、反力集計や中心変位の抽出が失敗します。

---

## 解決方針（恒久対策）
1. 非厳密比較（`>=`, `<=`）を用いる。
2. 幾何トレランス `tol` はメッシュ解像度に応じて設定：
   - `tol_abs = 1e-12`（下限の絶対トレランス）
   - `tol_geom = tol_factor * min(hx, hy)`（`hx=W/nx`, `hy=H/ny`）
   - 採用トレランス `tol = max(tol_abs, tol_geom)`
3. 用途分離：
   - 境界条件には面領域 `TopBand`（`facet` 指定）
   - 反力・DOF 抽出は頂点集合 `TopBandVerts`（`facet` なし）
4. 自動リトライ機構：
   - `tol` を指数的に拡大（例：×2）
   - パンチ幅 D を安全係数で段階拡張（例：+5%/試行）
   - 最大試行回数まで続け、非空になった時点で確定

---

## 追加したスクリプトの概要
- ファイル: `G:\RPi-Development\20251108SIM\Calc2_robust.py`
- 特徴:
  - `TopBand`/`TopBandVerts` を **自動リトライ** で堅牢に構築
  - ログに試行回数、実効 `tol` と `D`、選択頂点数、x 範囲、y 平均などを出力
  - `--dry-run` で領域構築だけ確認可能（ソルバーは回さない）
  - 既存 CSV 形式と互換（`result_elastic_press_robust.csv`）

---

## 使い方
### 1) ドライラン（領域確認のみ）
```
python G:\RPi-Development\20251108SIM\Calc2_robust.py --dry-run --log-level DEBUG
```
- 期待出力（例）
```
Attempt 1/4: tol=2.083e-04, D_eff=0.020000, TopBand facets=240, TopBandVerts nodes=121
TopBandVerts x-range=(0.040000,0.060000), y≈0.010000
[DRY-RUN] TopBandVerts count: 121
[DRY-RUN] Preview first nodes (x,y):
[[0.04083333 0.01      ]
 ...]
```
- `nodes=0` の場合は自動で `tol`/`D` を広げて再試行します。

### 2) 本解析の実行
```
python G:\RPi-Development\20251108SIM\Calc2_robust.py --log-level INFO
```
- 出力: `result_elastic_press_robust.csv`
- 末尾 5 行を標準出力に表示。

### 3) 主なパラメータ（必要時のみ指定）
- 幾何トレランス関連
  - `--tol-abs 1e-12`（絶対下限）
  - `--tol-factor 0.25`（`min(h)` に対する係数）
- バンド拡張
  - `--safety-growth 1.05`（試行ごとに D を 5% 拡張）
  - `--max-attempts 4`（最大試行回数）
- メッシュ/材料/荷重
  - `--nx 120 --ny 30`、`--E 1e10 --nu 0.3`、`--u-max 1e-4`

---

## 実装上の要点
- `TopBand`（facet）と `TopBandVerts`（vertices）の **分離**
- 非厳密比較：`(y >= y_top) & (x >= x_left) & (x <= x_right)`
- 反力は `r[dof_y]` の負号総和（`dof_y = 2*n + 1`）
- 中心ノードは「x0 に最も近い」かつ同距離なら「y が最大」を優先
- DOF 範囲チェック、および頂点番号の重複排除

---

## トラブルシュート
- 症状: `TopBandVerts に頂点が見つかりません` で停止
  1. `--dry-run` で領域だけ検証
  2. `--tol-factor` を 0.25 → 0.5 に上げる
  3. `--safety-growth` を 1.05 → 1.10 に上げる
  4. `--max-attempts` を 6 以上に拡大
  5. メッシュ密度 `nx, ny` を増やす
- 症状: 反力 `Fy_N` が極端に小さい/大きい
  - `TopBandVerts x-range` が意図した D と一致しているかログで確認
  - `TopBand` が空でないか（`facets>0`）を確認
- 症状: 解析が重い
  - `nx, ny` を適度に下げる、または `Integral(order=1)` へ（一貫性注意）

---

## 参考（背景知識）
- SfePy の region 構文
  - 頂点集合: `vertices in (<論理式>)`
  - 面領域: 第 3 引数 `'facet'`
  - 論理積/和: `(&)`, `(|)`、括弧は多めに
- 2D ベクトル DOF: `u = [u.x, u.y]` → ノード n の y-DOF は `2*n + 1`

---

## 既存スクリプトとの関係
- 既存の `Calc2.py` は従来どおり使用可能です。
- `Calc2_robust.py` は **領域選択の自動調整と詳細診断** を備えた堅牢版です。
- 同一条件での比較・検証にお使いください。

---

## 付録：よくある数式の誤り
- `y > max_y`（厳しすぎ）→ `y >= max_y - tol`
- `x > x_left` / `x < x_right`（厳しすぎ）→ `x >= x_left - tol` / `x <= x_right + tol`
- `facet` を付けた頂点集合（誤り）→ 頂点集合は `facet` なし


---

## 追記（Ver. Robust-2 修正ポイント）
- トレランス算出の誤り修正：`nx, ny` に誤って `n_nod-1` を使っていた点を修正し、実際のメッシュ分割数から `hx=W/nx, hy=H/ny` を計算するようにしました。
- 既定値の強化：`max_attempts=6`、`safety_growth=1.10` に増強し、閾値に届かず空領域になるケースを減らしました。
- facet フォールバック：`vertices` が非空だが `facet` が 0 のとき、`y_top` を緩めて `facet` を再生成する軽微なフォールバックを追加しました。
- 診断出力：`--diag-dir <PATH>` を指定すると、`region_attempts.csv`（試行ごとの tol/D_eff/件数）と、`--dry-run` 時に `topband_verts_preview.csv` / `topband_verts_indices.txt` を出力します。

### 実行例（診断付き）
```
python G:\RPi-Development\20251108SIM\Calc2_robust.py \
  --dry-run --log-level DEBUG \
  --diag-dir G:\\RPi-Development\\20251108SIM\\diag_robust
```

解析を回す場合：
```
python G:\RPi-Development\20251108SIM\Calc2_robust.py \
  --log-level INFO \
  --diag-dir G:\\RPi-Development\\20251108SIM\\diag_robust
```


---

## 追記（Robust-3 修正ポイント・2025-11-08）
今回の例外（`build_regions_with_retries()` が全試行で `TopBand/TopBandVerts` を非空にできない）に対し、以下の恒久修正を行いました（Calc2_robust.py）。

- 最上面の y 条件をメッシュ解像度に依存して緩和
  - 旧: `y >= max_y - tol`
  - 新: `y >= max_y - max(tol, hy/2)` （`hy = H/ny`）
  - これにより格子最上段の頂点を安定して拾えます。
- facet==0 の場合のフォールバック強化
  - `vertices` が非空なら、`y_top` を段階的に下げて `facet` を再生成（2 段階）。
  - それでも `facet` が 0 の場合は、最終手段として **頂点集合（TopBandVerts）をそのまま境界条件用 region として使用**（警告ログを出して継続）。
- 帯域式の明確化
  - 左右は `x0 ± D/2` に `± tol` バッファを付与し、`>=`, `<=` の非厳密比較を使用。
- 診断ログの拡充
  - `region_attempts.csv` に `y_top` を追加
  - ログに `y_top` と `TopBandVerts x-range` を出力

### 推奨の実行手順（検証フロー）
1) まずドライランで領域だけ確認（解析は回さない）
```
python G:\RPi-Development\20251108SIM\Calc2_robust.py \
  --dry-run --log-level DEBUG \
  --diag-dir G:\\RPi-Development\\20251108SIM\\diag
```
ログの `TopBand facets`, `TopBandVerts nodes`, `TopBandVerts x-range` を確認してください。

2) それでも頂点が空/少数の場合は引数で強化
- 例：
```
--tol-factor 0.5 --safety-growth 1.10 --max-attempts 6 --nx 120 --ny 40
```

3) 本解析の実行
```
python G:\RPi-Development\20251108SIM\Calc2_robust.py --log-level INFO
```

### 典型的な失敗要因と対処
- tol がメッシュ解像度に対して小さすぎる → `--tol-factor` を増やす
- D が頂点にかからない（端が格子間に落ちる）→ `--safety-growth` と再試行で帯域を拡大
- facet が 0 → Robust-3 では自動で `y_top` を順次下げ、最終的に頂点ベースで境界条件を適用

以上の修正により、`TopBand/TopBandVerts` が空になるケースを大幅に低減でき、例外による停止を避けられます。