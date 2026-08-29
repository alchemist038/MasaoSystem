# Masao System Component Map

Updated: 2026-07-10
Status: current

This map separates desired source, runtime state, historical context, source media, and delivery artifacts.

## Layer Model

| role | canonical location | rule |
| --- | --- | --- |
| Design, reviewable code, runbooks | `D:\MasaoSystem` | Git-managed intended state |
| Production runtime and control plane | `C:\...`, `D:\OBS\REC` | Confirm before deploy or restart |
| Decisions, analysis, handoffs | `D:\MD\context` | Context and reasoning, not runtime truth |
| Canonical source media | `E:\masaos_mov` | RAW media is immutable |
| Server/archive source media | `\\masao-n8n\MASAO_RAW\masaos_mov` | Read-only source/archive access |
| Editing and generated output | `D:\OBS\REC\work` | All manual media work happens here |
| Phone-posting delivery | `G:\マイドライブ\Masao_SNS` | Completed deliverables only |

## Components

| component | Git/design source | runtime or data path | owner/status | boundary |
| --- | --- | --- | --- | --- |
| Live helpers | `D:\MasaoSystem\current\daily_ops_win\live_ops` | `C:\Users\alche\Desktop\OBS\scripts` | Live management; active | Deploy source to runtime only after approval |
| OBS schedule | `live_ops\obs_scripts` | OBS script runtime on `C:` | Active | No casual changes during stream |
| Camera fallback | `live_ops\fallback` | OBS script runtime on `C:` | Active | Use the correct Jikka/Shataku preset |
| Room sensor overlay | `D:\MasaoSystem\current\daily_ops_win\live_overlays\masao_room_sensor` | `D:\OBS\REC\overlays\masao_room_sensor` | Active | Hub/Cloud method; secrets stay in environment variables |
| PTZ / V7 | Separate repository/runtime | `C:\masao_ptz` | PTZ lane; active | Do not absorb into Shorts or OBS trees |
| Live chatbot | Separate i5 runtime | Remote chatbot runtime | i5-side agent; active separately | No remote start/stop from this PC |
| Current Shorts code line | `D:\MasaoSystem\current\daily_ops_win\shorts_win` | `D:\OBS\REC\scripts\youtube\yolo\WIN` | Code retained; routine high-volume publishing is not current policy | Do not assume upload authorization |
| Post-publish tools | `D:\MasaoSystem\current\daily_ops_win\post_publish` | `D:\OBS\REC\work` utilities | On-demand | Public writes require target approval |
| Historical reprocessing | `D:\MasaoSystem\current\historical_reprocess_win` | Local helper runtime | On-demand | RAW read-only; output outside warehouse |
| Kodeko regular/daily video | Workflow docs and work scripts | `D:\OBS\REC\work` | Paused | No routine generation or publication |
| Taro Selection video | Workflow docs and work scripts | `D:\OBS\REC\work` | Paused | Chatbot Taro is a different component |
| SNS clip inventory | Context ledger, used-scenes list, gallery | `D:\MD\context\projects\masao` | Active | Structured dedupe before delivery |
| SNS delivery | Delivery workflow | `G:\マイドライブ\Masao_SNS\YYYY-MM-DD` | Active | Finished assets only; no RAW |
| Analytics | Context analysis scripts and Studio exports | `D:\MD\context`, `D:\OBS\REC\work\studio_exports` | Read/analysis lane | Prefer CSV; protect API quota |

## Source-to-Runtime Rule

- Git describes the intended implementation where a component has been migrated.
- Runtime paths describe what is actually running.
- A component is not considered deployed merely because Git changed.
- Deployment requires a diff, explicit approval, a safe time, post-copy verification, and a rollback path when practical.
- Runtime-only secrets and state never flow back into Git.

## Media Flow

```text
C:\OBS_TEMP
  -> approved capture/post-processing flow
  -> E:\masaos_mov canonical session
  -> read/copy only for agents
  -> D:\OBS\REC\work for editing
  -> G:\マイドライブ\Masao_SNS for completed SNS delivery
```

See `ABSOLUTE_RULES.md` for the exact RAW and sidecar exception rules.
