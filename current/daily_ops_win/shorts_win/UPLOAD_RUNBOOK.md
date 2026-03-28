# 3本アップ作業ログと繰り返し手順

更新日: 2026-02-18
対象環境: `D:\OBS\REC\scripts\youtube\yolo\WIN`

## 今回実施したアップ結果（3本）

- `07080_07100` -> `eLVmHJ0PSmA`
- `21660_21680` -> `tI713DNf4lU`
- `11840_11860` -> `5DM2SeuASX4`

公開時刻（JST）:

- `2026-02-20T22:00:00+09:00`
- `2026-02-21T02:00:00+09:00`
- `2026-02-21T06:00:00+09:00`

送信時のUTC変換ログ（参考）:

- `2026-02-20T13:00:00Z`
- `2026-02-20T17:00:00Z`
- `2026-02-20T21:00:00Z`

## 繰り返し手順（CLI）

1. 候補作成

```powershell
python scripts\build_candidates_win.py --config config.json --base-dir E:\masaos_mov
```

2. ピック（例: 動き優先 / 3本 / 4時間おき）

```powershell
python scripts\pick_global_candidates_win.py --config config.json --base-dir E:\masaos_mov --mode motion --total 3 --no-overlap --start 2026-02-20T22:00:00 --pitch-hours 4
```

3. パイプライン実行（レビューは自動承認）

```powershell
python scripts\run_event_queue_pipeline_yolo_win.py --config config.json --review-before-api --review-action approve --max 10
```

4. アップロード

```powershell
python scripts\upload_from_queue_win.py --config config.json --max 10
```

## 運用メモ

- `prompt` は同じCLIで入力待ちになるため、通常は `approve` を推奨。
- `lock exists` が出た場合は、先行プロセス終了を確認してから再実行。
- 日本時間を確実に扱うため、`publishAt` は `+09:00` 付きで扱う実装に修正済み。
- 完了確認は以下:

```powershell
Get-Content data\event_queue_yolo_win.jsonl | Measure-Object -Line
Get-Content data\upload_queue_yolo_win.jsonl | Measure-Object -Line
```

両方 `0` なら当該バッチは処理完了。

## `ui\app.py` を使った3月運用ルール（追加）

対象: `D:\OBS\REC\scripts\youtube\yolo\WIN\ui\app.py`

- 期間: 3月 `n` 日から `n` 日まで（例: `2026-03-06` 〜 `2026-03-09`）
- 投稿本数: 合計 `12` 本
- 想定配分: 1日 `3` 本（`22:00` / `02:00` / `06:00`）

時間帯ごとのピック条件（JST）:

- `22:00`: モーション `80` 以上、フレーム `20`
- `02:00`: モーション `50` 程度（目安 `45`〜`60`）、フレーム `20`
- `06:00`: モーション `50` 程度（目安 `45`〜`60`）、フレーム `20`

### 事前チェック（必須）

各候補で次を確認し、問題があれば除外する:

1. タイトル: 不自然な文言・崩れ・重複がないこと
2. 説明欄: 内容が破綻していないこと（空欄/不正値/意味不明文を除外）
3. JPEG: 明らかに不自然なサムネイルを除外
4. JPEG: 人の顔がはっきり識別できるものは除外

### 除外時の再ピック

- 除外した枠は同じ時間帯条件で再ピックする
- 12本すべてがチェック通過するまで再選定を繰り返す

### 在庫不足時の連絡ルール（必須）

- 事前に条件ごとの在庫数（例: `motion >= 70` かつ `hits >= 18`）を確認する
- 必要本数を満たせない場合は、投稿実行前に「在庫不足」を必ず報告する
- 報告時は以下を明記する:
  1. 不足している枠（`02:00` / `06:00` / `22:00`）
  2. 必要本数と確保本数（不足本数）
  3. 代替案（閾値緩和・期間短縮・本数調整など）

### 実施フロー（`app.py`）

1. `app.py` を起動
2. 期間（3月 `n` 日〜`n` 日）と本数（12本）を設定
3. 時間帯ごとに上記モーション/フレーム条件で候補作成
4. タイトル・説明欄・JPEGを目視チェックして除外判定
5. 除外分を再ピックし、12本を確定
6. 投稿実行
7. 必要に応じてキュー残件（`event_queue` / `upload_queue`）を確認

### 左右揺れ検討メモ（2026-03-06）

- 背景の横移動より、開始直後に被写体位置が大きく横へ跳ぶ候補があり、固定クロップだと左右の揺れとして見えやすい。
- 特に `2026-03-09 02:00 JST` 用に確認した `2026-02-20_06-45-14 / 31340_31360` は、開始 `2` 秒未満に揺れが集中していた。
- API に渡す `20` 枚の `1fps` JPEG でも傾向は見えるが、開始直後の揺れは `raw_yolo.jsonl` の数値で見た方が判定しやすい。

検討中の指標:

1. `head_span_0_2s`: 先頭 `0-2` 秒の `cx` 振れ幅
2. `head_shift`: 先頭 `3` 秒の中央値と残り `17` 秒の中央値の差
3. `offscreen_sec`: 固定クロップ想定で被写体中心が画面外に出る秒数

確認対象 `2026-02-20_06-45-14 / 31340_31360` の参考値:

- `head_span_0_2s = 74.1`
- `head_shift = 125.9`
- `offscreen_sec = 2`

暫定の在庫影響試算（未消化 / `hits >= 20`）:

- `head_span_0_2s <= 60`: `moderate 153 -> 144`, `high 110 -> 87`
- `head_span_0_2s <= 60 and head_shift <= 100`: `moderate 153 -> 144`, `high 110 -> 50`
- `head_span_0_2s <= 60 and head_shift <= 100 and offscreen_sec <= 5`: `moderate 153 -> 144`, `high 110 -> 33`
- `dx_max <= 80 and offscreen_sec <= 2` は厳しすぎて `high 110 -> 7` まで減るため、初期案としては不採用寄り

次回検討用の暫定方針:

- `motion` は面白さの指標として残す
- 別軸で「左右揺れ危険度」を `raw_yolo.jsonl` から判定する
- 第一候補は `head_span_0_2s <= 60 and head_shift <= 100`
- `offscreen_sec` は追加の安全条件として扱う
