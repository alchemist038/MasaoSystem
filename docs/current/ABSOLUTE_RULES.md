# Masao System Absolute Rules

Updated: 2026-07-10
Status: current / highest priority

This document defines the non-negotiable rules for Masao system work.
If an older memo or runbook conflicts with this file, stop and follow this file until the conflict is resolved.

## 1. Work Permission Model

| operation | default permission | condition |
| --- | --- | --- |
| Read local files, logs, manifests, and process state | allowed | Read-only only |
| View YouTube Studio and download CSV exports | allowed | Do not change public state |
| Small YouTube API read | conditionally allowed | Use the intended read/analysis project and protect quota |
| Large API scan, continuous polling, or full catalog read | approval required | Confirm scope, count, period, project quota, and stop condition |
| Existing approved automation | allowed within its standing scope | Changing settings or scope requires approval |
| YouTube API write | explicit approval required | Present exact targets and final state before execution |
| Public SNS post | explicit approval required | Confirm account, media, text, timing, and destination |
| Runtime deploy, restart, or configuration change | explicit approval required | Do not perform casually during an active stream |
| Delete a video, playlist item, comment, source file, or production asset | prohibited by default | Requires itemized, explicit approval; irreversible operations need separate confirmation |
| Start or recover i5-side scripts from this PC | prohibited | Use the i5-side agent/runtime |
| Expose or store secrets | prohibited | Never print or commit tokens, cookies, passwords, OAuth codes, or stream keys |

## 2. RAW Media Is Immutable

RAW media is never edited in place.

Protected locations and media include:

```text
E:\masaos_mov
\\masao-n8n\MASAO_RAW\masaos_mov
raw.mkv
proxy_360.mp4
source recordings and canonical session media
```

Allowed:

- Read and inspect.
- Analyze without writing to the source media.
- Copy required material to a work area.

Prohibited:

- Overwrite or edit RAW media.
- In-place transcode or re-encode.
- Rename, move, delete, or reorganize canonical sessions.
- Write rendered clips, previews, thumbnails, or temporary files into the warehouse.
- Treat the warehouse as a general work folder.

All manual editing and generated outputs belong under:

```text
D:\OBS\REC\work
```

The existing scheduled capture flow may move a completed recording from `C:\OBS_TEMP` into the canonical warehouse. Existing approved post-processing jobs may add their known sidecar artifacts, such as YOLO results, candidate JSON, and completion markers, without changing RAW media. This is the only standing warehouse-write exception. Agents must not add new warehouse writes without explicit approval.

## 3. YouTube API Read Rules

Read-only checks are allowed when they do not change public state and do not endanger quota.

Typical allowed reads:

- Channel, video, playlist, and live-broadcast status.
- View count, subscriber count, publish time, and metadata inspection.
- Post-write verification for an already approved operation.
- Google Cloud Console quota inspection.
- YouTube Studio inspection and CSV export.

Prefer Studio CSV for broad analytics. Do not use Chatbot Read A/B or Live Ops credentials for ad-hoc investigation. Large catalog scans require a quota check and an agreed target range.

## 4. YouTube API Write Rules

The following require explicit execution authorization:

- Upload, schedule, publish, or change video visibility.
- Change a title, description, thumbnail, publish time, or monetization-related setting.
- Create, update, bind, transition, or complete a live broadcast.
- Add, remove, or reorder playlist items.
- Post, reply to, pin, unpin, or delete comments.
- Change the channel description or other public channel metadata.
- Delete videos, broadcasts, playlists, or comments.

Before execution, establish:

1. Channel/account.
2. Target resource IDs and count.
3. Exact requested changes.
4. Visibility and publish/schedule state.
5. Date, time, and timezone.
6. Exclusions and things not to touch.
7. Verification and rollback method where possible.

Once the user authorizes the agreed scope, complete that scope end-to-end and verify it. Do not expand the target set or introduce another public change without new authorization.

A clear daily instruction such as `朝配信の準備して` may authorize the normal day-scoped live-prep flow when the date, three-part structure, privacy, and defaults are already established. It does not authorize unrelated metadata or channel changes.

## 5. YouTube API Quota Protection

Quota is evaluated per Google Cloud project, not per OAuth token.

Priority:

1. Live Ops / OBS.
2. Video upload and scheduled video operations.
3. Chatbot write primary.
4. Chatbot Read A.
5. Chatbot B reserve.
6. Shorts auto comment.
7. Ad-hoc analytics, catalog scans, and experiments.

Thresholds:

| project usage | action |
| --- | --- |
| over 70% | Stop new large API investigations |
| over 80% | Stop auto comments, metric polling, and inventory scans |
| over 90% | Preserve only Live Ops and the minimum approved posting/write operations |

## 6. Runtime and Machine Boundaries

- Do not deploy or restart OBS schedule, PTZ, fallback, sensor, or chatbot components during an active stream unless the user explicitly approves the exact intervention.
- Do not start, stop, or recover Chatbot Read A/B or other i5-owned scripts from this PC or through a UNC path.
- Use the i5-side agent for i5 runtime actions. This PC may perform read-only health checks when available.
- Keep `C:\masao_ptz` independent from Shorts and OBS repositories.
- Keep chatbot runtime independent from the local content-production tree.
- Preserve user changes and uncommitted Git work. Never reset or overwrite them casually.

## 7. Secrets and Public Artifacts

Never place the following in Markdown, Git, ZIP handoffs, screenshots, or chat:

- OAuth tokens.
- API keys.
- Cookies or browser profiles.
- Passwords or private RTSP credentials.
- Stream keys.
- Authentication codes.

Use role aliases, environment-variable names, and sanitized example configs instead.

## 8. Historical and Public-State Safety

- A new template applies to future content by default.
- Do not bulk-edit historical videos, live archives, playlists, or channel metadata unless the exact target list is approved.
- Archive old documentation before replacing an entry point.
- Do not delete old scripts or notes merely because a new LLM can regenerate them.
- Preserve reasoning, decisions, worldview, boundaries, and incident history even when implementation code is replaced.
