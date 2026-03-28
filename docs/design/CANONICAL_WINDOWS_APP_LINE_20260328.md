# Canonical Windows App Line

菴懈・譌･: 2026-03-28

## 1. 逶ｮ逧・
縺薙・譁・嶌縺ｯ縲・譛邨ら噪縺ｫ菫晏ｭ倥＠縺溘＞豁｣隕上Λ繧､繝ｳ縺御ｽ輔°繧貞崋螳壹☆繧九◆繧√・險ｭ險医Γ繝｢縺ｧ縺吶・
縺薙％縺ｧ縺ｯ縲・
- Ubuntu 蜀榊・逅・Λ繧､繝ｳ
- Windows 豁｣隕上Λ繧､繝ｳ

繧呈・遒ｺ縺ｫ蛻・￠縺ｦ謇ｱ縺・∪縺吶・
## 2. 邨占ｫ・
### Ubuntu 蛛ｴ縺ｮ諢丞袖

Ubuntu 邉ｻ縺ｯ縲・閾ｪ蜍戊ｿｽ蟆ｾ蟆主・蜑崎ｳ・肇繧貞・蜃ｦ逅・☆繧九→縺阪・繝ｩ繧､繝ｳ縺ｨ縺励※菫晄戟縺吶ｋ縲・
荳ｻ縺ｪ諤晄Φ:

- `proxy_360.mp4`
- `ﾎ悩`
- API1 縺ｧ `crop_x / start / end`
- API2 縺ｧ `title / description`

### Windows 蛛ｴ縺ｮ豁｣隕上Λ繧､繝ｳ

譛邨よｭ｣隕上Λ繧､繝ｳ縺ｯ縲・Ubuntu 縺ｮ諤晄Φ繧貞ｼ輔″邯吶℃縺､縺､縲・API1 繧偵Ο繝ｼ繧ｫ繝ｫ YOLO 縺ｫ鄂ｮ縺肴鋤縺医◆繧ゅ・縺ｧ縺吶・
縺､縺ｾ繧頑ｭ｣隕上Λ繧､繝ｳ縺ｯ谺｡縺ｧ縺吶・
`motion derived candidate`
-> `local YOLO based selection / crop`
-> `API2 for metadata`
-> `render`
-> `upload`

## 3. Ubuntu 縺ｧ荳崎ｦ√↓縺ｪ繧九ｂ縺ｮ

Windows 豁｣隕上Λ繧､繝ｳ縺ｫ遘ｻ縺吶→縺阪・Ubuntu 蛛ｴ縺ｧ荳崎ｦ√↓縺ｪ繧倶ｸｭ蠢・・谺｡縺ｧ縺吶・
- API1 繧貞娼縺・※ `crop_x / start / end` 繧呈ｱｺ繧√ｋ莉慕ｵ・∩

逅・罰:

- 縺昴・蠖ｹ蜑ｲ繧・Windows 豁｣隕上Λ繧､繝ｳ縺ｧ縺ｯ local YOLO 縺梧球縺・◆繧・
## 4. 豁｣隕上Λ繧､繝ｳ縺ｮ螳滉ｽ・
菫晏ｭ伜・縺ｮ蝓ｺ貅・

- `D:\MasaoSystem\current\daily_ops_win\shorts_win`

縺薙・繝輔か繝ｫ繝繧偵・Windows app 蛹悶＆繧後◆豁｣隕上Λ繧､繝ｳ縺ｮ菫晏ｭ伜・縺ｨ縺励※謇ｱ縺・・
## 5. 豁｣隕上Λ繧､繝ｳ縺ｮ荳ｻ隕∵ｧ区・

### app entry

- `launch_ui.ps1`
- `ui\app.py`

### stage 1: candidate generation

- `scripts\build_candidates_win.py`

諢丞袖:

- `raw_yolo.jsonl` 縺九ｉ 20 遘貞呵｣懊ｒ菴懊ｋ
- motion 蛟､縺ｨ hits 繧呈戟縺､

### stage 2: global pick

- `scripts\pick_global_candidates_win.py`

諢丞袖:

- 蛟呵｣懊°繧・event queue 繧剃ｽ懊ｋ

### stage 3: local YOLO based crop + API2

- `scripts\run_event_queue_pipeline_yolo_win.py`

諢丞袖:

- `raw_yolo.jsonl` 縺ｮ荳ｭ蠢・､縺九ｉ crop 繧呈ｱｺ繧√ｋ
- preview 繧貞・縺・- API 縺ｯ content/metadata 蛛ｴ縺ｫ髯仙ｮ壹＠縺ｦ菴ｿ縺・
驥崎ｦ・

- 縺薙・繝ｩ繧､繝ｳ縺ｧ縺ｯ crop 豎ｺ螳壹↓ API1 繧剃ｽｿ繧上↑縺・- local YOLO 繝吶・繧ｹ縺ｧ crop 繧呈ｱｺ繧√ｋ

### stage 4: upload

- `scripts\upload_from_queue_win.py`

## 6. API 縺ｮ蠖ｹ蜑ｲ謨ｴ逅・
### Ubuntu 蜀榊・逅・Λ繧､繝ｳ

- API1:
  - `crop_x`
  - `start_sec`
  - `end_sec`
- API2:
  - `title`
  - `description`

### Windows 豁｣隕上Λ繧､繝ｳ

- local YOLO:
  - 蛟呵｣懃函謌・  - selection 陬懷勧
  - crop 菴咲ｽｮ豎ｺ螳・- API2 逶ｸ蠖・
  - `title`
  - `description`

陬懆ｶｳ:

- 螳溯｣・ｸ翫・ `api_decision_pipeline.py --step 2` 繧剃ｽｿ縺・ｽ｢縺檎樟蝨ｨ縺ｮ譛ｬ邱・- 縺励◆縺後▲縺ｦ縲窟PI1 繧呈ｮ九＠縺・full Ubuntu logic縲阪ｒ豁｣隕上Λ繧､繝ｳ縺ｫ謖√■霎ｼ縺ｾ縺ｪ縺・
## 7. 縺・∪縺ｮ險ｭ險亥愛譁ｭ

莉雁ｾ後・謨ｴ逅・〒縺ｯ縲∵ｬ｡繧貞崋螳壹☆繧九・
1. Ubuntu 譌ｧ繝ｩ繧､繝ｳ縺ｯ蜀榊・逅・ｰら畑 legacy
2. Windows current 縺ｯ豁｣隕上Λ繧､繝ｳ
3. 豁｣隕上Λ繧､繝ｳ縺ｮ譛ｬ雉ｪ縺ｯ
   - Ubuntu 縺ｮ諤晄Φ繧剃ｿ昴▽
   - API1 繧・local YOLO 縺ｫ鄂ｮ縺肴鋤縺医ｋ
4. 菫晏ｭ伜・縺ｯ `D:\MasaoSystem\current\daily_ops_win\shorts_win`

## 8. 谺｡縺ｫ繧・ｋ縺薙→

1. `current\daily_ops_win\shorts_win` 縺ｮ config/path 繧呈眠蝓ｺ貅門・縺ｸ蟇・○繧・2. `ui\app.py` / `launch_ui.ps1` 繧呈ｭ｣隕丞・蜿｣縺ｨ縺励※謇ｱ縺・3. `api_decision_pipeline.py` 縺ｮ step 2 萓晏ｭ倥ｒ謨ｴ逅・☆繧・4. runbook 繧偵袈buntu 蜀榊・逅・阪→縲係indows 豁｣隕上Λ繧､繝ｳ縲阪〒蛻・￠繧・
