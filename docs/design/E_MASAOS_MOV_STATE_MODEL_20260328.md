# E_MASAOS_MOV_STATE_MODEL_20260328

## 結論

`E:\masaos_mov` は単なる動画倉庫ではない。

これは

- session 単位の作業箱
- file-based state board
- Explorer で在庫と進捗が読める運用面

を兼ねた中核フォルダである。

Windows 再構築では、この見え方を引き継ぐべき。

## 1. session 命名

トップレベルは session 単位で、

- `YYYY-MM-DD_HH-MM-SS`

命名になっている。

例:

- `E:\masaos_mov\2026-03-27_18-02-08`
- `E:\masaos_mov\2025-12-19_18-21-46`

この時点で

- いつの録画か
- どの単位で処理するか

がすぐ分かる。

## 2. session 直下の基本物

新しい session 例:

- `raw.mkv`
- `proxy_360.mp4`
- `raw_yolo.jsonl`
- `yolo_full.log`
- `.ready_for_move`
- `.yolo_done`

古い 360 / ΔY 系 session 例:

- `raw.mkv`
- `proxy_360.mp4`
- `logs`
- `frames_360`
- `events`

つまり session 直下を見るだけで、

- 素材があるか
- 360 proxy があるか
- YOLO が終わったか
- analyze 済みか
- events まで展開済みか

が分かる。

## 3. Explorer で読める state

確認できた主な marker / state file は次の通り。

### session レベル

- `.ready_for_move`
  - session が倉庫側へ移される準備完了の印
- `.yolo_done`
  - raw に対する YOLO 抽出完了
- `logs\.analyze_done`
  - ΔY / frames 抽出完了

### event / yolo レベル

- `events\<EVENT>\yolo\v1\.yolo_done`
  - YOLO 判定完了
- `events\<EVENT>\yolo\v1\.crop_done`
  - crop 生成完了
- `events\<EVENT>\yolo\v1\api2\v1\.api2_done`
  - API2 metadata 完了
- `events\<EVENT>\yolo\v1\.yolo_reject`
  - YOLO 判定で却下
- `events\<EVENT>\yolo\v1\.yolo_published`
  - yolo ライン側 publish 完了の印

### api / publish レベル

- `events\<EVENT>\api\vN\decision.json`
  - metadata / decision 結果
- `events\<EVENT>\api\vN\.published`
  - publish 済み

### render / failure レベル

- `events\<EVENT>\shorts\.render_fail_1`
  - render 失敗 1 回目
- `events\<EVENT>\shorts\.render_fail_logo`
  - logo 付与段階の失敗痕跡
- `events\<EVENT>\shorts\.render_skip`
  - 再試行停止

## 4. session の人間可読な進捗構造

古い 360 / ΔY 系では、

- `logs`
  - `showinfo_fps1.log`
  - `meanY_sec.csv`
  - `deltaY_sec.csv`
  - `hits_4sec.txt`
  - `segments_15s.txt`
  - `events_merged.txt`
  - `events_no_oped.txt`
  - `frames_extract.nohup.log`
  - `.analyze_done`
- `frames_360\<EVENT>`
  - 1fps frame 群
- `events\<EVENT>`
  - `api`
  - `shorts`
  - 必要に応じて `yolo`

となっており、処理の各段が人間にも見える。

## 4.5 360 在庫の読み方

運用上の在庫判定は非常に単純で、

- `frames_360\<EVENT>` が在庫
- 同名の `events\<EVENT>` ができたら、その在庫は消化済み

と読む。

つまり、

- 未投稿在庫:
  - `frames_360\<EVENT>` はある
  - `events\<EVENT>` はまだない
- 消化済み在庫:
  - `frames_360\<EVENT>` と同名の `events\<EVENT>` がある

この意味で、

- `frames_360` は在庫棚
- `events` は在庫を実処理ラインへ移した痕跡

として機能している。

補足:

- 厳密な YouTube 投稿済み判定は `api\vN\.published`
- ただし 360 在庫管理の目線では「同名 event フォルダができたか」が一次判定

この判定は実装にも表れており、`enqueue_daily_YA.py` は `frames_360` を見て pool を作り、同名 `events\<EVENT>` が既にあれば除外する。

## 5. 前段の cron / analyze chain

このラインの前段として重要なのは次の 2 段。

### 1. `D:\OBS\REC\jobs\run_analyze_cron.sh`

役割:

- `E:` に対応する Linux 側 root から、まだ `logs/.analyze_done` がない session を探す
- `proxy_360.mp4` が存在し、かつ増加中でないことを確認する
- `analyze_y2_events.py` を実行する
- 終了後に `logs/.analyze_done` を立てる

つまりこれは

- session 発見
- 成長中ファイル回避
- 1 回だけ analyze 実行

を担う cron 入口。

### 2. `D:\OBS\REC\scripts\active\enqueue_daily_YA.py`

役割:

- `frames_360` と `logs/.analyze_done` を持つ session を対象に pool を作る
- まだ同名 `events\<EVENT>` が存在しないものだけを未消化在庫として扱う
- `event_queue.jsonl` に `session_dir / event_name / frames_dir / event_dir / publishAt / route` を積む

つまり cron の次段で、

- analyze 済みの frame イベントを queue 化する

役割を持つ。

## 6. 実務上の理解

したがって、

- 前段入口は `run_analyze_cron.sh`
- queue 化は `enqueue_daily_YA.py`

の 2 つで見るのが正しい。

`run_analyze_cron.sh` だけでライン全体ではなく、
その次に `enqueue_daily_YA.py` が続いて初めて downstream へ渡る。

## 7. Windows 再構築で引き継ぐべきもの

### 必ず引き継ぐ

- session 命名規則
- session 直下を見れば素材状態が分かること
- empty file / small file による state 表現
- event 単位の独立フォルダ
- `.published` や `.analyze_done` のような人間可読 marker
- Explorer だけでも在庫が読めること

### スクリプト側で読むべきもの

- `raw.mkv`
- `proxy_360.mp4`
- `raw_yolo.jsonl`
- `logs\.analyze_done`
- `.yolo_done`
- `.ready_for_move`
- `events\<EVENT>\api\vN\decision.json`
- `events\<EVENT>\api\vN\.published`
- failure marker 群

## 8. 設計判断

Windows 化では、

- 「フォルダと marker で進捗が見える」

こと自体を仕様とみなすべき。

これは単なる偶然の副産物ではなく、運用上の強い価値である。

したがって Windows 正規ラインでも、

- script 内部だけで完結する hidden state

より、

- Explorer で一目で分かる file-based state

を優先する。
