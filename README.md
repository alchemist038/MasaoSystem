# MasaoSystem

譖ｴ譁ｰ譌･: 2026-03-28

## 1. 縺薙・繝輔か繝ｫ繝縺ｮ蠖ｹ蜑ｲ

`D:\MasaoSystem` 縺ｯ縲・譛ｬ逡ｪ `D:\OBS\REC` 繧貞｣翫＆縺壹↓蜀肴ｧ狗ｯ峨ｒ騾ｲ繧√ｋ縺溘ａ縺ｮ譁ｰ縺励＞蝓ｺ貅悶ヵ繧ｩ繝ｫ繝縺ｧ縺吶・
縺薙％縺ｧ縺ｯ遘ｻ蜍輔〒縺ｯ縺ｪ縺上さ繝斐・縺ｧ謨ｴ逅・ｒ騾ｲ繧√∪縺吶・譛ｬ逡ｪ current 縺ｯ蠑輔″邯壹″ `D:\OBS\REC` 蛛ｴ縺ｫ縺ゅｊ縺ｾ縺吶・
## 2. 迴ｾ蝨ｨ縺ｮ迥ｶ諷・
### 繧ｳ繝斐・貂医∩

- `current\daily_ops_win`
  - groups the two daily-used Windows lines
- `current\daily_ops_win\shorts_win`
  - source: `D:\OBS\REC\scripts\youtube\yolo\WIN`
- `current\historical_reprocess_win`
  - source: Windows-native rebuild of old analyze/enqueue upstream line
- `current\daily_ops_win\post_publish`
  - source: `D:\OBS\REC\work`
- `next\shorts_ptz_win`
  - source: `D:\OBS\REC\scripts\WIN_YOLO_PTZ_20S`
- `shared\keys`
  - source: `D:\OBS\REC\keys`
- `shared\bgm`
  - source: `D:\OBS\REC\bgm`
- `shared\prompts`
  - source: `D:\OBS\REC\prompts`
- `shared\models`
  - source: `D:\OBS\REC\models`
- `docs\*`
  - source: `D:\OBS\REC` 縺ｮ謨ｴ逅・枚譖ｸ鄒､

### 縺ｾ縺遨ｺ

- `legacy\linux_shared`
- `legacy\old_win_bridge`
- `research`
- `archive`

## 3. 驥崎ｦ√↑繝ｫ繝ｼ繝ｫ

- 譛ｬ逡ｪ `D:\OBS\REC` 縺ｯ縺ｾ縺 current 縺ｮ豁｣譛ｬ
- 縺薙％縺ｧ縺ｯ蜑企勁繧・ｧｻ蜍輔・縺励↑縺・- 縺ｾ縺・path 縺ｨ config 繧呈紛逅・☆繧・- queue 縺ｯ current 縺ｨ豺ｷ蝨ｨ縺輔○縺ｪ縺・- `E:\masaos_mov` 縺ｯ蜈ｱ譛牙牙ｺｫ縺ｮ縺ｾ縺ｾ菴ｿ縺・- `C:\masao_ptz` 縺ｨ `Z:\chatbot_v4` 縺ｯ蜷ｸ蜿弱＠縺ｪ縺・
## 4. 谺｡縺ｫ繧・ｋ縺薙→

1. `current\daily_ops_win\shorts_win` 縺ｮ path 萓晏ｭ倥ｒ豢励＞蜃ｺ縺・2. `shared` 繧貞盾辣ｧ縺吶ｋ config 縺ｸ蟇・○繧・3. queue 縺ｨ logs 縺ｮ譁ｰ邉ｻ蟆ら畑繝代せ繧貞・繧・4. 譁ｰ蝓ｺ貅門・縺ｧ襍ｷ蜍輔Λ繝・ヱ繧剃ｽ懊ｋ
5. 譁ｰ蝓ｺ貅門・縺縺代〒蜍穂ｽ懃｢ｺ隱阪☆繧・
## 5. 蜿り・枚譖ｸ

- `docs\design\CANONICAL_WINDOWS_APP_LINE_20260328.md`
- `docs\migration\SYSTEM_COPY_MAP_20260328.md`
- `docs\migration\PATH_REWRITE_PLAN_20260328.md`
- `docs\migration\REBUILD_MASTER_PLAN_20260327.md`
- `docs\public\GITHUB_PUBLIC_RELEASE_GOAL_20260328.md`

## Latest Update 2026-03-28

- regrouped the two daily-used Windows lines under `current\daily_ops_win`
- moved `shorts_win` and `post_publish` into that folder
- kept `historical_reprocess_win` separate as a helper line

