# Windows Migration Acceptance

Date: 2026-03-28

## Goal

The final goal of the Windows migration is:

- Historical assets can be reused on Windows
- Output quality is equal to or better than the old line
- Old copy-paste defects and stitched-together implementation issues may be fixed during migration

In short:

- Preserve the philosophy
- Do not preserve accidental implementation defects

## What Is Considered Essential

- File-based state management
- Queue-based stage separation
- Session-oriented artifact layout
- Re-runnable processing
- Ability to regenerate shorts from past assets
- Practical quality of crop, metadata, render, and upload-ready output

## What Is Not Considered Sacred

- Copy-paste leftovers
- Half-migrated helper calls
- Duplicate scripts with overlapping responsibility
- Hard-coded paths
- Transitional glue that existed only to keep the old line moving
- Structural inconsistency caused by ad hoc fixes

These may be normalized or replaced in the Windows line.

## Migration Principle

When an old script contains both:

- a useful idea
- and a messy implementation

we should keep the idea and rewrite the implementation if needed.

## Acceptance Criteria

Windows migration is acceptable when the following are true for historical assets:

1. Candidate extraction is at least as usable as the old line.
2. Clip framing and crop stability are equal to or better than the old line.
3. Metadata generation is equal to or better than the old line.
4. Final short rendering quality is equal to or better than the old line.
5. Queue/state behavior remains restart-safe and traceable.
6. The process can be run without depending on Ubuntu-specific path assumptions.

## Practical Evaluation View

For old sessions, compare Ubuntu-output expectations and Windows-output results from these angles:

- event selection quality
- crop positioning quality
- title / description usefulness
- render completeness
- reproducibility after rerun

If Windows is cleaner internally and equal or better in result quality, migration is successful.

## Working Rule For Refactoring

During Windows migration:

- Fix structural oddities freely
- Consolidate duplicated logic where helpful
- Prefer config-driven paths
- Prefer self-contained scripts over hidden cross-file dependencies
- Prefer one canonical chain over multiple near-duplicate bridges

## Canonical Outcome

The target is not:

- "preserve every old script exactly"

The target is:

- "preserve the ability to reuse past assets at the same or better quality on a cleaner Windows-native line"
