# プロジェクト現状整理

作成日: 2026-03-27

## 1. 全体像

現在の `D:\OBS\REC` は、次のものが同居しているワークスペースです。

1. 現在使っている Windows ショート生成ライン
2. 現在使っている投稿後メンテナンスライン
3. 古い Linux / VM 共有キュー型ライン
4. 古い Windows ブリッジ UI
5. 次世代候補の Windows ライン
6. 学習データ・モデル・ログ・バックアップ
7. チャット / スーパーチャット返信に関する構想や残骸

一番重要な原則は次です。

- まず実行可能性を守る
- 次に役割を分ける
- 物理移動は最後にする

## 2. current

### 2.1 current ショート生成ライン

対象:

- `scripts\youtube\yolo\WIN`

位置づけ:

- いまの実運用上の Windows 本線
- 実際の入口は `ui\app.py`
- 運用感としては `UPLOAD_RUNBOOK.md` と UI を中心に回っている

主な構成:

- `UPLOAD_RUNBOOK.md`
- `launch_ui.ps1`
- `ui\app.py`
- `scripts\build_candidates_win.py`
- `scripts\pick_global_candidates_win.py`
- `scripts\run_event_queue_pipeline_yolo_win.py`
- `scripts\upload_from_queue_win.py`
- `scripts\manage_youtube_videos_win.py`
- `config.json`
- `.env.win`
- `data\*.jsonl`

流れ:

1. `build_candidates_win.py`
   - `base_dir` 配下のセッションを走査
   - `raw_yolo.jsonl` を読み
   - `candidates_20s.jsonl` を作る
2. `pick_global_candidates_win.py`
   - 候補を選ぶ
   - `picked_at` と `pick_id` を書く
   - `event_queue_yolo_win.jsonl` へ積む
3. `run_event_queue_pipeline_yolo_win.py`
   - cropped JPEG を作る
   - review 用画像を作る
   - `api\v1\decision.json` を生成または利用する
   - BGM 付きショートを render する
   - `upload_queue_yolo_win.jsonl` へ積む
4. `upload_from_queue_win.py`
   - YouTube へ upload
   - playlist 追加
   - `.published` を作る

壊してはいけないもの:

- `config.json`
- `.env.win`
- `data` 配下の queue 名と役割
- `event_name=00000_00020` 形式
- `api\v1\decision.json`
- `.published`
- `assets\logo\masao_logo_overlay.png`
- UI が前提にしている起動方法

現在の弱点:

- 絶対パスが多い
- `E:\masaos_mov` 前提が強い
- working directory に依存する箇所がある
- token / prompt / API path の一部が固定
- `launch_ui.ps1` がローカル `config.json` を上書きしうる

### 2.2 current 投稿後メンテナンスライン

対象:

- `work`

位置づけ:

- 動画生成ラインではない
- 既存の YouTube 動画を後から整える運用バッチ

主な構成:

- `UPDATE_SHORTS_RUNBOOK.md`
- `update_shorts.py`
- `UNLISTED_VIDEOS_2026-03-23.md`
- `output.txt`
- `execution_log.txt`
- `get_playlists.py`
- `test_status.py`
- `test_calc.py`

流れ:

1. 直近アップロード動画を確認
2. private で説明欄未設定などの対象を絞る
3. 除外 ID を外す
4. タイトル接頭辞を付ける
5. 説明欄テンプレートを入れる
6. 公開予約を割り当てる
7. 再生リストへ追加する

壊してはいけないもの:

- `keys\youtube\token.json`
- 除外ファイル
- playlist ID
- スケジュール定数
- 現行 runbook の実行コマンド

重要な見方:

- これはショート生成本線ではなく、post-publish ライン
- current ショート生成ラインとは別に扱う方がよい

## 3. next

### 3.1 次世代 Windows 本線候補

対象:

- `scripts\WIN_YOLO_PTZ_20S`

位置づけ:

- 次の canonical Windows line 候補
- current より line-local に閉じる方向で設計されている

特徴:

- 自前の `assets`
- 自前の `data`
- 自前の `prompts`
- 自前の `scripts`
- 自前の `ui`
- config 基準の相対パス解決
- line-local queue
- line-local artifact
- shared Linux core から離れる設計

重要性:

- Windows ネイティブに整理していくなら一番筋がよい

まだ current にしていない理由:

- 現在の実運用は `scripts\youtube\yolo\WIN` 側
- まだ完全移行していない
- uploader 側に絶対パスが残る
- runbook と運用習慣がまだ current 側にある

## 4. legacy

### 4.1 Linux / VM 共有キュー型旧ライン

対象:

- `jobs`
- `scripts\active`
- `scripts\core`
- Linux 寄りの `scripts\youtube`

位置づけ:

- 古い共有キュー型の本線
- shared posting queue と shared event artifact で回る
- 後続ラインの元になった重要な旧基盤

代表的な流れ:

1. `jobs\run_360_cron.sh`
2. `jobs\run_analyze_cron.sh`
3. `scripts\active\analyze_y2_events.py`
4. `scripts\active\enqueue_daily_YA.py`
5. `scripts\youtube\run_event_queue_pipeline.py`
6. `scripts\core\api_decision_pipeline.py`
7. `scripts\active\upload_from_queue.py` または `scripts\youtube\upload_from_queue.py`

役割:

- 旧共通基盤
- データ契約や処理の系譜を理解する上では重要
- ただし Windows 本線整理の主対象にはしない方がよい

### 4.2 古い Windows ブリッジ

対象:

- `WIN`

位置づけ:

- `WIN\YoloShortsManager.py` は古い橋渡し UI
- Windows 完結ではない
- Windows で候補選別し、Linux 側 YOLO ラインへ流し込む前段

役割:

- legacy bridge
- 履歴としては重要
- 長期的な本線には向かない

## 5. チャット / スーパーチャット返信の現状

現状:

- そのまま使える現行ソース群は見つかっていない
- 残っているのは主に構想メモ、バックアップ、実装残骸

確認できたもの:

1. docs 内の構想メモ
2. `tmp\__pycache__\write_30s_chatbot_v4.cpython-314.pyc`
3. `_backup_n8n\2025-12-12_224102\n8n_data.tgz`
4. 投稿説明文やテロップにあるライブ視聴・コメント関連文言

見方:

- current ショート本線には含めない
- 将来復活するなら独立した bot プロジェクトとして分ける

推奨分類:

- `bots`
- `bots\chat_responder`

## 6. support / research / archive

### 6.1 support

- `keys`
- `prompts`
- `bgm`
- `posting`
- `logs`

### 6.2 research / training

- `models`
- `_masao_yolo`
- `yolo_train`
- `yolo_runs`
- `weak_angle_pick_20260210plus`
- `weak_angle_pick_20260210plus_v2`
- `weak_angle_pick_20260210plus_v2_combined`

見方:

- 実行入口ではない
- 学習・研究・素材資産
- 運用本線とは視覚的に分けたい

### 6.3 archive / leftovers

- `_backup_n8n`
- `_backup_scripts`
- `trash`
- `tmp`

見方:

- 退避物・一時物・掃除候補を明示する領域
- live production と同列に見せない方がよい

## 7. 現在の分類案

現時点では次のラベルで見るのが最もわかりやすいです。

### 7.1 current

- `scripts\youtube\yolo\WIN`
- `work`

### 7.2 next

- `scripts\WIN_YOLO_PTZ_20S`

### 7.3 legacy

- `WIN`
- `jobs`
- `scripts\active`
- `scripts\core`
- 古い Linux 寄り `scripts\youtube`

### 7.4 support

- `keys`
- `prompts`
- `bgm`
- `posting`
- `logs`

### 7.5 research

- モデル・学習関連ディレクトリ

### 7.6 archive

- `_backup_*`
- `trash`
- `tmp` の残骸

## 8. 整理ルール

整理は次のルールで進めるのが安全です。

1. `scripts\youtube\yolo\WIN\UPLOAD_RUNBOOK.md` を壊さない
2. `work\UPDATE_SHORTS_RUNBOOK.md` を壊さない
3. current を先に物理移動しない
4. 絶対パスを先に設定化する
5. queue 契約と artifact 契約を保ったまま整備する
6. next が current と同等に回るまでは昇格させない
7. チャットボット系はショート生成と分ける

## 9. 整理の進め方

### Phase 0

まず分類を明文化する。

- current
- next
- legacy
- support
- research
- archive

### Phase 1

人が使う入口を減らす。

例:

- current ショート用起動ラッパ
- post-publish 用起動ラッパ

### Phase 2

current を動かしたまま安全化する。

対象:

- `E:\masaos_mov`
- token path
- prompt path
- bgm path
- logo path
- cwd 依存 path

### Phase 3

必要なら shared utility を抜き出す。

候補:

- config loader
- queue helper
- schedule helper
- YouTube auth helper

### Phase 4

`scripts\WIN_YOLO_PTZ_20S` が current を置き換えられるか検証する。

必要条件:

- candidate build
- pick
- review
- metadata generation
- render
- upload

### Phase 5

置き換えが確認できてから legacy を畳む。

対象候補:

- `WIN`
- Linux 旧共有ライン
- 古い研究残骸

## 10. 実務上の結論

このプロジェクトは、単一の巨大コードベースとしてではなく、次のライン群として整理するべきです。

1. current Windows ショート生成
2. current 投稿後メンテナンス
3. next Windows canonical line
4. legacy Linux 共有ライン
5. legacy Windows bridge
6. chat bot backlog / remnants
7. support assets
8. research / archive

この見方で整理すれば、いま必要な実行性を守りながら、無理なく全体をきれいにできます。
