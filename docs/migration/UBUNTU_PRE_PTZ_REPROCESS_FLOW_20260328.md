# Ubuntu Pre-PTZ Reprocess Flow

作成日: 2026-03-28

## 1. この文書の位置づけ

この文書は、
自動追尾導入前の資産を再活用するときに使う
Ubuntu 旧ラインの処理構造を整理したものです。

これは「日次の正規本線」ではありません。
しかし、
旧資産を再処理するときの再利用ラインとして意味があります。

## 2. 一言で言うと

このラインは次の流れです。

`proxy_360.mp4`
-> `ΔY で動き区間抽出`
-> `event_queue へ投入`
-> `API1 で crop/start/end`
-> `API2 で title/description`
-> `render`
-> 必要なら upload queue へ

## 3. 実ファイルでの流れ

### Step 1: 360化済み動画から ΔY 解析

主スクリプト:

- `D:\OBS\REC\scripts\active\analyze_y2_events.py`

入力:

- `<session>\proxy_360.mp4`

やっていること:

- showinfo から fps=1 の meanY を取る
- `deltaY` を計算する
- 動きのある秒を hit として検出する
- segment 化 / merge / gap / OP/ED 除外を行う
- `frames_360\<EVENT>\*.jpg` を切り出す

出力:

- `<session>\frames_360\<EVENT>\`
- `logs\showinfo_fps1.log`
- `logs\meanY_deltaY.csv`
- `logs\.analyze_done`

### Step 2: 在庫から event_queue へ投入

主スクリプト:

- `D:\OBS\REC\scripts\active\enqueue_daily_YA.py`

やっていること:

- `frames_360` の在庫を見て
- `event_queue.jsonl` に投入する

役割:

- `frames_360` 在庫と event 処理をつなぐ橋渡し

### Step 3: API1 / API2 を通して decision を作る

主スクリプト:

- `D:\OBS\REC\scripts\core\api_decision_pipeline.py`

やっていること:

- 入力は `frames_360/<EVENT>/` の静止画群
- API1:
  - `crop_x`
  - `start_sec`
  - `end_sec`
  を返す
- ローカルで 9〜15秒の数値チェックを行う
- API2:
  - `title`
  - `description`
  を返す

出力:

- `<EVENT_DIR>\api\vN\request.json`
- `<EVENT_DIR>\api\vN\response.json`
- `<EVENT_DIR>\api\vN\decision.json`

## 4. bridge と render

主スクリプト:

- `D:\OBS\REC\scripts\youtube\run_event_queue_pipeline.py`

役割:

- `event_queue.jsonl` を読む
- 必要なら `api_decision_pipeline.py` を呼ぶ
- render を行う
- upload 用 queue へ橋渡しする

つまり、
旧ラインでは `api_decision_pipeline.py` 単体だけではなく、
`run_event_queue_pipeline.py` が event queue と render をまとめる bridge の役目です。

## 5. upload は条件付き

主スクリプト:

- `D:\OBS\REC\scripts\youtube\upload_from_queue.py`

位置づけ:

- 旧資産の再処理で「生成まで」が目的なら必須ではない
- 旧資産からそのまま投稿まで行くなら必要

したがって、
upload は常時本線ではないが、
再活用の目的次第で保持価値があります。

## 6. いまの判断

このラインは次のように整理するのがよいです。

- 日次本線:
  - 使わない
- 旧資産の再処理ライン:
  - 保持する
- GitHub 公開の主役:
  - しない
- legacy としての参照価値:
  - 高い

## 7. 実務上の結論

Ubuntu 旧ラインは、
「もう不要な昔のライン」ではなく、
「自動追尾導入前資産を再利用するときの再処理ライン」
として扱うべきです。

## 8. 次にやること

1. `legacy\linux_shared` にこの系統を参照用コピーする
2. `run_event_queue_pipeline.py` を `daily production retired / historical reprocess usable` と明記する
3. current 本線と混同しないよう runbook を分ける
