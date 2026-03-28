# Codex Working Rules

更新日: 2026-03-28

## 1. 目的

この文書は、このワークスペースで Codex や次回の作業者が
どの順番で考え、何を先にやり、何をしてはいけないかを固定するための運用ルールです。

## 1.5 最上位優先目標

最上位の目標は、
GitHub 公開を前提に、
低スペック環境でも動く自動処理パイプラインの構成と思想を公開できる形へ整理することです。

以後の判断では、通常のローカル整理よりも次を優先します。

- README を主役にする
- 設計を主役にする
- 実運用の state / queue / immutable 設計を見せる
- 機密を除外する
- 公開用の最小構成に落とす

## 2. 今回の進め方は正しいか

結論:

- はい、今回ユーザーが指示した進め方でよい

今回採用した流れは、現状のように

- 実行系
- 文書系
- 倉庫
- 別マシン runtime
- 研究 / legacy / backup

が混在している環境では、安全で合理的です。

## 3. 今回の正しい進行順

この環境では、次の順番を基本ルールとします。

1. まず全体を探索して把握する
2. current / next / legacy / support / research / archive を切り分ける
3. ドライブごとの役割を明確にする
4. 文書に落として正本を作る
5. いきなり移動せず、新しい基準フォルダへコピーして整理する
6. 新基準側で動作確認する
7. 問題がなければ旧散在ラインを archive 化する
8. 安定後に不要分だけ削減する

## 4. この順番がよい理由

- current を壊しにくい
- 役割の違うものを無理に 1 箇所へ押し込まない
- `C:` `D:` `E:` `Z:` の意味を保てる
- 旧ラインを参照しながら安全に移行できる
- 文書が先に整うので、次回以降の判断が速い

## 5. Codex の初動ルール

新しいセッションで作業を始めたら、まず次を行う。

1. `AGENT_START_HERE.md` を読む
2. `GITHUB_PUBLIC_RELEASE_GOAL_20260328.md` を読む
3. `SESSION_LOG.md` を読む
4. `REBUILD_MASTER_PLAN_20260327.md` を読む
5. `SYSTEM_FULL_INVENTORY_20260327.md` を読む
6. 必要なら current の runbook を読む

そのあとにやること:

- すぐ編集しない
- 関係フォルダと入口を確認する
- 今回何をやるかを短く共有する
- 破壊的な操作は避ける

## 6. この環境での固定認識

- `C:` は hot runtime
- `D:` は control plane
- `D:\MD` は knowledge base
- `E:\masaos_mov` は warehouse
- `Z:` は remote runtime

## 7. current / next / legacy

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

## 8. 絶対に急がないこと

- current の物理移動
- legacy の削除
- `E:\masaos_mov` の大規模複製
- `C:\masao_ptz` の吸収
- `Z:\chatbot_v4` の吸収
- queue 混在

## 9. 推奨される次の実務

1. GitHub 公開版の README 骨子を先に定義する
2. 公開対象と除外対象を決める
3. 公開版の別ディレクトリを作る
4. そこへ最小構成をコピーする
5. sample data / mock config を用意する
6. 公開版で理解できる構造へ整える
7. その後に必要なら `D:\MasaoSystem` 側の整理を進める

## 10. ユーザー方針の固定

今回ユーザーが示した方針を、今後の再構築の基準方針として扱う。

その方針は次の通り:

1. まずプロジェクトを洗い出す
2. 別フォルダを作る
3. そこを基準に散らばっているものをコピーして整理する
4. 動作確認し、運用が崩れないことを確認する
5. 旧散在ラインを archive もしくは削減対象にする
6. 文章は整理して残す

現時点では、この方針で進めて問題ない。
