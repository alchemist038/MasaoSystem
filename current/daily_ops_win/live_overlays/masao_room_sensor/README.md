# まさお部屋 温湿度オーバーレイ

SwitchBot 温湿度計ProをOBSブラウザソースへ表示する。

2026-06-22以降の本番更新は、PCのBluetoothを使わないSwitchBot Hub / Cloud API方式。
BLE直接取得は調査・非常時用として残す。

朝配信準備では、OBS / PTZ / Bouyomi / スケジュール監視と同じ正規起動対象として扱う。

運用正本:

```text
D:\OBS\REC\overlays\masao_room_sensor
```

Git管理コピー:

```text
D:\MasaoSystem\current\daily_ops_win\live_overlays\masao_room_sensor
```

## OBS

- ソース種別: ブラウザ
- ローカルファイル: `D:\OBS\REC\overlays\masao_room_sensor\index.html`
- 幅: `1920`
- 高さ: `1080`
- FPS: `5`
- 位置: 画面全体に合わせる

URLで位置調整もできる。

```text
file:///D:/OBS/REC/overlays/masao_room_sensor/index.html?position=top-right
file:///D:/OBS/REC/overlays/masao_room_sensor/index.html?position=bottom-right
```

## 手動更新

Hub / Cloud API:

```powershell
py -3 D:\OBS\REC\overlays\masao_room_sensor\update_room_sensor_hub.py
```

BLE直接取得:

```powershell
C:\Users\alche\Desktop\OBS\venvs\switchbot_ble\Scripts\python.exe C:\Users\alche\Desktop\OBS\overlays\masao_room_sensor\update_room_sensor.py
```

## 常時更新

現在の本番起動は、Bluetoothマウス/イヤホンへの影響を避けるためHub / Cloud APIで60秒ごとに更新する。
配信準備時はこのHubウォッチャーを起動し、値と更新時刻を最終報告に含める。
ログやデータの書き込み先であるDドライブが一時的に準備不可になっても、ウォッチャーは終了せず次の周期で再試行する。

```powershell
D:\OBS\REC\overlays\masao_room_sensor\start_room_sensor_hub_watch.ps1
```

この方式はユーザー環境変数から次の2つを読む。

```text
SWITCHBOT_TOKEN
SWITCHBOT_SECRET
```

更新間隔を一時変更する場合:

```powershell
$env:MASAO_ROOM_SENSOR_HUB_PERIOD='120'
D:\OBS\REC\overlays\masao_room_sensor\start_room_sensor_hub_watch.ps1
```

BLE連続更新は旧方式。

```powershell
C:\Users\alche\Desktop\OBS\venvs\switchbot_ble\Scripts\python.exe C:\Users\alche\Desktop\OBS\overlays\masao_room_sensor\update_room_sensor.py --watch --interval 60 --timeout 15
```

BLEの配信優先型は、Bluetoothマウス/イヤホンへの影響を抑えるため、15分おきに最大20秒だけパッシブスキャンし、値が取れたらその回のスキャンを即停止する。

```powershell
C:\Users\alche\Desktop\OBS\overlays\masao_room_sensor\start_room_sensor_watch.ps1
```

調査時だけ旧条件の5分おき最大90秒を使う。

```powershell
C:\Users\alche\Desktop\OBS\overlays\masao_room_sensor\start_room_sensor_watch_legacy_300_90.ps1
```

一時的にアクティブスキャンへ戻す場合:

```powershell
$env:MASAO_ROOM_SENSOR_SCANNING_MODE='active'
C:\Users\alche\Desktop\OBS\overlays\masao_room_sensor\start_room_sensor_watch.ps1
```

## 温度アラート表示

しきい値は `sensor-config.js` で管理する。

```text
通常 -> 黄: 23.5C 以上
黄 -> 通常: 23.0C 未満
通常/黄 -> 赤: 25.5C 以上
赤 -> 黄/通常: 24.5C 未満
未更新警告: 45分以上更新なし
```

表示:

- 黄: 注意色、点滅なし
- 赤: 赤色、ゆっくり点滅
- 未更新: 温度色より優先し、更新遅れの点滅

ログ:

```text
D:\OBS\REC\logs\masao_room_sensor_hub_YYYY-MM-DD.log
C:\Users\alche\Desktop\OBS\logs\masao_room_sensor_YYYY-MM-DD.log
```

`--periodic` の通常ログは、成功/失敗ごとに `scanElapsed=...s` を出す。
この値で、最大スキャン時間をどこまで短くできるかを後から判断する。

BLE広告周期を調べる診断:

```powershell
C:\Users\alche\Desktop\OBS\venvs\switchbot_ble\Scripts\python.exe C:\Users\alche\Desktop\OBS\overlays\masao_room_sensor\diagnose_ble_advertisements.py --duration 600 --scanning-mode passive
```

Realtek RTL8852BE環境では連続スキャン中に `BTHUSB ID 5` が出る場合があるため、配信中は通常ウォッチャーの短時間スキャンを優先する。
