# MasaoSystem

Updated: 2026-07-10

`D:\MasaoSystem` is the Git-managed source and design repository for the Masao operating system.
It stores reviewable scripts, runbooks, policies, examples, and component maps.
It is not the RAW warehouse and it is not automatically the same as the currently deployed runtime.

## Start Here

Read in this order:

1. `D:\MD\context\AGENT_START_HERE.md`
2. `D:\MD\context\projects\masao\AGENT_START_HERE.md`
3. `D:\MasaoSystem\docs\current\ABSOLUTE_RULES.md`
4. `D:\MasaoSystem\docs\current\CURRENT_OPERATIONS.md`
5. The runbook for the component being handled.

Repository-specific entry:

```text
D:\MasaoSystem\docs\current\AGENT_START_HERE.md
```

## Current Position

- YouTube Live remains active, with Part 3 night/dinner as the core slot.
- Kodeko routine daily/regular video production is paused.
- Taro Selection video production is paused.
- Existing live chatbot Taro is a separate component and is not stopped by the video-production pause.
- YouTube regular-video routine publishing is paused.
- YouTube Shorts is a limited experiment, approximately one post every two days.
- X, TikTok, Instagram, SNS inventory, and Drive delivery continue as lightweight operations.

See `docs\current\CURRENT_OPERATIONS.md` for the complete current table.

## Repository Layout

```text
current/
  daily_ops_win/
    live_ops/
    live_overlays/
    post_publish/
    shorts_win/
  historical_reprocess_win/
next/
  shorts_ptz_win/
docs/
  current/
  archive/
  design/
  migration/
  public/
  reference/
shared/
```

## Source and Runtime

| role | location |
| --- | --- |
| Git-managed intended source | `D:\MasaoSystem` |
| OBS/production control and work | `D:\OBS\REC` |
| Hot runtime and temporary capture | `C:\...`, `C:\OBS_TEMP` |
| PTZ runtime/repository | `C:\masao_ptz` |
| Canonical media warehouse | `E:\masaos_mov` |
| Context and decision history | `D:\MD\context` |
| SNS delivery | `G:\マイドライブ\Masao_SNS` |

Component-specific source/runtime relationships are defined in:

```text
D:\MasaoSystem\docs\current\SYSTEM_COMPONENT_MAP.md
```

## Non-Negotiable Rules

- RAW media is immutable. Read or copy it; never edit it in place.
- Manual editing and generated outputs belong in `D:\OBS\REC\work`.
- Do not expose or commit tokens, keys, cookies, passwords, or stream keys.
- YouTube/SNS public writes require the permission defined in `ABSOLUTE_RULES.md`.
- Do not start or recover i5-owned chatbot scripts from this PC.
- Do not deploy runtime changes merely because Git changed.
- Do not overwrite uncommitted user changes.

## Deployment

Some components use Git as their source and a separate production copy as runtime.
Before deployment:

1. Confirm the exact component and intended final state.
2. Compare source and runtime.
3. Confirm the stream is at a safe point.
4. Deploy only the agreed files.
5. Verify runtime state and retain a rollback path.

Live helper deployment details:

```text
D:\MasaoSystem\current\daily_ops_win\live_ops\docs\DEPLOY.md
```

## Archive

Current documents stay short. Older entry documents, detailed investigations, and superseded designs are preserved through Git history and:

```text
D:\MasaoSystem\docs\archive\ARCHIVE_INDEX.md
```

Do not place RAW media, generated media, secrets, or browser state in the documentation archive.

