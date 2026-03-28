# Masao PTZ Tracker V4 仕様書

作成日: 2026-03-07

対象実装: [C:\masao_ptz\track_masao_ptz_v4_ui.py](C:\masao_ptz\track_masao_ptz_v4_ui.py)

## 1. 概要

`track_masao_ptz_v4_ui.py` は、YOLO による `masao` 検出結果を使って PTZ カメラへ OSC 制御を送り、自動追尾を行う Windows 向けの UI 付きトラッカーである。

主な役割は次の 4 つ。

- カメラ映像の取得
- YOLO 推論による対象検出
- P 制御 + EMA によるパン・チルト指令生成
- Tkinter UI と OSC による運用制御

V4 の現行標準は `masao_V06.pt` を既定モデルとして使う構成である。

## 2. 実行環境と入出力

### 2.1 カメラ入出力

- 入力カメラ: `cv2.VideoCapture`
- 既定解像度: `1920x1080`
- 既定 FPS: `30`
- 仮想カメラ出力: `pyvirtualcam`

定数:

- `CAP_W=1920`
- `CAP_H=1080`
- `CAP_FPS=30`
- `V_W=1920`
- `V_H=1080`
- `V_FPS=30`

### 2.2 OSC

- 送信先 IP: `127.0.0.1`
- 送信ポート: `33333`
- 受信ポート: `33334`
- 送信メッセージ: `/XY [pan, tilt]`
- 受信メッセージ: `/Tracking`

`/Tracking` を受けると `tracking_enabled` を ON/OFF できる。

### 2.3 モデル

- 既定モデル名: `masao_V06.pt`
- 解決ルール:
  - 絶対パスならそのまま使用
  - 相対パスならスクリプト配置フォルダ基準で解決

このため `C:\masao_ptz\masao_V06.pt` を置けば、そのまま起動できる。

## 3. システム構成

`PTZTracker` クラスが主処理を持つ。構成は次の通り。

- UI スレッド
  - Tkinter UI
- Run Loop スレッド
  - カメラ取得
  - 検出結果の採用判定
  - 追尾/ロスト/検索の状態遷移
  - OSC 送信
  - 仮想カメラ出力
- Inference スレッド
  - 最新フレーム 1 枚のみを対象に YOLO 推論

推論キューは `Queue(maxsize=1)` で、常に最新フレーム優先。

## 4. 起動と排他

### 4.1 単一起動

Windows named mutex を使い、同時多重起動を防ぐ。

- mutex 名: `Local\MasaoPTZ_TrackV4_UI_SingleInstance`

すでに起動中なら新規プロセスは終了する。

### 4.2 起動シーケンス

1. セッション ID を生成
2. 単一起動ガードを取得
3. `PTZTracker` を生成
4. `run_loop()` を別スレッドで起動
5. UI を生成して `mainloop()` に入る

## 5. 検出処理

### 5.1 推論条件

既定値:

- `conf = 0.55`
- `imgsz = 640`

対象クラス:

- `DEFAULT_TARGET_CLASSES = {0}`

除外クラス:

- `DEFAULT_IGNORE_CLASSES = set()`

### 5.2 候補選定

YOLO の出力から対象クラスだけを残し、最終候補 `best_det` を 1 つ選ぶ。

選定ルール:

1. `confidence` が最も高い候補を優先
2. `confidence` が同値なら面積が大きい候補を優先

これは、従来の「最大面積優先」より誤検出で大きい箱に引っ張られにくくするための変更である。

### 5.3 連続検出確認

V4 現行版では、1 フレーム単発の検出では追尾を開始しない。

- `DET_CONFIRM_N = 3`

ただし単なる 3 フレーム連続ではなく、同じ対象とみなせる検出が続いた場合のみ有効化する。

同一判定条件:

- IoU が `0.10` 以上
- または中心距離が `max(140px, 対象サイズ * 0.45)` 以下

内部状態:

- `det_anchor`: 連続確認中の基準検出
- `det_streak`: 同一対象の連続検出回数

これにより、位置が飛ぶ誤検出が 3 回続いても追尾開始しにくくしている。

## 6. 追尾制御

### 6.1 中心偏差

採用した検出 `det` から bbox 中心を取り、実フレームサイズ基準で偏差を計算する。

- `dx = cx - frame_width / 2`
- `dy = cy - frame_height / 2`

固定の `1920x1080` を前提にせず、実際に読めたフレームサイズを使う。

### 6.2 フィルタ

偏差には EMA をかける。

- `dx_f = (1-a) * dx_f + a * dx`
- `dy_f = (1-a) * dy_f + a * dy`
- `a = ema_alpha`

既定値:

- `ema_alpha = 0.65`

### 6.3 デッドゾーン

中央付近の微小な揺れで PTZ が反応しないよう、X/Y にデッドゾーンを設ける。

既定値:

- `deadzone_x = 80`
- `deadzone_y = 45`

### 6.4 速度算出

デッドゾーン外の偏差にゲインを掛け、上限速度でクリップして `pan_cmd`, `tilt_cmd` を決める。

既定値:

- `pan_gain = 0.045`
- `tilt_gain = 0.06`
- `max_speed = 55`

### 6.5 パン方向の記録

`pan_cmd` の符号から直近のパン方向を記録し、ロスト後の検索開始方向に使う。

- `last_pan_dir = +1` なら右
- `last_pan_dir = -1` なら左

## 7. ロスト処理と検索

### 7.1 ロスト猶予

検出が消えてもすぐ検索に入らず、一定時間は停止して待つ。

- `lost_grace_sec = 15.0`

### 7.2 検索開始

`lost_grace_sec` を超えると `search_mode=True` にし、検索ステートマシンへ入る。

開始方向は `last_pan_dir` を引き継ぐ。

### 7.3 検索パターン

検索は次の段階で進む。

1. `pan_first`
2. `pan_second`
3. `tilt_down`
4. `tilt_up`
5. `pan_step`

調整パラメータ:

- `breath_sec = 0.15`
- `search_pan_speed = 12`
- `search_tilt_speed = 40`
- `pan_sec_first = 15.0`
- `pan_sec_second = 15.0`
- `tilt_down_sec = 6.0`
- `tilt_up_step_sec = 1.2`
- `pan_sec_step = 15.0`
- `up_steps = 2`

検索中は推論頻度を少し落とせる。

- `search_infer_interval_sec = 0.08`

## 8. 自動送信と UI

### 8.1 UI の主な役割

Tkinter UI から次を切り替えできる。

- `AUTO SEND`
- `TRACKING ENABLE`
- `SHOW BBOX`
- `MODEL_PATH`
- 各種スライダーパラメータ

### 8.2 ボタン

- `PAUSE`
  - `auto_send=False`
  - `/XY [0,0]` を送る
- `RESUME`
  - `auto_send=True`
- `EXIT`
  - `running=False` にして UI を閉じる

### 8.3 調整可能パラメータ

UI から調整できる主な項目:

- `deadzone_x`
- `deadzone_y`
- `pan_gain`
- `tilt_gain`
- `max_speed`
- `ema_alpha`
- `cmd_period`
- `lost_grace_sec`
- `breath_sec`
- `search_pan_speed`
- `search_tilt_speed`
- `pan_sec_first`
- `pan_sec_second`
- `tilt_down_sec`
- `tilt_up_step_sec`
- `pan_sec_step`
- `up_steps`
- `conf`
- `imgsz`
- `search_infer_interval_sec`

## 9. カメラ・VCam・OSC の自己回復

### 9.1 カメラ read fail

`cap.read()` 失敗が一定回数続いたらカメラを reopen する。

- `CAM_READ_FAIL_REOPEN_COUNT = 8`
- `CAM_REOPEN_RETRY_SEC = 1.0`

### 9.2 黒画面回復

`cap.read()` 自体は成功しても、実フレームが全黒の状態が続けば再接続を試みる。

- `BLACK_FRAME_REOPEN_MIN_STREAK = 3`
- `BLACK_FRAME_REOPEN_SEC = 2.0`
- `BLACK_FRAME_REOPEN_RETRY_SEC = 3.0`

### 9.3 仮想カメラ再試行

仮想カメラ開始に失敗した場合も、一定間隔で再試行する。

- `VCAM_RETRY_SEC = 5.0`

### 9.4 OSC bind 再試行

OSC 受信ポート bind に失敗した場合も再試行する。

- `OSC_BIND_RETRY_SEC = 5.0`

## 10. ログ

ログは標準出力と `track_masao_ptz_v4_ui_error.log` に書かれる。

代表的なログ:

- `session_start`
- `runloop_thread_start`
- `ready`
- `model_load`
- `health`
- `cam_read_fail`
- `black_frame_detected`
- `black_frame_recover`
- `vcam_start_fail`
- `osc_bind_fail`
- `ui_mainloop_exit`

## 11. 現行標準運用

現時点での標準運用は次の通り。

- モデルは `C:\masao_ptz\masao_V06.pt`
- スクリプトは `track_masao_ptz_v4_ui.py`
- 誤検出対策として `conf=0.55` を既定化
- 追尾開始は「同一対象の 3 回連続確認」必須
- 候補選定は「最大面積」ではなく「最高 confidence」優先

## 12. 既知の運用上の注意

- `masao_V06.pt` は git では通常管理していないため、実行環境ごとに配置が必要
- `conf` を上げすぎると誤検出は減るが見逃しは増える
- `SHOW BBOX` は確認用であり、常時 ON にする必要はない
- `lost_grace_sec` を長くしすぎるとロスト後の再探索開始が遅くなる

## 13. 今回の V4 更新要点

今回の V4 仕様更新点は次の 4 つ。

1. `masao_V06.pt` を既定モデル化
2. 相対 `MODEL_PATH` をスクリプト配置フォルダ基準で解決
3. 誤検出抑制のため、最高 confidence 優先で候補選定
4. 誤追尾抑制のため、同一位置の連続検出でのみ追尾開始

以上をもって、現行の `Masao PTZ Tracker V4` の運用仕様とする。
