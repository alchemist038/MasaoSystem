# PTZ V07 Default Switch 2026-04-14

## Decision

- `C:\masao_ptz` production tracker default model was switched from `masao_V06.pt` to `masao_V07.pt`
- `masao_V06.pt` is still kept locally as the rollback weight

## Why

- V07 was trained to reduce split upper/lower box behavior on low posture and flop-like rabbit poses
- live tracking was reported stable after deployment testing
- direct comparison on the V07 flop validation subset showed the main target improvement:
  - multi-pred frames `52 -> 15`
  - IoU50 rate `83.56% -> 91.78%`
  - IoU75 rate `72.60% -> 76.71%`

## Relevant Files

- runtime tracker:
  - `C:\masao_ptz\prod\track_masao_ptz_v5_ui.py`
- runtime weights:
  - `C:\masao_ptz\masao_V07.pt`
  - `C:\masao_ptz\masao_V06.pt`
- training run:
  - `D:\yolo_train\runs\masao_v07_flopfix_ft1_20260412`
- compare memo:
  - `D:\OBS\REC\work\YOLO_V6_V7_COMPARE_20260413.md`

## Notes

- This is a runtime-default change, not a deletion of V06
- public/reference docs that still mention `masao_V06.pt` should now be read as historical unless updated later
