# Ubuntu Legacy Triage

作成日: 2026-03-28
参照元:

- `D:\MD\pc_back\MASAO_WINDOWS_REBUILD_ACTION_GUIDELINE_FINAL_2026-02-28.md`
- `D:\MD\pc_back\OLD360_360YOLO_script_map.md`
- `D:\MD\pc_back\PIPELINE_TIMELINE_CANONICAL_AUDIT.md`
- `D:\MD\pc_back\WIN_360YOLO_MIGRATION_PROMPT_PACK.md`
- `D:\MD\pc_back\masao_D_OBS_REC_analysis.md`

## 1. 結論

Ubuntu 系の旧ラインは、全部を一括削除する対象ではありません。
取捨選択は次の 3 分類で扱うのが安全です。

1. `残す`
   - 現行 Windows 本線がまだ依存しているもの
   - 自動追尾導入前資産の再処理に必要なもの
2. `凍結して参照用に残す`
   - 実運用の価値は落ちたが、思想やロジックの参照価値が高いもの
3. `本番から退役扱いにする`
   - 今後の正規運用から外すもの

## 2. 参照資料から読み取れる固定判断

### 2.1 正規運用ライン

参照資料の判断は一貫しています。

- 正規運用ラインは Windows canonical
- 場所は `D:\OBS\REC\scripts\youtube\yolo\WIN`
- 旧 Ubuntu ラインは当面 legacy 扱い

つまり、
Ubuntu 旧ラインを今後の正規本線として扱う前提は切ってよいです。

## 3. Ubuntu 系ラインの分類

### 3.1 Line-A: 旧360ライン（ΔY / cron中心）

想定フロー:

- `analyze_y2_events.py`
- `enqueue_daily_YA.py`
- `run_event_queue_pipeline.py`
- `upload_from_queue.py`

主な場所:

- `D:\OBS\REC\scripts\active`
- `D:\OBS\REC\scripts\youtube`
- `D:\OBS\REC\scripts\core`

判断:

- `日次本線としては凍結`
- `旧資産再処理ラインとしては保持`

理由:

- 360 / ΔY による動き抽出の価値はまだある
- 自動追尾導入前の資産を再利用するとき、このラインの構造が必要
- ただし daily production としては Windows 本線へ移行済み
- timeline 監査でも日次主軸は WIN 系

取扱い:

- `analyze_y2_events.py`
- `enqueue_daily_YA.py`
- `run_event_queue_pipeline.py`
- `api_decision_pipeline.py`

は「旧資産再処理ライン」として残す。

- `upload_from_queue.py`

は「必要時のみ使う optional stage」として残す。

### 3.2 Line-B: Ubuntu YOLO 中間ライン

想定フロー:

- `run_yolo_event_queue_pipeline.py`
- `run_yolo_queue_to_upload_queue.py`

判断:

- `退役扱い`
- `参照用にだけ残す`

理由:

- `posting/*.jsonl` 系の旧キューに依存
- 新しい運用文書、runbook、UI は WIN data 側を主語にしている
- 旧 Windows / Ubuntu 橋渡しの中間世代で、いまの正規形ではない

### 3.3 Line-C: Ubuntu YOLO v2 直呼びライン

想定フロー:

- `build_candidates_20s.py`
- `pick_from_candidates.py`
- `run_event_queue_pipeline_yolo.py`
- `run_event_queue_pipeline_yolo_v2.py`
- `upload_from_queue_yolo.py`

判断:

- `移行元ライン`
- `ロジック参照用として残す`
- `本番実行は禁止`

理由:

- 360 + YOLO の移行元として意味は大きい
- ただし現在の本線は WIN isolated
- migration pack でも old YOLO flows は reference only と読むのが自然

### 3.4 Line-D: shared core のうち残すべきもの

主な場所:

- `D:\OBS\REC\scripts\core`

判断:

- `一部は残す`

理由:

- `api_decision_pipeline.py` は Windows current がまだ参照している
- これは Ubuntu legacy の残骸というより、現行 Windows 本線の shared dependency

扱い:

- `api_decision_pipeline.py`
  - すぐ削除不可
  - 当面は current 依存として保持
  - 将来 `D:\MasaoSystem` 側へ移設または shared 化する

- `render_short_from_decision.py`
- `render_latest_from_decision.py`
  - 現時点では legacy / reference 扱い

## 4. 取捨選択の実務判断

### 4.1 残す

- `D:\OBS\REC\scripts\active\analyze_y2_events.py`
- `D:\OBS\REC\scripts\active\enqueue_daily_YA.py`
- `D:\OBS\REC\scripts\youtube\run_event_queue_pipeline.py`
- `D:\OBS\REC\scripts\core\api_decision_pipeline.py`

意味:

- motion 抽出の価値
- current の shared dependency
- 旧資産の再処理ライン

### 4.2 凍結して参照用に残す

- `D:\OBS\REC\scripts\youtube\upload_from_queue.py`
- `D:\OBS\REC\scripts\youtube\yolo\build_candidates_20s.py`
- `D:\OBS\REC\scripts\youtube\yolo\pick_from_candidates.py`
- `D:\OBS\REC\scripts\youtube\yolo\run_event_queue_pipeline_yolo.py`
- `D:\OBS\REC\scripts\youtube\yolo\run_event_queue_pipeline_yolo_v2.py`
- `D:\OBS\REC\scripts\youtube\yolo\upload_from_queue_yolo.py`
- `D:\OBS\REC\scripts\youtube\run_yolo_event_queue_pipeline.py`
- `D:\OBS\REC\scripts\youtube\run_yolo_queue_to_upload_queue.py`
- `D:\OBS\REC\scripts\core\render_short_from_decision.py`
- `D:\OBS\REC\scripts\core\render_latest_from_decision.py`

扱い:

- legacy へ寄せる
- 誤起動防止の明示を後で追加する
- runbook の主語から外す

### 4.3 本番から退役扱いにする

- Ubuntu cron 前提の full production flow
- `/media/sf_REC/...` 前提の旧キュー運用
- old 360 two-API direct production line

扱い:

- 新規投入しない
- 正規運用手順に載せない
- 本番 current の入口から切り離す

## 5. 今の再構築での意味

Ubuntu legacy の取捨選択は、次の形で反映するのがよいです。

1. `D:\MasaoSystem\legacy\linux_shared`
   - Ubuntu 旧ラインの参照用コピー置き場
2. `D:\MasaoSystem\current`
   - Windows canonical
3. `D:\MasaoSystem\shared`
   - current がまだ必要とする共通資産

特に注意:

- `scripts\core\api_decision_pipeline.py` を legacy 側へ完全隔離すると current が壊れる
- ここは「旧Ubuntu由来だが現行依存あり」の例外として扱う

## 6. 一言で要約

Ubuntu 系の旧ラインは、

- `motion 抽出の思想は残す`
- `旧資産再処理ラインとしては残す`
- `daily production としては退役`
- `shared core の一部だけは現役依存として残す`

が結論です。

補足:

- 正規 Windows ラインでは API1 役を local YOLO が担う
- したがって Ubuntu 側の API1 crop 決定システムは正規本線には持ち込まない

## 7. 次の作業

1. `legacy\linux_shared` へ Ubuntu 旧ラインを参照用コピーする
2. `api_decision_pipeline.py` を current/shared のどこへ置くか決める
3. 旧ラインを runbook と入口から外す
4. 誤起動防止の印をつける
