# REC 全体調査メモ

調査日: 2026-03-27

## 1. いま見えている全体像

このワークスペースは、少なくとも次の 5 系統が同居している。

1. Ubuntu 上で回していた旧自動化ライン
2. Windows 上で切り抜き生成を回すための旧 WIN ライン
3. Windows 上で独立運用するための新ライン `WIN_YOLO_PTZ_20S`
4. YOLO 学習データ作成・学習成果物
5. YouTube 公開後のメンテナンス用スクリプト

ルート `D:\OBS\REC` 自体は Git 管理ではないが、`scripts\` 配下だけが別 Git リポジトリになっている。

## 2. 現行の主な実行ライン

### 2.1 Ubuntu 旧ライン

`scripts\README_RUNPATHS.txt` に書かれている「正の実行パス」は次の流れ。

1. `jobs\run_360_cron.sh`
2. `scripts\active\analyze_y2_events.py`
3. `scripts\active\enqueue_daily_YA.py`
4. `scripts\youtube\run_event_queue_pipeline.py`
5. `scripts\youtube\upload_from_queue.py`
6. `scripts\core\api_decision_pipeline.py`
7. `scripts\core\render_short_from_decision.py`

役割は次の通り。

- `jobs\run_360_cron.sh`
  - `/media/sf_OBS_TEMP` から `raw.mkv` を拾う
  - `proxy_360.mp4` を作る
  - `.ready_for_move` を置く
- `jobs\run_analyze_cron.sh`
  - `/media/sf_masaos_mov` 以下から未解析セッションを 1 本拾う
  - `scripts\active\analyze_y2_events.py` を動かす
- `scripts\active\analyze_y2_events.py`
  - `proxy_360.mp4` から `showinfo_fps1.log` を作る
  - `meanY_sec.csv`, `deltaY_sec.csv`, `events_no_oped.txt` などを出す
  - `frames_360\<EVENT>\*.jpg` を切り出す
  - `logs\.analyze_done` を置く
- `scripts\active\enqueue_daily_YA.py`
  - 解析済みセッションから未処理イベントを選び
  - `posting\event_queue.jsonl` に投入する
- `scripts\youtube\run_event_queue_pipeline.py`
  - `event_queue.jsonl` を消費する
  - `api_decision_pipeline.py` を呼ぶ
  - `raw.mkv` から縦動画を作り
  - `posting\queue.jsonl` に upload 用行を積む
- `scripts\youtube\upload_from_queue.py`
  - YouTube API で投稿し
  - `api\vN\.published` を作る

### 2.2 Windows 旧 WIN ライン

`WIN\YoloShortsManager.py` は古い Windows ブリッジ UI。

- `E:\masaos_mov` を前提に候補を読む
- キューは `D:\OBS\REC\posting\event_queue_yolo.jsonl`
- 書き込む際に Windows パスを `/media/sf_masaos_mov` / `/media/sf_REC` へ変換する

つまり「操作は Windows、実処理は Linux/VM 側に寄せる」橋渡し設計になっている。

### 2.3 Windows 独立ライン その1

`scripts\youtube\yolo\WIN\` は Windows 専用パイプラインの作業場。

流れ:

1. `scripts\build_candidates_win.py`
2. `scripts\pick_global_candidates_win.py`
3. `scripts\run_event_queue_pipeline_yolo_win.py`
4. `scripts\upload_from_queue_win.py`
5. `ui\app.py`

特徴:

- `config.json` あり
- キューを `scripts\youtube\yolo\WIN\data\` 配下に分離
- `raw_yolo.jsonl` から中央値 `crop_x` を計算
- JPEG レビューを挟める

ただし絶対パスが多く、`D:\OBS\REC` と `E:\masaos_mov` に強く依存している。

### 2.4 Windows 独立ライン その2

`scripts\WIN_YOLO_PTZ_20S\` は新しい canonical line。

設計意図:

- 20 秒クリップ固定
- line-local な assets / data / prompts / scripts / ui
- `config.json` 基準の相対パス解決
- 旧キューと共有しない

実装状態:

- `common_line.py` で設定相対パス化が入っている
- `run_event_queue_pipeline_win_yolo_ptz_20s.py` で生成フローはある
- `generate_metadata_win_yolo_ptz_20s.py` で OpenAI API を直接 `curl` 叩き
- `upload_from_queue_win_yolo_ptz_20s.py` だけは `D:\OBS\REC\keys\youtube\token.json` をまだ固定で参照
- `ui\README.md` では「まだ legacy WIN queue files に依存しない UI へ移行中」とされている

## 3. 現在のフォルダ分類

### 3.1 本線候補

- `scripts\`
- `jobs\`
- `posting\`
- `prompts\`
- `keys\`
- `bgm\`
- `logs\`

### 3.2 Windows 運用試行・移行中

- `WIN\`
- `scripts\youtube\yolo\WIN\`
- `scripts\WIN_YOLO_PTZ_20S\`
- `work\`

### 3.3 学習・モデル系

- `models\`
- `_masao_yolo\`
- `yolo_train\`
- `yolo_runs\`
- `weak_angle_pick_20260210plus*`

### 3.4 退避・保管

- `trash\`
- `_backup_n8n\`
- `_backup_scripts\`
- `jobs\archive\`
- `jobs\_archive_unused_2025-12-19\`
- `scripts\archive\`
- `scripts\_archive_unused_*`

## 4. 目立つ依存関係と絡み

### 4.1 セッション単位の基本データ

旧ラインでも新ラインでも、セッション配下には次のような素材が前提になっている。

- `raw.mkv`
- `proxy_360.mp4`
- `raw_yolo.jsonl`
- `frames_360\<EVENT>\*.jpg`
- `events\<EVENT>\api\vN\decision.json`

### 4.2 キュー

ルート `posting\` は旧ラインの共通キュー置き場。

- `event_queue.jsonl`
- `queue.jsonl`
- `event_queue_yolo.jsonl`
- `queue_yolo.jsonl`
- `yolo_event_queue.jsonl`
- `yolo_queue.jsonl`

現時点ではこれらは空。

一方、新しい Windows ラインは `scripts\youtube\yolo\WIN\data\` や `scripts\WIN_YOLO_PTZ_20S\data\` のローカルキューを使う方針。

### 4.3 API と認証

- OpenAI キー:
  - Linux 旧運用は `keys\openai\env.sh`
  - Windows 新運用は `.env.win` を読む設計
- YouTube 認証:
  - `keys\youtube\token.json`
  - `keys\youtube\client_secret.json`

### 4.4 依存パッケージ

コードから見えた主な依存:

- `googleapiclient`
- `google_auth_oauthlib`
- `PIL`
- `cv2`
- `ultralytics`
- `tkinter`

この環境では次を確認した。

- `python --version` -> `3.14.3`
- `ffmpeg -version` -> `8.0.1`
- `googleapiclient`, `google_auth_oauthlib`, `PIL`, `cv2`, `ultralytics`, `tkinter` は import 可
- `openai` パッケージは import 不可
- ただし現在の API 実装は `curl` を使っているので、`openai` パッケージ未導入でも主線は動かせる可能性がある
- `python -m pip` は使えず、`pip` モジュールが見つからない

## 5. Windows 化の観点での注意点

### 5.1 まだ Linux 前提が濃い箇所

- `/media/sf_REC`
- `/media/sf_masaos_mov`
- `/media/sf_OBS_TEMP`
- `/usr/share/fonts/...`
- `/tmp/...`
- `bash`, `flock`, `find`, `stat`, `head`
- `python3` 固定

これらは主に `jobs\*.sh`, `scripts\active\*`, `scripts\youtube\*`, `scripts\core\*` に残っている。

### 5.2 まだ Windows でも絶対パス依存が残る箇所

- `D:\OBS\REC\...`
- `E:\masaos_mov`
- `C:\Windows\Fonts\meiryo.ttc`

とくに `scripts\youtube\yolo\WIN\` は config があっても絶対パス前提が強い。

### 5.3 移行先として比較的筋が良い箇所

`scripts\WIN_YOLO_PTZ_20S\` は次の点で整理しやすい。

- line-local の構成がはっきりしている
- `common_line.py` で相対パス解決を持っている
- runbook で「旧 shared flow を置き換える」と明言している

## 6. 絡みが複雑になっているポイント

### 6.1 同じ役割のものが複数ある

- UI:
  - `WIN\YoloShortsManager.py`
  - `scripts\youtube\yolo\WIN\ui\app.py`
  - `scripts\WIN_YOLO_PTZ_20S\ui\app.py`
- render/pipeline:
  - `scripts\youtube\run_event_queue_pipeline.py`
  - `scripts\youtube\yolo\run_event_queue_pipeline_yolo.py`
  - `scripts\youtube\yolo\WIN\scripts\run_event_queue_pipeline_yolo_win.py`
  - `scripts\WIN_YOLO_PTZ_20S\scripts\run_event_queue_pipeline_win_yolo_ptz_20s.py`
- uploader:
  - `scripts\active\upload_from_queue.py`
  - `scripts\youtube\upload_from_queue.py`
  - `scripts\youtube\yolo\upload_from_queue_yolo.py`
  - `scripts\youtube\yolo\WIN\scripts\upload_from_queue_win.py`
  - `scripts\WIN_YOLO_PTZ_20S\scripts\upload_from_queue_win_yolo_ptz_20s.py`

### 6.2 Git 境界が中途半端

- ルートは Git ではない
- `scripts\` だけ Git リポジトリ
- しかし `jobs\`, `WIN\`, `work\`, `docs\`, `models\` はその外にある

このため、「どこまでが変更対象か」が見えにくい。

### 6.3 エンコードの混在

複数ファイルで UTF-8 と Windows 側既定コードページの混在が見える。
PowerShell 既定読みでは文字化けするが、`-Encoding utf8` 指定で正常に読める文書もある。

## 7. 今回見つかった具体的な注意点

1. `scripts\active\run_analyze_cron.sh` は `SCRIPT="/media/sf_REC/scripts/analyze_y2_events.py"` を指しており、`active\analyze_y2_events.py` ではない
2. `jobs\run_analyze_cron.sh` の方は `scripts/active/analyze_y2_events.py` を指している
3. `scripts\WIN_YOLO_PTZ_20S\scripts\upload_from_queue_win_yolo_ptz_20s.py` はまだ YouTube token の絶対パス固定
4. `WIN\YoloShortsManager.py` は VM パス変換を前提にしており、純 Windows 完結ではない
5. `work\update_shorts.py` 系は投稿後メンテナンスであり、主生成ラインとは別扱いにした方がよい

## 8. フォルダ整理の第一候補

整理を進めるなら、まずは次の 4 区分に分けるのがよい。

1. 実運用コード
   - `scripts\`
   - `jobs\`
   - `posting\`
   - `prompts\`
   - `keys\`
   - `bgm\`
2. Windows 新本線
   - `scripts\WIN_YOLO_PTZ_20S\`
3. 旧ライン・移行元
   - `WIN\`
   - `scripts\youtube\yolo\WIN\`
   - Linux 前提の `jobs\*.sh`, `scripts\active\*`, `scripts\youtube\*`
4. 学習成果物・素材
   - `models\`
   - `_masao_yolo\`
   - `yolo_train\`
   - `yolo_runs\`
   - `weak_angle_pick_*`
   - `trash\`

## 9. 次の作業順の提案

1. `scripts\WIN_YOLO_PTZ_20S\` を Windows の唯一の本線候補として確定する
2. そのラインで絶対パスを全部設定化する
3. `keys\youtube\token.json` 参照も config 化する
4. 旧 `WIN\` と `scripts\youtube\yolo\WIN\` を「legacy」扱いで明示する
5. ルート直下の素材・学習成果物・退避物を別階層へ寄せる
6. 可能ならルートごと Git 管理するか、少なくとも管理境界を文書化する

## 10. いまの結論

「Ubuntu で動いていた旧ライン」と「Windows へ寄せる途中の複数ライン」が同居しているのが現在の混線の主因。

Windows 完結の整理先としては、`scripts\WIN_YOLO_PTZ_20S\` を軸に寄せていくのが最も自然。
そのうえで、旧 Linux 依存ラインと学習成果物を実運用ラインから分離すると、全体がかなり見やすくなる。
