# 手動アップロード動画の一括更新ランブック

手動でアップロードされた非公開のショート動画のうち、説明欄が空欄の動画に対して、タイトル、説明欄、公開予約、再生リスト追加を一括で行う手順です。

## 使用スクリプト
- スクリプトパス: `D:\OBS\REC\work\update_shorts.py`
- 認証情報: `D:\OBS\REC\keys\youtube\token.json`
- 除外管理リスト: `D:\OBS\REC\work\UNLISTED_VIDEOS_2026-03-23.md`

## 除外ルール
- 今回公開予約を設定した23本は `UNLISTED_VIDEOS_2026-03-23.md` に記載しない。
- `UNLISTED_VIDEOS_2026-03-23.md` に記載されている動画は、次回以降の一括更新・公開予約の対象から除外する。

## 更新内容の標準
1. **タイトル**: 先頭に `"Cute Bunny Masao "` を付与。
2. **説明欄**: プロフィール、ハッシュタグ、ライブ告知を含む定型文をセット。
3. **公開スケジュール**:
   - **2026-03-27 22:00 (JST)** を先頭に、以後 **4時間おき**。
   - 具体的な枠は **02:00 / 06:00 / 10:00 / 14:00 / 18:00 / 22:00** (JST)。
   - スクリプトが既存の予約と重複しない空き枠を自動で検索します。
4. **追加先再生リスト**:
   - `うさぎのまさお｜可愛いショート動画集` (ID: `PLvSj66EpFnyf-D10-HV16IELUofOSxHm7`)
   - `うさぎのまさお｜ライブ切り抜きショート` (ID: `PLvSj66EpFnyeFFDKuWhE-jYm4nuJdFMDd`)

## 実行手順

### 1. 動作テスト（Dry Run）
まずは実際に更新を行わず、どの動画がいつ予約されるかを確認します。

```powershell
python D:\OBS\REC\work\update_shorts.py --dry_run --exclude_file "D:\OBS\REC\work\UNLISTED_VIDEOS_2026-03-23.md" --playlist "PLvSj66EpFnyf-D10-HV16IELUofOSxHm7,PLvSj66EpFnyeFFDKuWhE-jYm4nuJdFMDd" --max 50
```

- `--max 50` は今回の対象23本を含む直近動画をスキャン対象にする設定です。
- `--exclude_file` に記載された `videoId` は自動で処理対象から除外されます。
- 画面に表示される候補と予定日時が正しいか確認してください。

### 2. 本番実行
内容に問題がなければ、`--dry_run` を外して実行します。

```powershell
python D:\OBS\REC\work\update_shorts.py --exclude_file "D:\OBS\REC\work\UNLISTED_VIDEOS_2026-03-23.md" --playlist "PLvSj66EpFnyf-D10-HV16IELUofOSxHm7,PLvSj66EpFnyeFFDKuWhE-jYm4nuJdFMDd" --max 50
```

実行後、「○件処理成功」と表示されれば完了です。YouTube Studioで予約状況を確認してください。

## 補足
- 説明欄やタイトル、開始日のロジックを変更したい場合は `update_shorts.py` 内の以下の定数を編集してください：
  - `TITLE_PREFIX`: タイトルの先頭文言
  - `DESCRIPTION_TEMPLATE`: 説明欄のテンプレート
  - `SCHEDULE_HOURS`: 予約投稿する時間（[2, 6, 10, 14, 18, 22]）
  - `START_DATE`: 予約を開始する日時の基準
