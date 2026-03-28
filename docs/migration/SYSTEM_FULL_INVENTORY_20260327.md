# 全体システム棚卸し

作成日: 2026-03-27

## 1. 対象

今回の棚卸し対象は次の 5 箇所です。

- `D:\OBS\REC`
- `D:\MD`
- `Z:\`
- `C:\masao_ptz`
- `E:\masaos_mov`

この文書は「何がどこにあり、何を担っていて、再構築時にどう扱うべきか」を確認するための全体台帳です。
再構築の設計方針そのものは `REBUILD_MASTER_PLAN_20260327.md` を正本とします。

## 2. 全体要約

現在の全体像は、単一プロジェクトではなく、次の 5 系統の集合です。

1. ショート生成 current ライン
2. 投稿後整備 current ライン
3. Linux / VM 由来の legacy ライン
4. PTZ runtime ライン
5. chat bot runtime ライン

これらの上に、

- 文書・年表・設計知識
- 学習・研究・モデル
- 大容量セッション倉庫
- バックアップ / 廃棄候補

が重なっています。

## 3. 規模感

2026-03-27 時点の概数:

- `D:\OBS\REC`
  - 約 1,727 files
  - 約 4.74 GB
- `D:\MD`
  - 約 4,229 files
  - 約 2.78 GB
- `Z:\`
  - 約 3,423 files
  - 約 0.08 GB
- `C:\masao_ptz`
  - 約 66 files
  - 約 0.06 GB
- `E:\masaos_mov`
  - 約 47,501 files
  - 約 5.8 TB
  - 約 203 sessions

補足:

- 容量の大半は `E:\masaos_mov` と `D:\OBS\REC\trash` に偏っています。
- `D:\MD` は文書量が多いものの、コード本体ではありません。
- `Z:\` と `C:\masao_ptz` は容量は小さいですが、役割上は本線です。

## 4. ドライブごとの役割

### 4.1 `C:\`

役割:

- 高速実行
- SSD を生かす短命処理
- 応答速度重視 runtime

主要実体:

- `C:\masao_ptz`

扱い:

- 残す
- 無理に `D:` へ吸収しない
- 将来的には `C:\masao_runtime` のような runtime 専用構造に寄せる

### 4.2 `D:\`

役割:

- 主作業領域
- 常設コード
- 日常運用
- 文書の入口

主要実体:

- `D:\OBS\REC`
- `D:\MD`

扱い:

- 司令塔
- 再構築の中心
- current / next / legacy / shared / docs / research / archive の論理分割を置く

### 4.3 `E:\`

役割:

- 倉庫
- セッション保管
- 素材と成果物の蓄積

主要実体:

- `E:\masaos_mov`

扱い:

- 共有倉庫として継続利用
- 大量コピーを避ける
- 将来は session 内部を論理分類する

### 4.4 `Z:\`

役割:

- ネットワークフォルダ
- 別マシン runtime の共有面

主要実体:

- `Z:\chatbot_v4`
- `Z:\chatbot_v3`
- `Z:\keys`

扱い:

- chat 専用本線
- shorts 系とは分離維持

## 5. `D:\OBS\REC` 棚卸し

### 5.1 current

#### `scripts\youtube\yolo\WIN`

役割:

- 現行のショート生成本線

入口:

- `UPLOAD_RUNBOOK.md`
- `launch_ui.ps1`
- `ui\app.py`

主処理:

- 候補生成
- pick
- review
- metadata 生成
- render
- upload

注意:

- `config.json` 依存が強い
- `E:\masaos_mov` 前提が強い
- 絶対パスが一部残る
- queue と artifact の互換性を壊さないことが重要

#### `work`

役割:

- 投稿後整備の current 本線

入口:

- `UPDATE_SHORTS_RUNBOOK.md`
- `update_shorts.py`

注意:

- ショート生成とは別ライン
- token や playlist 設定の依存が強い
- one-off 的なログや作業メモが混ざる

### 5.2 next

#### `scripts\WIN_YOLO_PTZ_20S`

役割:

- 次世代 Windows 本線候補

特徴:

- line-local な `assets` `data` `prompts` `scripts` `ui` を持つ
- current より自己完結に近い
- canonical Windows line の候補として最有力

扱い:

- すぐ切替しない
- current と同等に回せるまで育成

### 5.3 legacy

#### `jobs`
#### `scripts\active`
#### `scripts\core`
#### Linux 寄り `scripts\youtube`

役割:

- Linux / VM 時代の共有キュー型本線

特徴:

- `360 -> ΔY -> queue -> render/upload` の旧ライン
- パスずれや Linux 前提が残る
- 参照価値は高いが current としては扱わない

#### `WIN`

役割:

- 旧 Windows ブリッジ

特徴:

- `YoloShortsManager.py` が旧 UI
- VM / 共有フォルダ前提の橋渡し用途

扱い:

- legacy 固定

### 5.4 support

対象:

- `keys`
- `prompts`
- `bgm`
- `models`
- `posting`
- `docs`

扱い:

- 再構築先へコピー候補
- ただし正本を 1 箇所に決める

### 5.5 research

対象:

- `_masao_yolo`
- `yolo_train`
- `yolo_runs`
- `weak_angle_pick_*`
- ルート直下の学習 / データセット用 `.py`

扱い:

- 運用本線と切り離す
- `research` 領域へ寄せる

### 5.6 archive / cleanup 候補

対象:

- `trash`
- `_backup_n8n`
- `_backup_scripts`
- `tmp`
- 古い `.log` `.csv`
- 単発メモ

扱い:

- まず archive
- すぐ削除しない

### 5.7 特記事項

- `D:\OBS\REC` ルートは Git 管理ではなく、`scripts` 配下だけが別 Git です。
- `scripts` の中に current / next / legacy が混在しているため、ここが最大の分離対象です。
- `trash` が大きく、現状把握を見えにくくしています。

## 6. `D:\MD` 棚卸し

### 6.1 `masao`

役割:

- 長期知識ベース候補

重要文書例:

- `masao_chatbot.md`
- `masao_ptz_v4_spec_20260307.md`
- `yolo_youtube_360_dy_relation.md`
- `chat_timeline_summary.md`
- `TIPS.md`

扱い:

- 文書正本候補

### 6.2 `pc_back`

役割:

- 再構築監査パック
- 移行時の背景説明

重要文書例:

- `MASAO_WINDOWS_REBUILD_ACTION_GUIDELINE_FINAL_2026-02-28.md`
- `PIPELINE_TIMELINE_CANONICAL_AUDIT.md`
- `WIN_360YOLO_MIGRATION_PROMPT_PACK.md`
- `OLD360_360YOLO_script_map.md`
- `masao_D_OBS_REC_analysis.md`

扱い:

- 凍結監査資料として残す

### 6.3 `GPT`

役割:

- raw 会話アーカイブ

扱い:

- 情報源ではあるが、日常の正本にはしない

### 6.4 `Archive_PDFs`

役割:

- PDF アーカイブ

扱い:

- 保管

## 7. `Z:\` 棚卸し

### 7.1 `chatbot_v4`

役割:

- 現行 chat bot 本線

大まかな流れ:

1. `read_A_40s` / `read_B_40s` がチャット取得
2. `decide_30s.py` がトリガー判定
3. `data\outbox.jsonl` を生成
4. `write_30s.py` が返信送信

関連:

- `Z:\keys\...`
- `prompts\taro_system.txt`
- `OPENAI_API_KEY`
- 補助クライアント `C:\masao\chatbot_client`

扱い:

- `REC` へ吸収しない
- chat 専用 runtime として独立維持

### 7.2 `chatbot_v3` / `chatbot` / `archive`

役割:

- 旧系

扱い:

- 参照用

## 8. `C:\masao_ptz` 棚卸し

### 8.1 current

入口:

- `start_masao_v5_with_tocc.bat`
- `prod\track_masao_ptz_v5_ui.py`

役割:

- カメラ入力
- YOLO 検出
- OSC 送受信
- PTZ 追尾
- 仮想カメラ出力

関連:

- `integrations\obsbot_center_tocc_bridge.py`
- モデル `masao_V06.pt`

扱い:

- hot runtime
- `D:` へ寄せない

### 8.2 `prototype` / `archive` / `diagnostics`

扱い:

- current から分けて保持

## 9. `E:\masaos_mov` 棚卸し

### 9.1 性格

`E:\masaos_mov` は単なる RAW 倉庫ではありません。
セッション単位で、素材から解析結果、イベント、投稿成果物まで保持しています。

### 9.2 確認できた要素

- `raw.mkv`
- `proxy_360.mp4`
- `.ready_for_move`
- `frames_360`
- `events`
- `api\v1\decision.json`
- `yolo\v1\decision.json`
- `shorts\*.mp4`
- `.published`

### 9.3 扱い

- shared warehouse のまま維持
- 新基準フォルダへ大量コピーしない
- セッション命名や artifact 互換性を壊さない

## 10. 再構築時の分類

### 10.1 current

- `D:\OBS\REC\scripts\youtube\yolo\WIN`
- `D:\OBS\REC\work`

### 10.2 next

- `D:\OBS\REC\scripts\WIN_YOLO_PTZ_20S`

### 10.3 legacy

- `D:\OBS\REC\jobs`
- `D:\OBS\REC\scripts\active`
- `D:\OBS\REC\scripts\core`
- Linux 寄り `scripts\youtube`
- `D:\OBS\REC\WIN`
- `Z:\chatbot_v3`

### 10.4 support

- `keys`
- `prompts`
- `bgm`
- `models`
- `docs`

### 10.5 research

- `yolo_train`
- `yolo_runs`
- `weak_angle_pick_*`
- dataset / training scripts

### 10.6 archive

- `trash`
- `_backup_*`
- old logs
- old queue backups
- old chatbot variants

## 11. 再構築上の重要判断

1. `C:` を SSD 用 hot runtime として残すのは合理的です。
2. `D:` は管理と運用の司令塔にします。
3. `E:` は倉庫として共有のまま使います。
4. `Z:` は別マシン runtime なので shorts 系と混ぜません。
5. 文書の正本は `D:\MD\masao` を軸にします。
6. `D:\OBS\REC` は機能別よりも `current / next / legacy / support / research / archive` で切る方が安全です。
7. いきなり移動せず、新基準フォルダへコピーして検証後に archive 化する方針が適しています。

## 12. 次にやるべきこと

1. `REBUILD_MASTER_PLAN_20260327.md` を正本設計として固定する
2. 新しい基準フォルダ名を確定する
3. `shared` に入れるものと `E:` 共有のままにするものを確定する
4. current の入口をラッパ化する
5. 新基準側で current 複製を動作確認する
6. 安定後に legacy と archive を整理する
