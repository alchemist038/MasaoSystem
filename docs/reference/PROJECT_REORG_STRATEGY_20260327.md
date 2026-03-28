# プロジェクト整理方針

作成日: 2026-03-27

## 1. 前提

現在の実運用で優先して守るべき入口は次の 2 つ。

1. `D:\OBS\REC\scripts\youtube\yolo\WIN\UPLOAD_RUNBOOK.md`
2. `D:\OBS\REC\work\UPDATE_SHORTS_RUNBOOK.md`

将来的に再利用・整理対象になる可能性が高いのは次。

- `D:\OBS\REC\scripts\youtube\yolo`

このため、整理の第一原則は次の通り。

- 今の実行手順は壊さない
- いきなり移動しない
- まず「本線」と「保留線」を決める
- 移動するときは互換ラッパか案内ファイルを置く

## 2. このプロジェクトを機能で分けると

時系列の作業としては、次の 6 本に分けるのが自然。

### 2.1 録画前処理ライン

目的:

- 長時間ライブ録画を処理しやすい形にする

主な内容:

- 360 化・軽量化
- `proxy_360.mp4` 作成
- セッション単位の素材整理

### 2.2 ΔY 動体検出ライン

目的:

- 録画全体から動きのある区間を粗く拾う

主な内容:

- `showinfo`
- `meanY`
- `deltaY`
- イベント候補抽出

### 2.3 YOLO フィルタライン

目的:

- 「うさぎのまさお」が映っている区間に絞る

主な内容:

- `raw_yolo.jsonl`
- 候補点数化
- ピック
- 20 秒候補作成

### 2.4 PTZ 由来ショート生成ライン

目的:

- PTZ 制御で被写体が中央にいる時間が長くなった録画から
- モーション値や検出値を使ってクリップ位置を決める

主な内容:

- 20 秒固定ショート
- `crop_x`
- JPEG から metadata 生成
- render
- upload

### 2.5 投稿後メンテナンスライン

目的:

- 手動アップロード済み動画や非公開動画を一括整備する

主な内容:

- タイトル更新
- 説明欄更新
- 公開予約
- プレイリスト追加

### 2.6 チャットボットライン

目的:

- 特定ワード返信
- スーパーチャット返信
- 配信中補助

この機能はショート生成ラインとは別プロジェクトとして切り出した方が管理しやすい。

## 3. 今の実態に当てはめた本線

### 3.1 現在の本線

現時点では次を本線とみなすのがよい。

- Shorts 本線:
  - `scripts\youtube\yolo\WIN`
- 投稿後更新本線:
  - `work`

理由:

- 実際に使っている runbook がここにある
- 実運用の入口が明確
- 動いている前提を崩したくない

### 3.2 将来の本線候補

- `scripts\WIN_YOLO_PTZ_20S`

これは「次の正式ライン候補」。
ただし、現時点ではまだ完全移行前として扱う。

### 3.3 保留・研究・旧資産

- `scripts\youtube\yolo`
- `WIN`
- `jobs`
- `scripts\active`
- `scripts\core`
- `scripts\youtube` の Linux 依存部分

これらは削除対象ではなく、役割を明示したうえで legacy / source / research 側へ寄せる対象。

## 4. きれいにまとめるときの基本方針

おすすめは「機能別に 4 階層へ分ける」やり方。

### 4.1 runner

実際に人が叩く入口だけを置く。

例:

- 現在の Shorts 運用 runbook
- 投稿後更新 runbook
- 起動用 `.ps1`

### 4.2 pipeline

動画処理そのものを置く。

例:

- 360 前処理
- ΔY 検出
- YOLO フィルタ
- PTZ ショート生成
- render / upload

### 4.3 shared

共通部品だけを置く。

例:

- config loader
- queue utilities
- time / schedule utilities
- YouTube API helper
- OpenAI API helper

### 4.4 archive / legacy / research

今は本線ではないが、知見として残したいものを置く。

例:

- Ubuntu 前提ライン
- 旧 WIN UI
- 試作スクリプト
- 学習データ作成補助

## 5. すぐやるべきでないこと

次は先にやらない方がよい。

1. `scripts\youtube\yolo\WIN` をいきなり別場所へ移動する
2. `work\update_shorts.py` を今すぐ pipeline 側へ統合する
3. Linux 旧ラインを削除する
4. `keys`, `prompts`, `bgm` の位置を先に変える

理由は単純で、今の runbook が直接パス指定しているから。

## 6. 先にやると効果が大きいこと

### 6.1 運用入口を明文化する

最低限、次の 3 区分を決める。

- current
- next
- legacy

具体的には:

- current:
  - `scripts\youtube\yolo\WIN`
  - `work`
- next:
  - `scripts\WIN_YOLO_PTZ_20S`
- legacy:
  - `WIN`
  - Ubuntu 前提ライン

### 6.2 config 依存へ寄せる

最初の整理対象は絶対パス。

特に次は設定化したい。

- `D:\OBS\REC\keys\youtube\token.json`
- `D:\OBS\REC\prompts\...`
- `E:\masaos_mov`
- `D:\OBS\REC\bgm\...`

### 6.3 「役割別フォルダ名」を導入する

現状は `scripts` 配下にいろいろ混ざっている。
将来的には少なくとも次の見え方に揃えるとわかりやすい。

- `pipelines\shorts_yolo_win_current`
- `pipelines\shorts_ptz_win_next`
- `pipelines\legacy_linux`
- `tools\post_publish`
- `bots\chat_responder`
- `ml\training`

ただし、これは最終形であって今すぐ移動はしない。

## 7. 実行可能性を守る移行順

安全な順番は次。

### Phase 0

文書だけで本線を確定する。

- current
- next
- legacy

### Phase 1

今の運用パスのまま、起動入口を追加する。

例:

- `run_current_shorts_win.ps1`
- `run_update_shorts.ps1`

この段階では中身は既存 runbook の呼び出しだけでよい。

### Phase 2

現在本線の `scripts\youtube\yolo\WIN` から、共有化できるものだけを抜き出す。

対象候補:

- queue 操作
- config 読み込み
- YouTube token 読み込み
- 時刻計算

### Phase 3

`scripts\WIN_YOLO_PTZ_20S` を next から current に上げられるか検証する。

条件:

- build
- pick
- render
- upload
- runbook

が current と同等に回ること。

### Phase 4

移行完了後にだけ legacy を畳む。

この時点で初めて次を検討する。

- `WIN`
- Linux 旧ライン
- `scripts\youtube\yolo\WIN` の旧部品

## 8. 推奨する最終的な見え方

最終的には、利用者視点では次の 3 本に見えるのが理想。

1. まさおショート生成
2. 投稿後の一括更新
3. 配信チャットボット

内部では細かく分かれていてもよいが、入口はこの 3 つに絞る。

## 9. 今の結論

いま一番よい整理方針は、「現運用の `scripts\youtube\yolo\WIN` を current として固定し、`work` を post-publish 専用として切り分け、`scripts\WIN_YOLO_PTZ_20S` を next として育てる」こと。

つまり、先に大移動するのではなく、

- 現在使うものを current と明記
- 次に移す先を next と明記
- 旧資産を legacy と明記

この 3 層で整理を始めるのが最も安全。
