# Masao Agent Routing

Updated: 2026-08-30
Status: current

## Startup Order

1. `D:\MD\context\AGENT_START_HERE.md`
2. `D:\MD\context\projects\masao\AGENT_START_HERE.md`
3. `D:\MasaoSystem\docs\current\ABSOLUTE_RULES.md`
4. `D:\MasaoSystem\docs\current\CURRENT_OPERATIONS.md`
5. Only the runbook for the task being performed.

Do not load the complete historical archive for ordinary work.

## Work Modes

| user language | mode | permitted action |
| --- | --- | --- |
| `確認`, `調査`, `分析`, `表示` | READ | Inspect and report; do not change public or runtime state |
| `提案`, `方針`, `案を出して` | PROPOSE | Design the final state; do not execute writes |
| `実行`, `変更して`, `投稿して` after target agreement | EXECUTE | Complete only the agreed scope and verify it |

Destructive or irreversible actions require itemized confirmation even when the general word `実行` was used.

## Agent Lanes

| lane | responsibility | primary references | boundary |
| --- | --- | --- | --- |
| Channel analysis | Studio, CSV, API reads, Shorts/regular/Live/SNS analysis | Latest analysis notes and quota policy | Read-only; no metadata changes |
| Live management | Daily 04:00 duplicate-safe Live reservation pass and manifest handoff; OBS, schedule, PTZ checks, sensor, chat docks only after separate preparation authorization | `RUNBOOK_morning_live_prep.md` | The standing heartbeat may reserve and verify the three frames only; runtime preparation and start remain separate |
| SNS clip management | Daily 04:30 guarded generation, posting, related-Live readback, selection, editing, dedupe, gallery, and delivery | SNS management start, ledger, used-scenes list | The standing heartbeat runs only from a complete same-day Live manifest; otherwise stop the affected YouTube post |
| X operation | Live-start text, current-Masao reply, X analytics | X workflow and recent X logs | Do not silently absorb general SNS inventory work |
| i5 agent | Chatbot Read A/B and i5-owned runtime | i5 runtime/runbook | This PC does not start or recover it |
| System maintenance | Git source, component map, deploy checks, runbooks, and the daily 05:15 read-only cross-check | `D:\MasaoSystem` current docs | The cross-check reports gaps to the owning lane; it does not auto-repair runtime, schedules, files, or public state |

## Character Roles

- Masao: subject and center of the channel.
- Oton: owner and final decision maker.
- GPT Goro: organization, progress, and overall guidance.
- GPT Taro: words, descriptions, and live chatbot behavior. The paused Taro Selection video is a separate production line.
- Kodeko: investigation, generation support, QA, and documentation. Routine Kodeko video publishing is paused.

Character identity does not grant technical permission. Permissions come from the work mode and component boundary.

## Handoff Requirements

Every meaningful execution handoff should state:

- Objective and approved scope.
- Files, resource IDs, platforms, dates, and count.
- What changed.
- What was intentionally not touched.
- Verification result.
- Remaining risks or manual actions.

Never include secret values in a handoff.
