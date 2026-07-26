# MasaoSystem Agent Start Here

Updated: 2026-07-10
Status: current

This is the repository entry point. It is intentionally short.

## Required Reads

1. `D:\MD\context\AGENT_START_HERE.md`
2. `D:\MD\context\projects\masao\AGENT_START_HERE.md`
3. `D:\MasaoSystem\docs\current\ABSOLUTE_RULES.md`
4. `D:\MasaoSystem\docs\current\CURRENT_OPERATIONS.md`
5. `D:\MasaoSystem\docs\current\SYSTEM_COMPONENT_MAP.md`
6. Only the task-specific runbook.

Agent ownership and task routing:

```text
D:\MasaoSystem\docs\current\AGENT_ROUTING.md
```

Content and platform policy:

```text
D:\MasaoSystem\docs\current\CONTENT_AND_SNS_POLICY.md
```

## Current Operating Summary

- Live/OBS/PTZ/fallback/sensor operations continue.
- Protect Part 3 night/dinner Live.
- Kodeko routine video publishing is paused.
- Taro Selection video publishing is paused.
- Live chatbot Taro remains a separate component.
- Regular-video routine publishing is paused.
- Main-channel YouTube Shorts continue morning/evening; the hideout experiment targets one daily post at 20:00 JST.
- X, TikTok, Instagram, SNS inventory, and agreed Drive/local delivery continue lightly.

## Absolute Safety Summary

- RAW media is immutable.
- Copy source material to `D:\OBS\REC\work` before editing.
- Do not rename, move, delete, or reorganize warehouse sessions.
- Existing approved sidecar jobs may add only their known analysis artifacts without modifying RAW.
- Do not expose secrets.
- Do not perform YouTube/SNS writes without the required authorization.
- Do not start i5-owned scripts from this PC.
- Do not deploy or restart production components casually during a stream.

The full rules in `ABSOLUTE_RULES.md` override older notes.

## Repository Role

`D:\MasaoSystem` stores intended, reviewable source and documentation.
Runtime may exist under `C:` or `D:\OBS\REC`.
A source edit is not a deployment.

Before a runtime change:

1. Identify the component and runtime owner.
2. Compare source and runtime.
3. Agree on the final state and rollback.
4. Deploy at a safe time.
5. Verify the deployed state.

## Current and Historical Material

- Standing policy belongs under `docs\current`.
- Historical detail belongs in Git history, `docs\archive`, or the context vault.
- Do not append daily analysis to this file.
- Do not delete old material merely because it is not active.

Archive index:

```text
D:\MasaoSystem\docs\archive\ARCHIVE_INDEX.md
```
