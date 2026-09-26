# Masao System Agent Instructions

Read these before changing this repository:
1. `docs/current/ABSOLUTE_RULES.md`
2. `docs/current/CURRENT_OPERATIONS.md`
3. `docs/current/AGENT_ROUTING.md`
4. `docs/current/SYSTEM_COMPONENT_MAP.md`
5. The task-specific runbook and `D:\MD\context\.okf\governance\task-protocol.md`.

This Git repository describes intended source and policy, not deployed runtime.
Do not deploy, restart a component, change schedules, or write public/API state
just because source or documentation changed. Obtain the agreed authorization
and verify the current target.

E: is protected across projects. Do not modify, rename, move, delete, or
reorganize its contents. RAW/canonical media remains immutable. Only the
existing approved ingest/sidecar flow retains its narrow exception; this file
does not authorize new warehouse writes.

Preserve existing user changes and accumulated decisions/ledgers. Keep secrets,
RAW, generated media, and runtime-only state out of Git. Stage explicit paths,
never the entire working directory. Do not switch a shared working tree's
branch to do unrelated work.

Use `D:\MD\context\projects\masao\AGENT_START_HERE.md` and OKF for context.
Dated notes are history; inspect the actual runtime before claiming it is active.
The chatbot belongs to its current remote host's agent, not necessarily i5.
Do not start or recover remote scripts from this PC.
