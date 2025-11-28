# SfePy 解析スクリプト（Calc2.py）の地域（region）指定修正について

本ドキュメントは、`pyparsing.exceptions.ParseException: Expected end of text, found '0' (at char 15)` に対する根本原因と修正内容、SfePy の region 構文の要点、実行方法をまとめたものです。

## 発生していた例外と原因
- 例外: `pyparsing.exceptions.ParseException: Expected end of text, found '0' (at char 15)`
- 発生箇所（概念）: `domain.create_region('PinNode', f'vertices by id {pin_ids}')` のような文字列生成系
- 原因の本質:
  - SfePy の region セレクタは独自パーサで、`vertices by id 1,2,3` のような厳格な書式を要求します。
  - 先行コードでは面（facet）境界の作法と混同し、頂点集合（vertex set）に対して `facet` 指定や ID 指定の文字列整形を混在させたため、わずかなスペースや余分文字でパースが破綻しました。
  - 解析モデルは 2D 平面ひずみ（2 成分 DOF）で正しいものの、`PinNode` は頂点集合である必要がある一方、境界条件に使う他の領域では面（facet）が必要です。ここが混同されるとパーサのエラーに繋がります。

## 採用した解決方針（堅牢化）
1. 頂点集合は **座標式で指定** し、`facet` を付けない
   - 例: `vertices in ((x <= min_x+eps) & (y <= min_y+eps))`
   - ID 指定（`vertices by id ...`）は整形ミスで壊れやすいため避けました。
2. 同一の幾何位置に対して、用途別に region を使い分け
   - パンチ上面の **境界条件用** には面領域（`facet`）を維持: `TopBand`
   - 反力・DOF 抽出用に **頂点集合** を別途作成: `TopBandVerts`
3. DOF/反力抽出は頂点番号から直接インデクス
   - 2D ベクトル DOF のため `dof_y = 2*node + 1`（y 成分）で反力を集計

## 具体的なコード変更点（Calc2.py）
- 変更ファイル: `G:\RPi-Development\20251108SIM\Calc2.py`
- 主な修正:
  - `PinNode` を座標式の **頂点集合** で再定義（`facet` 指定なし）
  - `TopBand`（facet）はそのまま境界条件で使用、加えて **頂点集合 `TopBandVerts`** を新規追加
  - 反力計算・中心変位の抽出に `TopBandVerts.entities`（頂点番号）を使用
  - 変位ベクトル `vec` と残差 `r` を用いて、`Fy`（総反力）を `-r[dof_y]` の総和として算出
  - 変数名の誤り `coors_all` → `coors` を修正

### パッチ相当の抜粋
```python
# Top central band for punch (on top edge)
x0 = 0.5 * (min_x + max_x)
top_band = domain.create_region(
    'TopBand',
    f'vertices in ((y > {max_y - eps}) & (x > {x0 - D/2 - eps}) & (x < {x0 + D/2 + eps}))',
    'facet'
)
# Vertex set corresponding to the same top band (for DOF/reaction extraction)
top_band_verts = domain.create_region(
    'TopBandVerts',
    f'vertices in ((y > {max_y - eps}) & (x > {x0 - D/2 - eps}) & (x < {x0 + D/2 + eps}))'
)

# Robust pin node selection by coordinate region (vertex set, no 'facet')
pin_region = domain.create_region(
    'PinNode',
    f'vertices in ((x <= {min_x + eps}) & (y <= {min_y + eps}))'
)

# ... 省略 ...

# Sum Y-direction reactions at top band DOFs (use vertex region)
band_nodes = np.array(top_band_verts.entities, dtype=int).copy()
Fy = 0.0
for n in band_nodes:
    dof_y = 2*n + 1
    Fy += -r[dof_y]  # reaction = -residual

# Track tip displacement at center of band (use vertex coordinates)
band_coors = coors[band_nodes]
center_node = int(band_nodes[np.argmin((band_coors[:, 0] - x0)**2)])
uy_node = vec[2*center_node + 1]
```

## SfePy の region 構文メモ
- `all` 全領域
- `vertices in (<論理式>)` 頂点集合（点集合）。境界条件で **点拘束** したいときや DOF 抽出時に便利
- `... , 'facet'` を第 3 引数に付けると **面領域**（境界の辺/面）として解釈
- 典型的な座標式:
  - `x < a`, `x > b`, `y <= c`
  - 論理積/和: `(&)`, `(|)`
  - 括弧を丁寧に付けること
- ID 直接指定:
  - `vertices by id 1, 2, 3`（厳密な書式が必要。余計なカンマ・空白・括弧に注意）

## 実行方法
1. 依存パッケージ（例）
   - `sfepy`, `numpy`, `pandas`
2. 実行
   - `python G:\RPi-Development\20251108SIM\Calc2.py`
3. 出力
   - `result_elastic_press.csv`（カラム: `step, uy_cmd, uy_center, Fy_N`）
   - 標準出力に DataFrame の末尾（`df.tail()`）が表示されます

## 確認ポイント
- パンチ上面（TopBand）に `u.1 = -uy` の境界条件が正しく適用される
- `PinNode` に `u.0 = 0` が適用され、剛体回転が抑制される
- `Fy_N` がステップに応じて増減し、`uy_center` と整合的

## よくあるハマりどころ
- `facet` と **頂点集合** の混同
- `vertices by id` の文字列整形ミス
- 2D ベクトル DOF のオフセット（`2*n + 0/1`）の取り違え
- タプル/配列の dtype が float のままでインデクスに使って例外（→ `astype(int)` / `np.array(..., dtype=int)`）

## 変更履歴
- 2025-11-08: region 指定の堅牢化、反力・中心変位の抽出ロジックを vertex ベースに統一、ドキュメント追加。
