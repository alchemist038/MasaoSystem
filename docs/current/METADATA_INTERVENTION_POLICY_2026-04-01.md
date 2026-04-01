# Metadata Operation Policy (Keep API2 + Codex Review)

Last updated: 2026-04-01

## Policy

- Keep the `API2` line alive; do not remove it.
- Let `Codex` review title / description quality and step in when needed.
- Preserve an `API2 only` fallback mode for emergencies and rollback safety.

## Default Mode

- Recommended flow: `API2 draft -> Codex review -> overwrite if needed`
- Let `API2` create `decision.json` first.
- Then review `review JPEG` and `decision.json`.
- If title / description feels weak or off-prompt, overwrite `decision.json` before upload.

## Operation Modes

### 1. Standard

- `API2 + Codex review`
- Use this by default.
- Best balance of speed and quality.

### 2. Fallback

- `API2 only`
- Use when Codex is unavailable.
- Keep at least a lightweight human visual check.

### 3. Manual-Strong

- `API2 off + Codex manual`
- Use `--no-api`, or manually replace `decision.json` before upload.
- Best when metadata quality matters more than speed.

## Default Decision

- If not specified, use `Standard`.
- In practice: keep `API2`, but let `Codex` review the metadata.

## What Codex Reviews

- Human face / unwanted person visibility
- Broken crop or obviously bad review JPEGs
- Title shape matches the prompt
- Description keeps the intended 4-line structure
- English reaction line is not too weak
- The scene stays centered on Masao

## Intervention Timing

- `decision.json` review before render / upload
- final check before upload
- post-publish metadata fix for already scheduled videos

## Practical Rules

- If metadata is corrected, sync it back to the source event `events/<event>/api/v*/decision.json`
- Keep review outputs in `work/*.json` or line-local `data/*.json` when useful
- Apply the same policy to both the current line and the next line
