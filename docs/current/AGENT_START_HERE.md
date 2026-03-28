# Agent Start Here

更新日: 2026-03-28

## 1. この文書の役割

次回このワークスペースで作業を始める人やエージェントが、
最短で全体像をつかみ、危険な誤整理を避けながら再構築を進めるための開始点です。

この文書は要約版です。
詳細は下の正本文書を参照します。

## 2. 最初に読む順番

1. `D:\OBS\REC\GITHUB_PUBLIC_RELEASE_GOAL_20260328.md`
2. `D:\OBS\REC\REBUILD_MASTER_PLAN_20260327.md`
3. `D:\OBS\REC\CODEX_WORKING_RULES.md`
4. `D:\OBS\REC\SYSTEM_FULL_INVENTORY_20260327.md`
5. `D:\OBS\REC\SESSION_LOG.md`
6. `D:\OBS\REC\PROJECT_SUMMARY_20260327.md`
7. `D:\OBS\REC\PROJECT_STATUS_20260327.md`
8. `D:\OBS\REC\scripts\youtube\yolo\WIN\UPLOAD_RUNBOOK.md`
9. `D:\OBS\REC\work\UPDATE_SHORTS_RUNBOOK.md`

必要に応じて読む文書:

- `D:\MD\masao\yolo_youtube_360_dy_relation.md`
- `D:\MD\masao\masao_ptz_v4_spec_20260307.md`
- `D:\MD\masao\masao_chatbot.md`
- `D:\MD\pc_back\MASAO_WINDOWS_REBUILD_ACTION_GUIDELINE_FINAL_2026-02-28.md`

## 3. このシステムの正しい見方

これは 1 本のコードツリーではありません。
次の層に分けて理解します。

- `C:` = hot runtime
- `D:` = control plane
- `D:\MD` = knowledge base
- `E:` = warehouse
- `Z:` = remote runtime

## 3.5 最上位の公開目標

今後の最上位目標は、
GitHub 公開を前提に、
低スペック環境でも動く自動処理パイプラインの構成と思想を公開できる形へ整理することです。

そのため、以後の整理は

- README 主役
- 設計重視
- 実運用構造の抽出
- 機密の除外
- 公開用最小構成

を優先します。

## 4. 現在の本線

### current

- `D:\OBS\REC\scripts\youtube\yolo\WIN`
- `D:\OBS\REC\work`

### next

- `D:\OBS\REC\scripts\WIN_YOLO_PTZ_20S`

### legacy

- `D:\OBS\REC\jobs`
- `D:\OBS\REC\scripts\active`
- `D:\OBS\REC\scripts\core`
- Linux 寄り `D:\OBS\REC\scripts\youtube`
- `D:\OBS\REC\WIN`

### separate runtime

- PTZ: `C:\masao_ptz`
- chat bot: `Z:\chatbot_v4`

### warehouse

- `E:\masaos_mov`

## 5. 重要な前提

- `C:` に点在しているのは偶然ではない
- PTZ 制御は応答性のため SSD 側に置く意図がある
- 360 化まわりも SSD 上で処理したい意図がある
- それ以外はできるだけ `D:` に寄せる方針だった
- `E:\masaos_mov` は単なる RAW 置き場ではなく、巨大なセッション倉庫
- `Z:\chatbot_v4` は別マシン runtime の本線

## 6. 壊してはいけないもの

- current の入口
  - `D:\OBS\REC\scripts\youtube\yolo\WIN\UPLOAD_RUNBOOK.md`
  - `D:\OBS\REC\work\UPDATE_SHORTS_RUNBOOK.md`
- `E:\masaos_mov` の session 構造
- queue 名と artifact の互換性
- `.published`
- event 名の形
- token / key の参照先
- `C:\masao_ptz` と `Z:\chatbot_v4` の独立性

## 7. やってはいけないこと

- いきなり current を移動する
- いきなり legacy を削除する
- `C:\masao_ptz` を shorts 本線の下へ吸収する
- `Z:\chatbot_v4` を `REC` の一部として混ぜる
- `E:\masaos_mov` を新基準フォルダへ丸ごとコピーする
- current と next の queue を混在させる

## 8. 次に安全に始める作業

1. GitHub 公開版の README 目次を先に作る
2. 公開対象と除外対象を決める
3. GitHub 公開版の別ディレクトリを作る
4. 公開版の最小フォルダ構成を定義する
5. sample data / mock config の方針を決める
6. その後に必要な current の複製を行う
7. 新基準側だけで動作確認する
8. 安定後に legacy を archive 化する

## 9. 新しい基準構造

```text
D:\MasaoSystem
  current
    daily_ops_win
      shorts_win
      post_publish
    historical_reprocess_win
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

## 10. 迷ったときの判断基準

- 速度が重要で常駐するか
  - なら `C:` 寄り
- 日常運用の制御か
  - なら `D:` 寄り
- 文書か
  - なら `D:\MD`
- 大容量セッションデータか
  - なら `E:\masaos_mov`
- 別マシン runtime か
  - なら `Z:`

## 11. 次回作業の最初のゴール

最初のゴールは「ローカル整理そのもの」ではなく、
GitHub 公開版の README 骨子と最小構成を先に定義することです。

その後に、必要なローカル複製や移行作業へ入ります。
