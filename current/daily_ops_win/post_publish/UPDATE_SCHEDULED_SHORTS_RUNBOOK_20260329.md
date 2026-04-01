# Scheduled Shorts Update Runbook

予約済み Shorts の `publishAt` を維持したまま、タイトルと説明欄だけを更新するときの手順です。

## スクリプト

- `D:\OBS\REC\work\update_scheduled_shorts.py`

## 関連ファイル

- 説明欄テンプレ:
  - `D:\OBS\REC\work\scheduled_shorts_description_2026-03-29.txt`
- タイトル対応表の例:
  - `D:\OBS\REC\work\scheduled_shorts_title_map_2026-03-29.json`
  - `D:\OBS\REC\work\scheduled_shorts_title_map_2026-03-30_to_2026-03-31_06.json`

## 既定の動き

- 対象は `private` かつ `publishAt` ありの Shorts
- 既存の予約時刻はそのまま残す
- `--description_file` を付けたときだけ説明欄を置き換える
- `--title_map_file` があれば、そのタイトルをそのまま使う
- `--title_prefix` を使うと、既知 prefix を外したうえで再構築できる

## 基本 dry-run

```powershell
python D:\OBS\REC\work\update_scheduled_shorts.py --dry_run --max 80
```

## 予約済みをまとめて更新する例

```powershell
python D:\OBS\REC\work\update_scheduled_shorts.py --dry_run --max 80 --title_prefix "" --strip_prefixes "Cute Bunny Masao " --description_file "D:\OBS\REC\work\scheduled_shorts_description_2026-03-29.txt"
```

## title map を使う例

```powershell
python D:\OBS\REC\work\update_scheduled_shorts.py --dry_run --max 80 --title_map_file "D:\OBS\REC\work\scheduled_shorts_title_map_2026-03-29.json" --description_file "D:\OBS\REC\work\scheduled_shorts_description_2026-03-29.txt"
```

## 特定 ID だけ更新する例

```powershell
python D:\OBS\REC\work\update_scheduled_shorts.py --dry_run --video_ids "FBIxwF9TBeE,6uQoWk4o3mE,GJjIR__8Ny8,NbYaKWcVPso,wglAmzAdwaM,rNLSDbq_zbA,MnMafqAFO8E,MAvAJwo9sIQ" --title_map_file "D:\OBS\REC\work\scheduled_shorts_title_map_2026-03-30_to_2026-03-31_06.json" --description_file "D:\OBS\REC\work\scheduled_shorts_description_2026-03-29.txt"
```

## 本番実行

`--dry_run` を外すだけです。

```powershell
python D:\OBS\REC\work\update_scheduled_shorts.py --video_ids "FBIxwF9TBeE,6uQoWk4o3mE,GJjIR__8Ny8,NbYaKWcVPso,wglAmzAdwaM,rNLSDbq_zbA,MnMafqAFO8E,MAvAJwo9sIQ" --title_map_file "D:\OBS\REC\work\scheduled_shorts_title_map_2026-03-30_to_2026-03-31_06.json" --description_file "D:\OBS\REC\work\scheduled_shorts_description_2026-03-29.txt"
```

## 注意

- このスクリプトは新しい予約枠を作らない
- Studio では見えていても uploads playlist から取れない予約動画がある
- その場合は URL から `videoId` を抜いて `--video_ids` で直接指定する
- 例:
  - `https://youtube.com/shorts/MAvAJwo9sIQ?feature=share`
  - `videoId = MAvAJwo9sIQ`

## 使い分け

- 予約済みの metadata 更新:
  - `update_scheduled_shorts.py`
- 未予約を最終予約の後ろへ 4 時間ピッチで足す:
  - `schedule_unscheduled_shorts_from_tail.py`
- 未予約を通常ルールでまとめて予約する:
  - `update_shorts.py`

## 安全手順

1. 先に `--dry_run`
2. 対象 `videoId` と `publishAt` を確認
3. 本番実行
4. YouTube Studio で数本だけ目視確認
