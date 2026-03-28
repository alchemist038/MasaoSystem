# バッチ投稿ランブック（UI運用・改修なし）

最終更新: 2026-03-01  
対象: `D:\OBS\REC\scripts\youtube\yolo\WIN\ui\app.py`

## 目的
- 同じ投稿作業を毎回ブレずに実行するための手順書。
- 「候補選定 -> JPEG/文面確認 -> 除外 -> 再補充 -> 投稿」を再現可能にする。

## 今回の標準条件（テンプレ）
- 本数: `12本`
- 期間: `4日間`
- 投稿時刻: `02:00 / 06:00 / 22:00`（JST）
- 尺: `20秒`（`render_duration_sec=20`）
- 条件:
  - `02:00` と `06:00`: モーション `50帯`（目安: `50 <= motion < 80`）
  - `22:00`: モーション `80以上`（`motion >= 80`）
  - 共通: `hits >= 20`
- 除外基準:
  - 人の顔がはっきり映る
  - JPEGが明らかにおかしい（破綻・誤クロップ）
  - title/description が明らかに不自然

## 事前確認
1. キュー残件を確認（空であること）
   - `event_queue_yolo_win.jsonl`
   - `upload_queue_yolo_win.jsonl`
2. `config.json` の主要設定確認
   - `base_dir`
   - `publish_pitch_hours`（UI空欄時に使われる）
   - `render_duration_sec=20`

## 実行フロー（改修なし）
1. `候補作成`（必要時）
   - UIボタン: `1) 候補作成`
2. 条件で候補をピックして `event_queue` を作る
   - 3枠（02/06/22）を4日分で計12本
   - 02/06 は 50帯、22 は 80以上
3. `パイプライン実行`
   - UI設定:
     - `API 実行前に JPEG を確認` = ON
     - `確認後の処理` = `approve`（バッチ実行時）
   - UIボタン: `3) パイプライン実行`
4. JPEG/decision確認
   - 画像: `events/<event_name>/images_review/review_00s.jpg ... review_15s.jpg`
   - 文面: `events/<event_name>/api/v*/decision.json`
5. 除外判定
   - NGがあれば除外し、同じ時刻枠へ再補充
6. `アップロード`
   - UIボタン: `4) アップロード`
   - 完了後、`upload_queue` が空になっていることを確認

## 除外時のルール
- 除外候補は「理由」を記録する:
  - `face_visible`
  - `jpeg_bad`
  - `text_bad`
- 除外で不足した本数は、同じ枠（02/06/22）条件で再ピックして補充する。
- 4日 x 3枠の時刻配置は崩さない。

## レポート保存先（推奨）
- 選定一覧: `WIN/data/batch_YYYYMMDD_selection.json`
- JPEG確認シート: `WIN/data/batch_YYYYMMDD_review_sheet.jpg`
- 文面確認結果: `WIN/data/batch_YYYYMMDD_decision_review.json`

## 依頼テンプレ（次回用）
以下をそのまま伝える:

`4日間12本。02:00/06:00はmotion50帯、22:00はmotion80以上。hits20以上、20秒。JPEGとtitle/descriptionを確認し、顔がはっきり映るもの・不自然なものを除外。除外分は再ピックして同時刻に補充して投稿。`

