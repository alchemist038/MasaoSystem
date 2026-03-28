# YOUTUBE_YOLO_DEEP_READ_20260328

## 対象

- `D:\OBS\REC\scripts\youtube\yolo`
- `D:\OBS\REC\scripts\youtube\yolo\WIN\scripts`

## 結論

`D:\OBS\REC\scripts\youtube\yolo` は、`raw_yolo.jsonl` を使って

1. 候補 20 秒区間を作る
2. 候補から pick する
3. `event_queue_yolo.jsonl` に積む
4. crop 済み画像を作る
5. API2 で title / description を作る
6. shorts を render する
7. `queue_yolo.jsonl` に積む
8. YouTube upload する

という 1 本のラインとして整理されている。

そのうえで、現在の Windows 正規ラインはこの思想を引き継ぎつつ、

- Linux 固定パスを config 化
- session 単位 pick を global pick に拡張
- crop 決定を API1 ではなく local YOLO 中心値で置き換え
- review gate を追加

したものになっている。

## 旧 `scripts\youtube\yolo` の役割

### 1. `build_candidates_20s.py`

役割:

- `raw_yolo.jsonl` から 20 秒候補を作る
- 候補は `candidates_20s.jsonl` に保存する

中身:

- `sec` 単位の YOLO ログを読み込む
- valid detection 条件:
  - `conf >= 0.40`
  - bbox 幅 `50 <= w <= 210`
  - 全画面寄り bbox は reject
- 先頭 5 分 / 末尾 5 分を除外
- 20 秒窓を `start += 20` の non-overlap で走査
- `hits >= 15` の窓だけ残す
- motion は `p90(cx) - p10(cx)`

意味:

- ここで「動きのある 20 秒候補」を file-based に固定している
- 後段はこの候補ファイルを正として扱う

参考:

- `build_candidates_20s.py:21`
- `build_candidates_20s.py:25`
- `build_candidates_20s.py:27`
- `build_candidates_20s.py:29`
- `build_candidates_20s.py:48`
- `build_candidates_20s.py:145`
- `build_candidates_20s.py:152`

### 2. `pick_from_candidates.py`

役割:

- 1 session 内の `candidates_20s.jsonl` から pick する
- pick 結果を同じ `candidates_20s.jsonl` に `picked_at` と `pick_id` で刻む
- 必要なら `event_queue_yolo.jsonl` へ enqueue する

中身:

- motion 帯ごとの range 指定を受ける
- default は
  - `0-10` から 2 本
  - `10-20` から 3 本
  - `30+` から 3 本
- 既存 `picked_at` を持つ行は除外
- `--skip-uploaded` で `video_id` 付きも除外可能
- overlap しない窓を優先
- 不足時は `.warn_no_motion_*` を作る
- `--enqueue` 時は `event_queue_yolo.jsonl` に
  - `session_dir`
  - `event_name`
  - `frames_dir`
  - `event_dir`
  - `publishAt`
  - `route`
  を積む

意味:

- 旧ラインでは pick は session 内ローカル処理
- queue に積む前に候補ファイル自体へ state を刻む設計

参考:

- `pick_from_candidates.py:30`
- `pick_from_candidates.py:95`
- `pick_from_candidates.py:103`
- `pick_from_candidates.py:106`
- `pick_from_candidates.py:116`
- `pick_from_candidates.py:166`
- `pick_from_candidates.py:218`
- `pick_from_candidates.py:228`
- `pick_from_candidates.py:245`

### 3. `run_event_queue_pipeline_yolo_v2.py`

役割:

- 旧 yolo ラインの実質的な self-contained bridge
- `event_queue_yolo.jsonl` を読み、preview export -> API2 -> render -> upload queue 追記まで行う

中身:

- `raw_yolo.jsonl` の指定区間から `cx` の中央値を出す
- `calculate_crop_x()` で 360p 上の crop 位置を決める
- `raw.mkv` から crop 済み preview JPEG を 1fps で書き出す
- API は `api_decision_pipeline.py --step 2` のみ呼ぶ
- `decision.json` は `api/v1/decision.json` を前提
- render 後に `queue_yolo.jsonl` へ
  - `video_path`
  - `decision_path`
  - `published_flag_path`
  - `publishAt`
  - `route`
  を追記する

重要:

- ここでは API1 に crop を決めさせていない
- crop はすでに local YOLO の `median cx` で決まっている
- API2 は title / description 決定に限定されている

参考:

- `run_event_queue_pipeline_yolo_v2.py:7`
- `run_event_queue_pipeline_yolo_v2.py:51`
- `run_event_queue_pipeline_yolo_v2.py:69`
- `run_event_queue_pipeline_yolo_v2.py:77`
- `run_event_queue_pipeline_yolo_v2.py:95`
- `run_event_queue_pipeline_yolo_v2.py:101`
- `run_event_queue_pipeline_yolo_v2.py:185`
- `run_event_queue_pipeline_yolo_v2.py:196`
- `run_event_queue_pipeline_yolo_v2.py:204`
- `run_event_queue_pipeline_yolo_v2.py:218`

### 4. `upload_from_queue_yolo.py`

役割:

- `queue_yolo.jsonl` を YouTube upload へ流す

中身:

- `decision.json` の `title` / `description` を使う
- timeline 文を session path と event name から組み立てる
- fixed block と hashtags を後ろに足す
- upload 成功後は `.published` を作る
- queue は先頭から dequeue する

意味:

- upload 後 state は DB ではなく `.published`
- queue も JSONL 1 本で運ぶ

参考:

- `upload_from_queue_yolo.py:21`
- `upload_from_queue_yolo.py:22`
- `upload_from_queue_yolo.py:86`
- `upload_from_queue_yolo.py:110`
- `upload_from_queue_yolo.py:125`
- `upload_from_queue_yolo.py:177`
- `upload_from_queue_yolo.py:201`
- `upload_from_queue_yolo.py:247`
- `upload_from_queue_yolo.py:299`
- `upload_from_queue_yolo.py:311`

### 5. `run_event_queue_pipeline_yolo.py`

位置づけ:

- `run_event_queue_pipeline_yolo_v2.py` とは別に残っている bridge 版
- ただし、現ファイルは helper を自前定義しておらず self-contained ではない

観察:

- `run_api_if_needed`
- `already_enqueued`
- `render_with_retry`
- `append_upload_queue`

を呼んでいるが、同ファイル内には定義がない

補足:

- これらの helper は `D:\OBS\REC\scripts\youtube\run_event_queue_pipeline.py` には存在する
- そのため、この yolo 版は「途中の移植物」または「未完成の派生版」と見るのが自然

判断:

- 構造理解の参考にはなる
- ただし、現在の canonical source としては `run_event_queue_pipeline_yolo_v2.py` の方が信頼できる

参考:

- `run_event_queue_pipeline_yolo.py:121`
- `run_event_queue_pipeline_yolo.py:123`
- `run_event_queue_pipeline_yolo.py:183`
- `run_event_queue_pipeline_yolo.py:202`
- `run_event_queue_pipeline_yolo.py:207`
- `run_event_queue_pipeline_yolo.py:228`
- `D:\OBS\REC\scripts\youtube\run_event_queue_pipeline.py:145`
- `D:\OBS\REC\scripts\youtube\run_event_queue_pipeline.py:156`
- `D:\OBS\REC\scripts\youtube\run_event_queue_pipeline.py:261`

## Windows 版でどう変わったか

### 1. `WIN\scripts\build_candidates_win.py`

これは旧 `build_candidates_20s.py` のほぼ直系移植。

引き継いだもの:

- `20 sec`
- `stride 20`
- `hits >= 15`
- `motion = p90(cx) - p10(cx)`
- head/tail 5 分 cut
- bbox reject 条件

変わったもの:

- config 読み込み化
- `base_dir` / `raw_yolo_name` / `candidates_name` を差し替え可能

参考:

- `build_candidates_win.py:12`
- `build_candidates_win.py:15`
- `build_candidates_win.py:17`
- `build_candidates_win.py:18`
- `build_candidates_win.py:106`
- `build_candidates_win.py:147`
- `build_candidates_win.py:156`

### 2. `WIN\scripts\pick_global_candidates_win.py`

ここが旧ラインからの大きな変化。

変化:

- session 単位 pick -> 全 session 横断 pick
- `max_per_session` を導入
- mode を
  - `random`
  - `motion`
  - `band`
  - `hybrid`
  へ拡張
- `pick_reason` を残す

意味:

- 旧ラインは「1 session をどう捌くか」
- Windows 版は「複数 session をどう全体最適で捌くか」

参考:

- `pick_global_candidates_win.py:46`
- `pick_global_candidates_win.py:66`
- `pick_global_candidates_win.py:79`
- `pick_global_candidates_win.py:117`
- `pick_global_candidates_win.py:127`
- `pick_global_candidates_win.py:166`
- `pick_global_candidates_win.py:212`
- `pick_global_candidates_win.py:230`
- `pick_global_candidates_win.py:317`

### 3. `WIN\scripts\run_event_queue_pipeline_yolo_win.py`

これは `run_event_queue_pipeline_yolo_v2.py` の Windows 正規化版と見てよい。

引き継いだもの:

- `raw_yolo.jsonl` から `median cx`
- local crop 決定
- crop 済み JPEG export
- API2 step2
- render
- upload queue
- `.published`

追加されたもの:

- config 化
- env file 取り込み
- logo overlay
- review gate
- defer / reject queue
- retry items を queue に戻す制御

重要:

- ここでも crop 決定は API1 ではなく local YOLO
- API は title / description 用の API2 が中心

参考:

- `run_event_queue_pipeline_yolo_win.py:50`
- `run_event_queue_pipeline_yolo_win.py:76`
- `run_event_queue_pipeline_yolo_win.py:82`
- `run_event_queue_pipeline_yolo_win.py:119`
- `run_event_queue_pipeline_yolo_win.py:190`
- `run_event_queue_pipeline_yolo_win.py:201`
- `run_event_queue_pipeline_yolo_win.py:263`
- `run_event_queue_pipeline_yolo_win.py:375`
- `run_event_queue_pipeline_yolo_win.py:456`
- `run_event_queue_pipeline_yolo_win.py:515`

### 4. `WIN\scripts\upload_from_queue_win.py`

引き継いだもの:

- queue -> upload
- description 組み立て
- `.published`

改善:

- config 化
- description block を柔軟化
- `publishAt` を UTC RFC3339 へ正規化
- queue を JSONL としてまとめて書き戻す

参考:

- `upload_from_queue_win.py:21`
- `upload_from_queue_win.py:22`
- `upload_from_queue_win.py:78`
- `upload_from_queue_win.py:99`
- `upload_from_queue_win.py:121`
- `upload_from_queue_win.py:151`
- `upload_from_queue_win.py:192`
- `upload_from_queue_win.py:222`
- `upload_from_queue_win.py:289`
- `upload_from_queue_win.py:305`

## 継承された思想

- DB ではなく file-based state
- queue は JSONL
- session ごとに素材と event を閉じ込める
- candidate -> pick -> event_queue -> upload_queue の段階分離
- `.published` を最終 state にする
- 再実行しても同じ state file を見れば追跡できる

## 置き換わった部分

### Ubuntu / 旧系で残るもの

- `raw_yolo.jsonl` から候補を作る思想
- `candidates_20s.jsonl`
- `event_queue` / `queue`
- `.published`

### Windows 正規ラインで置き換わったもの

- Linux 固定パス -> config / common_win
- session 内 pick -> global pick
- API1 crop 判定 -> local YOLO 中央値 crop
- 単純 bridge -> review / defer / reject を含む運用ライン

## この deep read からの判断

1. `scripts\youtube\yolo` は Windows 正規ラインの直接の祖先として重要
2. 特に `build_candidates_20s.py` と `run_event_queue_pipeline_yolo_v2.py` は思想の核
3. `run_event_queue_pipeline_yolo.py` は参照価値はあるが、現ファイル単体では信頼度が低い
4. 正規 Windows 化の本質は「API1 を捨てて local YOLO crop に寄せたこと」
5. したがって今後の再構築では
   - candidate generation
   - global pick
   - local YOLO crop
   - API2 metadata
   - upload queue
   を canonical chain として整理するのが自然
