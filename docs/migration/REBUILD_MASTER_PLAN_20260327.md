# 再構築マスタープラン

作成日: 2026-03-27

## 1. この文書の目的

この文書は、現在点在している

- `D:\OBS\REC`
- `D:\MD`
- `Z:\`
- `C:\masao_ptz`
- `E:\masaos_mov`

を 1 つの全体システムとして把握し、今後無理なく再構築できるようにするための設計書です。

2026-03-28 以降は、
`GITHUB_PUBLIC_RELEASE_GOAL_20260328.md` を最上位目標とし、
この文書はその公開目標を支えるローカル再構築計画として扱います。

今回の方針は単なるフォルダ整理ではなく、

- どこが実行系か
- どこが倉庫か
- どこが知識ベースか
- どこが高速処理層か
- どこが別マシン runtime か

を明確に分けたうえで、壊さず移行できる構造を作ることです。

## 2. 現在のドライブ別役割

### 2.1 `C:\`

役割:

- 高速実行・高速作業用 SSD

今回把握できた実体:

- `C:\masao_ptz`

意味:

- PTZ 制御は応答性が重要
- 360 化が済むまで SSD 上で処理したいという意図がある
- そのため、速度が必要な runtime を `C:` に置いたのは合理的

### 2.2 `D:\`

役割:

- 主作業領域
- 常設コード
- 運用スクリプト
- 文書
- 支援資産

今回把握できた実体:

- `D:\OBS\REC`
- `D:\MD`

意味:

- 実装と知識の中心は `D:` に寄せる方針だった
- 実際にも、動画本線・後処理・文書・設計メモは `D:` に多く集まっている

### 2.3 `E:\`

役割:

- 倉庫
- セッション格納
- 素材と成果物の蓄積先

今回把握できた実体:

- `E:\masaos_mov`

意味:

- 単なる RAW 置き場ではない
- セッション単位の `raw.mkv`、`proxy_360.mp4`、`frames_360`、`events`、`api`、`shorts` が積み上がる巨大倉庫
- 2026-03-27 時点で約 203 セッション、約 5.8TB

### 2.4 `Z:\`

役割:

- ネットワークフォルダ
- 別マシンで動いている runtime の共有面

今回把握できた実体:

- `Z:\chatbot_v4`
- `Z:\chatbot_v3`
- `Z:\keys`

意味:

- 現行 chat bot は `Z:` 側が本線
- `REC` 本体とは別の runtime として扱うべき

## 3. 現在のシステム全体

全体は次の 5 ラインから成っています。

### 3.1 ショート生成 current ライン

場所:

- `D:\OBS\REC\scripts\youtube\yolo\WIN`

入口:

- `UPLOAD_RUNBOOK.md`
- `launch_ui.ps1`
- `ui\app.py`

役割:

- Windows 上で候補作成
- ピック
- review
- metadata 生成
- render
- upload

### 3.2 投稿後整備 current ライン

場所:

- `D:\OBS\REC\work`

入口:

- `UPDATE_SHORTS_RUNBOOK.md`
- `update_shorts.py`

役割:

- 既に上がっている動画のタイトル・説明欄・公開予約・再生リスト整理

### 3.3 Linux / VM legacy ライン

場所:

- `D:\OBS\REC\jobs`
- `D:\OBS\REC\scripts\active`
- `D:\OBS\REC\scripts\core`
- Linux 寄り `scripts\youtube`

役割:

- `360 -> ΔY -> queue -> render/upload`
  の古い共有キュー型本線

### 3.4 PTZ 制御ライン

場所:

- `C:\masao_ptz`

入口:

- `start_masao_v5_with_tocc.bat`
- `prod\track_masao_ptz_v5_ui.py`

役割:

- カメラ入力
- YOLO 検出
- OSC 送信
- PTZ 追尾
- 仮想カメラ出力

### 3.5 Chat bot ライン

場所:

- `Z:\chatbot_v4`

役割:

- YouTube Live Chat 取得
- トリガー判定
- outbox 作成
- YouTube Live Chat 返信送信
- 補助的に `C:\masao\chatbot_client` 側で読み上げ連携

## 4. 文書系の現状

### 4.1 `D:\MD` の位置づけ

`D:\MD` は実装置き場ではなく、知識ベースとアーカイブの集約先です。

### 4.2 正本候補

- 文書の長期正本候補:
  - `D:\MD\masao`
- 再構築監査パック:
  - `D:\MD\pc_back`
- raw 原資料:
  - `D:\MD\GPT`
  - `D:\MD\Archive_PDFs`
  - `D:\MD\ChatGPT_LifeLog_Archive.md`

### 4.3 文書として重要なもの

- `masao_chatbot.md`
- `masao_ptz_v4_spec_20260307.md`
- `yolo_youtube_360_dy_relation.md`
- `chat_timeline_summary.md`
- `pc_back` 配下の再構築ガイド群

## 5. 現在の問題

### 5.1 問題は「散らばっている」だけではない

実際の問題は、次の 4 つが混ざっていることです。

1. 実行系
2. 文書系
3. 倉庫
4. 研究・履歴・バックアップ

### 5.2 `D:\OBS\REC` の中に混在が強い

特に混在が大きいのは:

- `scripts`
- ルート直下の単発 `.py`
- 学習物と運用物の同居
- `trash` や `_backup_*` の残存

### 5.3 `E:\masaos_mov` が単純な RAW 倉庫ではない

ここには

- 素材
- 解析結果
- イベント
- metadata
- shorts
- `.published`

まで積まれており、すでに「データレイク + 成果物倉庫」の性格を持っています。

### 5.4 `Z:\` と `C:\masao_ptz` は `REC` とは別の本線

- `Z:\chatbot_v4` は chat runtime 本線
- `C:\masao_ptz` は PTZ runtime 本線

この 2 つを無理に `REC` の中へ吸収するのはよくありません。

## 6. 再構築の基本思想

再構築では、フォルダを「機能」だけでなく「層」で分けます。

### 6.1 Hot layer

高速実行が必要な層

場所:

- `C:\`

対象:

- PTZ 制御
- 360 化前後の高速 scratch
- 反応速度が重要な runtime

### 6.2 Control layer

日常運用の中心となる制御面

場所:

- `D:\`

対象:

- current ショート生成
- post-publish
- runbook
- 設定
- 共通資産
- docs 入口

### 6.3 Knowledge layer

文書・設計・年表・再構築知識

場所:

- `D:\MD`

対象:

- `masao`
- `pc_back`
- 必要最小限の整理済み MD

### 6.4 Data warehouse layer

巨大素材とセッション成果物

場所:

- `E:\masaos_mov`

対象:

- セッション一式
- 解析済みイベント
- shorts 成果物

### 6.5 Remote runtime layer

別マシン本線

場所:

- `Z:\`

対象:

- `chatbot_v4`
- その認証
- その prompt

## 7. 再構築後のあるべき見え方

### 7.1 `D:` は「司令塔」にする

`D:` の新しい基準フォルダは、次のような形がよいです。

```text
D:\MasaoSystem
  current
    shorts_win
    post_publish
  next
    shorts_ptz_win
  legacy
    linux_shared
    old_win_bridge
  shared
    keys
    prompts
    bgm
    models
    schemas
    libs
  docs
    current
    design
    migration
  research
    yolo_training
    dataset_build
    experiments
  archive
    backups
    trash
    old_logs
```

### 7.2 `E:` は引き続き倉庫

`E:\masaos_mov` はそのまま shared warehouse として残す方がよいです。

ただし将来的には、セッション内の役割を明確にします。

例:

```text
E:\masaos_mov\<session>\
  source
    raw.mkv
  proxy
    proxy_360.mp4
  analysis
    logs
    frames_360
  publish
    events
  lineage
    markers (.ready_for_move / .analyze_done / .published)
```

今すぐ物理移動はせず、まずはこの論理モデルを定義するだけで十分です。

### 7.3 `C:` は runtime 特化

```text
C:\masao_runtime
  ptz
  scratch_360
  temp_render
```

意味:

- 長時間常駐する高速 runtime
- 一時処理
- SSD 前提の短命データ

### 7.4 `Z:` は chat 専用

```text
Z:\chatbot_v4
Z:\keys
```

をそのまま保ち、

- chat runtime
- chat token
- chat prompt

は shorts 本線と共有しない方がよいです。

## 8. shared に残すべきもの

shared に残すべきものは最小限でよいです。

### 8.1 shared で持つべきもの

- `keys`
- `prompts`
- `bgm`
- `models`
- path/config 抽象化
- queue schema
- event artifact schema
- time/schedule utility
- YouTube auth helper
- OpenAI helper

### 8.2 shared にしない方がよいもの

- `Z:\chatbot_v4` の read/decide/write 本体
- `C:\masao_ptz` の tracker/UI 本体
- `E:` 上の line-local 生成ロジック
- legacy の古い queue 運用

## 9. current / next / legacy の確定

### 9.1 current

- `D:\OBS\REC\scripts\youtube\yolo\WIN`
- `D:\OBS\REC\work`

### 9.2 next

- `D:\OBS\REC\scripts\WIN_YOLO_PTZ_20S`

### 9.3 legacy

- `D:\OBS\REC\jobs`
- `D:\OBS\REC\scripts\active`
- `D:\OBS\REC\scripts\core`
- Linux 寄り `scripts\youtube`
- `D:\OBS\REC\WIN`

### 9.4 support

- `keys`
- `prompts`
- `bgm`
- `models`
- `docs`

### 9.5 research

- `yolo_train`
- `yolo_runs`
- `weak_angle_pick_*`
- `scripts\experimental`
- ルート直下の単発学習用スクリプト

### 9.6 archive

- `trash`
- `_backup_*`
- old logs
- old queue backups

## 10. 実際の移行順

### Phase 0

現状を固定する。

- current を確定
- next を確定
- legacy を確定
- drive の役割を確定

### Phase 1

新しい基準フォルダを `D:` に作る。

- まだ current は動かし続ける
- まずはコピーで構造だけ作る

### Phase 2

`shared` をコピーする。

対象:

- `keys`
- `bgm`
- `prompts`
- `models`
- runbook
- docs

ただし `E:\masaos_mov` は共有のまま使う。

### Phase 3

current 本線を新基準側へ複製し、設定を整理する。

重要:

- queue を新系専用にする
- `config` に path を寄せる
- working directory 依存を減らす

### Phase 4

post-publish を分離して新基準側へ整える。

### Phase 5

`next` を current と同等に回せるか検証する。

### Phase 6

旧散在ラインを archive 化する。

### Phase 7

十分に安定したら不要分だけ削減する。

## 11. 今回の結論

今回の再構築で重要なのは、
単に `D:\OBS\REC` を整理することではありません。

本当にやるべきことは、

- `C:` を hot runtime
- `D:` を control plane
- `D:\MD` を knowledge base
- `E:` を warehouse
- `Z:` を remote runtime

として再定義し、

そのうえで

- current
- next
- legacy
- support
- research
- archive

を切り分けることです。

この構造にすれば、今の「散らばっている」状態は、
単なる混乱ではなく、役割ごとに意味のある配置へ再編できます。
