# Path Rewrite Plan

菴懈・譌･: 2026-03-28

## 1. 逶ｮ逧・
縺薙・譁・嶌縺ｯ縲・`D:\MasaoSystem` 蛛ｴ縺ｧ蜍穂ｽ懃｢ｺ隱阪↓蜈･繧句燕縺ｫ縲・縺ｩ縺ｮ邨ｶ蟇ｾ繝代せ繧偵←縺薙∈蟇・○逶ｴ縺吝ｿ・ｦ√′縺ゅｋ縺九ｒ謨ｴ逅・☆繧九◆繧√・菫ｮ豁｣險育判縺ｧ縺吶・
## 2. 蝓ｺ譛ｬ譁ｹ驥・
- `D:\OBS\REC` 逶ｴ蜿ら・繧呈ｸ帙ｉ縺・- `shared` 繧貞盾辣ｧ縺吶ｋ蠖｢縺ｸ蟇・○繧・- queue 縺ｨ logs 縺ｯ `D:\MasaoSystem` 蛛ｴ縺ｮ蟆ら畑繝代せ縺ｫ縺吶ｋ
- `E:\masaos_mov` 縺ｯ蜈ｱ譛牙牙ｺｫ縺ｨ縺励※縺昴・縺ｾ縺ｾ菴ｿ縺・- `C:\Windows\Fonts\meiryo.ttc` 縺ｯ Windows 萓晏ｭ倥→縺励※險ｱ螳ｹ縺吶ｋ

## 3. current\\shorts_win

### config / code

菫ｮ豁｣蟇ｾ雎｡:

- `current\daily_ops_win\shorts_win\config.json`
- `current\daily_ops_win\shorts_win\config.example.json`
- `current\daily_ops_win\shorts_win\scripts\upload_from_queue_win.py`
- `current\daily_ops_win\shorts_win\scripts\manage_youtube_videos_win.py`
- `current\daily_ops_win\shorts_win\scripts\run_event_queue_pipeline_yolo_win.py`

谿九▲縺ｦ縺・ｋ荳ｻ縺ｪ邨ｶ蟇ｾ蜿ら・:

- `D:\OBS\REC\keys\youtube\token.json`
- `D:\OBS\REC\prompts\api2_system_yolo.txt`
- `D:\OBS\REC\scripts\core\api_decision_pipeline.py`

蟇・○蜈亥呵｣・

- token:
  - `D:\MasaoSystem\shared\keys\youtube\token.json`
- prompt:
  - `D:\MasaoSystem\shared\prompts\api2_system_yolo.txt`
- queue:
  - `D:\MasaoSystem\current\daily_ops_win\shorts_win\data\*.jsonl`

隕∵､懆ｨ・

- `api_script` 縺ｯ legacy core 繧偵∪縺蜿ら・縺励※縺・ｋ
- 縺薙％繧偵←縺・桶縺・°縺ｧ current 縺ｮ迢ｬ遶句ｺｦ縺悟､峨ｏ繧・
### README / runbook

菫ｮ豁｣蟇ｾ雎｡:

- `current\daily_ops_win\shorts_win\README.md`
- `current\daily_ops_win\shorts_win\UPLOAD_RUNBOOK.md`
- `current\daily_ops_win\shorts_win\UI_SPEC.md`
- `current\daily_ops_win\shorts_win\ui\BATCH_POSTING_RUNBOOK.md`

谿九▲縺ｦ縺・ｋ荳ｻ縺ｪ險倩ｿｰ:

- `D:\OBS\REC\scripts\youtube\yolo\WIN`
- `E:\masaos_mov`

譁ｹ驥・

- `D:\MasaoSystem\current\daily_ops_win\shorts_win` 繧貞燕謠舌↓譖ｸ縺肴鋤縺医ｋ
- `E:\masaos_mov` 縺ｯ縺昴・縺ｾ縺ｾ谿九☆

## 4. current\\post_publish

菫ｮ豁｣蟇ｾ雎｡:

- `current\daily_ops_win\post_publish\update_shorts.py`
- `current\daily_ops_win\post_publish\get_playlists.py`
- `current\daily_ops_win\post_publish\test_status.py`
- `current\daily_ops_win\post_publish\UPDATE_SHORTS_RUNBOOK.md`

谿九▲縺ｦ縺・ｋ荳ｻ縺ｪ邨ｶ蟇ｾ蜿ら・:

- `D:\OBS\REC\keys\youtube\token.json`
- `D:\OBS\REC\work\update_shorts.py`
- `D:\OBS\REC\work\UNLISTED_VIDEOS_2026-03-23.md`

蟇・○蜈亥呵｣・

- token:
  - `D:\MasaoSystem\shared\keys\youtube\token.json`
- exclude list:
  - `D:\MasaoSystem\current\daily_ops_win\post_publish\UNLISTED_VIDEOS_2026-03-23.md`

## 5. next\\shorts_ptz_win

菫ｮ豁｣蟇ｾ雎｡:

- `next\shorts_ptz_win\config.json`
- `next\shorts_ptz_win\config.example.json`
- `next\shorts_ptz_win\scripts\upload_from_queue_win_yolo_ptz_20s.py`

谿九▲縺ｦ縺・ｋ荳ｻ縺ｪ邨ｶ蟇ｾ蜿ら・:

- `D:\OBS\REC\keys\youtube\token.json`

隧穂ｾ｡:

- current 繧医ｊ閾ｪ蟾ｱ螳檎ｵ舌↓霑代＞
- token 蜿ら・繧・shared 蛛ｴ縺ｸ蟇・○繧後・縲√°縺ｪ繧願ｦ矩壹＠縺瑚憶縺上↑繧・
## 6. 蜆ｪ蜈磯・
1. `current\daily_ops_win\shorts_win\config*.json`
2. `current\daily_ops_win\shorts_win` 縺ｮ upload / manage / pipeline scripts
3. `current\daily_ops_win\post_publish\update_shorts.py`
4. `current` 蜷・runbook
5. `next` 縺ｮ token 蜿ら・

## 7. 谺｡縺ｮ菴懈･ｭ

谺｡蝗槭・谺｡縺ｮ鬆・〒騾ｲ繧√ｋ縲・
1. `current\daily_ops_win\shorts_win\config.json` 繧・`D:\MasaoSystem` 蜑肴署縺ｸ蟇・○繧・2. token / prompt / queue path 繧・shared / local data 縺ｸ蛻・ｊ譖ｿ縺医ｋ
3. `post_publish` 縺ｮ token / exclude path 繧貞・繧頑崛縺医ｋ
4. runbook 繧呈眠蝓ｺ貅門・縺ｸ譖ｸ縺肴鋤縺医ｋ
5. 縺昴・蠕後↓ dry-run 繝吶・繧ｹ縺ｧ蜍穂ｽ懃｢ｺ隱阪☆繧・
