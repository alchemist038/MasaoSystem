# PIPELINE_ORIGIN_AND_TRIAGE_20260328

Date: 2026-03-28

## 1. This memo

This memo fixes two things in one place:

1. Why the current structure was born
2. What should be kept, recorded only, or retired

The purpose is not to preserve every old script.
The purpose is to preserve the useful structure and rebuild it cleanly on Windows.

## 2. Origin of the structure

### 2.1 Why DB was not used

The starting point was simple:

- DB was not familiar
- The system had to be understandable from Explorer
- State had to be visible with folders and files

That is why the system started as:

- session folders
- marker files
- JSONL queues
- visible artifacts

This was not theory-first design.
It started as a practical way to make the system understandable.

But the result has lasting value:

- humans can read status quickly
- scripts can read the same state
- recovery is easier
- inventory can be seen without opening a database

So the origin was "I did not want to depend on a DB I did not understand",
but the value now is "file-based state is visible and robust enough for this project".

### 2.2 Why API1 and API2 were separated

API1 and API2 were split for practical reasons:

- reduce API cost
- separate responsibilities completely
- reduce AI confusion
- make outputs easier to inspect stage by stage

Role split:

- API1:
  - crop_x
  - start / end
  - framing decision
- API2:
  - title
  - description
  - metadata language task

The intention was:

- do not let one AI prompt decide everything at once
- keep visual selection and language generation separate
- avoid paying for a larger mixed judgment than necessary

This was a real operational design choice, not an accident.

### 2.3 Why the folder structure looks the way it does

The folder structure came from the need to understand progress at a glance.

Important examples:

- `E:\masaos_mov\<SESSION>`
  - one recording unit
- `frames_360\<EVENT>`
  - inventory shelf
- `events\<EVENT>`
  - processing side for the same inventory item
- `.analyze_done`
  - analyze complete
- `.published`
  - upload complete

This means:

- session is the natural work container
- frames are stock
- events are consumed stock
- marker files make state visible without extra tools

### 2.4 Why this still matters now

Even though the project is moving toward a cleaner Windows-native line,
these ideas still matter:

- visible state
- stage separation
- restart safety
- low-spec friendly operation
- Explorer-readable inventory

So we should keep the ideas and fix the messy parts.

## 3. Canonical direction now

The canonical daily line is no longer:

- DeltaY -> API1 -> API2 as the main production line

The canonical daily line should become:

- candidate / motion based detection
- local YOLO selection and crop
- API2 for metadata
- render
- upload

At the same time, the old 360 / DeltaY asset world still matters as a source of historical inventory.

So the project now has two different values:

- operational canonical line:
  - Windows YOLO line
- historical memory and reprocess reference:
  - old Ubuntu / API1 line

## 4. Three-way classification

### A. Keep

These should remain in the rebuilt system as living structure or living logic.

- `E:\masaos_mov` style session-based inventory model
- Explorer-readable file-based state
- `frames_360` as inventory
- `events` as consumed / processing side
- marker files such as:
  - `.analyze_done`
  - `.published`
  - `.yolo_done`
  - `.crop_done`
- JSONL queue thinking
- stage separation:
  - candidate
  - pick
  - event queue
  - upload queue
- Windows YOLO canonical line:
  - candidate generation
  - global pick
  - local YOLO crop
  - API2 metadata
  - render
  - upload
- historical asset reuse as a requirement
- quality goal:
  - same or better output than old assets produced before

### B. Keep As Record Only

These do not need to survive as active production code, but the memory must remain in MD and examples.

- why API1 and API2 were split
- why DB was avoided at the beginning
- why session / frames_360 / events became the structure
- the old Ubuntu pre-PTZ line as design history
- API1-era responsibilities:
  - crop_x
  - start / end decision
- old request / response artifact layout under `api`
- the meaning of old `yolo\v1` markers
- old queue flow documents
- old runbook logic, if it helps explain the pipeline lineage

In other words:

- keep the knowledge
- do not require the old implementation to stay canonical

### C. Can Be Retired Or Rewritten Freely

These are not sacred and may be removed, merged, or rewritten during Windows migration.

- hard-coded Linux paths
- cross-file helper dependencies created by copy-paste migration
- half-migrated bridge scripts
- duplicate scripts with almost the same job
- old API1 production dependency in the daily line
- accidental folder duplication
- ad hoc transitional glue that only existed to keep the old line moving
- implementation quirks caused by "patching while running"

Important:

- this category does not mean the idea was bad
- it means the implementation shape is not worth preserving

## 5. Practical interpretation

If something belongs to the old system, ask three questions:

1. Is this a core idea?
2. Is this only an old implementation artifact?
3. Do we need it to reproduce old quality on Windows?

Decision rule:

- if it is a core idea and still useful:
  - Keep
- if the idea matters but the code no longer needs to live:
  - Keep As Record Only
- if it is mostly transitional glue:
  - Retire Or Rewrite

## 6. Current judgment for this project

### Keep

- Windows YOLO selection pipeline
- file-based inventory/state model
- session/event folder logic
- queue and marker based operation
- historical asset reuse requirement

### Keep As Record Only

- API1 split rationale
- API1-era folder semantics
- Ubuntu pipeline history
- old design reasons behind file-based state

### Retire Or Rewrite

- API1 as a required step in the daily canonical line
- messy duplicated bridge implementations
- Linux-specific path assumptions
- structurally inconsistent copy-paste code

## 7. Final design stance

The target is:

- preserve the philosophy
- preserve the inventory/state readability
- preserve the ability to reuse old assets
- preserve or improve output quality

The target is not:

- preserve every old implementation detail

Short version:

- keep the thinking
- keep the visible state model
- keep the YOLO line
- record API1 history
- rewrite the messy parts
