# Batch Posting Runbook (WIN_YOLO_PTZ_20S UI)

Last updated: 2026-04-01  
Target: `D:\MasaoSystem\next\shorts_ptz_win\ui\app.py`

## Goal

- Keep the next-line UI operation reproducible.
- Run `candidate selection -> face check -> metadata review -> render -> upload` inside the line.
- Keep `API2`, but let `Codex` step in for metadata when needed.

## Metadata Policy

- Default: `API2 draft -> Codex review -> overwrite if needed`
- Fallback: `API2 only`
- Quality-first: `Codex manual`
- Shared policy: `D:\MasaoSystem\docs\current\METADATA_INTERVENTION_POLICY_2026-04-01.md`

## Standard Template

- Count: `12`
- Span: `4 days`
- Start: `same-day 22:00 JST`
- Daily slots: `22:00,02:00,06:00`
- Duration: `20s`
- Motion target: `around 50`
- Suggested filters:
  - `min motion = 45`
  - `max motion = 55`
  - `target motion = 50`
  - `min hits = 20`

## Review Points

- no clearly visible human face / unwanted person
- no obvious crop failure
- title stays on prompt
- description keeps the intended 4-line structure
- if metadata is weak, overwrite `decision.json` before upload

## Metadata Modes

- Standard: `API2 + Codex review`
- Fallback: `API2 only`
- Manual-strong: `API2 off + Codex manual`
- If not specified, use `Standard`
