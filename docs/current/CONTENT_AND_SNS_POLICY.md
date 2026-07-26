# Masao Content and SNS Policy

Updated: 2026-07-20
Status: current

## Core Principle

Masao is the subject. AI characters support selection, writing, organization, and operation.
Content is not published merely to keep a production line busy.

## Platform Policy

| platform/format | current policy | main purpose |
| --- | --- | --- |
| YouTube Live | Continue three parts; prioritize Part 3 | Community, habit, watch time, comments, discovery of moments |
| YouTube regular video | Routine publishing paused | Publish only a strong story after separate approval |
| Kodeko daily digest | Paused | Preserve workflow and history; no automatic restart |
| Taro Selection video | Paused | Preserve workflow and assets; chatbot Taro remains separate |
| YouTube Shorts | Main channel morning/evening operation plus experimental `まさおの隠れ家` | Continue the main cadence; target one hideout post per day at 20:00 JST |
| X | Lightweight Live support | Live-start notice and current-Masao self-reply clip |
| TikTok | About two per day | External reach and creative testing |
| Instagram Reels | About one per day | External reach and reusable short-form distribution |
| note | Occasional | Story, worldview, system background |

## YouTube Shorts

- Main-channel Shorts remain active in morning/evening slots under the `YouTube Shorts` platform key and `YouTube` Drive folder.
- Main-channel output should include a draft post-package JSON and readable title/description TXT in the same Drive `YouTube` folder. Follow `D:\MD\context\projects\masao\MAIN_SHORTS_METADATA_STYLE.md`; this preparation does not authorize upload or publication.
- `まさおの隠れ家` (`UCIG-z7Q4rRq-cbIUJDB8SlA`) is a separate experimental Shorts-only channel. Target one post per day at 20:00 JST; skip a day when no suitable finished asset exists and do not compensate with a double post.
- An unqualified `YouTube` request targets the main channel; a hideout request must be labeled explicitly.
- Use `YouTube Shorts（まさおの隠れ家）` as the exact inventory/usage platform key.
- Do not reuse the same scene across the existing YouTube channel and `まさおの隠れ家`.
- Hideout outputs use the existing approved vertical stock by default to preserve framing and Masao's position. OBS overlays are allowed; rebuild a no-telop version only when explicitly requested. RAW and existing stock remain immutable.
- Hideout generation and API upload normally stay on the local PC. Drive is optional when another operator or device needs the asset, or when explicit archival delivery is requested.
- Generate a draft posting package with the finished hideout video. Follow `D:\MD\context\projects\masao\HIDEOUT_METADATA_STYLE.md`; generation, usage recording, metadata approval, upload, and schedule/publication remain separate permissions.
- Do not restore six/eight-post daily volume without a new decision.
- Prefer a small number of clearly different experiments over repeated template output.
- Current useful lanes are approximately 22-30 seconds and a smaller number of longer multi-cut tests.
- Show Masao immediately. Do not lead with an AI character card or a long logo opening.
- Do not use a fixed end CTA when it occupies a large share of the video.
- Upload, schedule, metadata changes, comments, and playlist writes require the permissions in `ABSOLUTE_RULES.md`.

## Regular Video

- Do not resume daily Kodeko publication by default.
- A strong event, relationship, behavior, or story is required before proposing a video.
- Date and series name are secondary to the viewer's reason to click.
- Drafting or researching material does not authorize generation, delivery, upload, or publication.

## X

- Treat X as a real-time contact point, not the primary subscriber-growth engine.
- Live-start posts may include the current Live URL.
- The self-reply may contain a short vertical `current Masao` clip.
- Keep normal X posts native and lightweight; do not attach a YouTube link to every post.
- Public posting requires confirmation unless the exact recurring post is already covered by a standing instruction.

## TikTok and Instagram

- Reuse one prepared master when practical.
- Do not create heavy platform-specific edits every day unless results justify the work.
- TikTok and Instagram posting status must be recorded separately.
- External SNS remains an experiment until measured YouTube return becomes meaningful.

## Asset Workflow

1. Confirm the source scene, video ID, timestamp, and prior use.
2. Read/copy from canonical source media without modifying it.
3. Create source cuts and all processed files under `D:\OBS\REC\work`.
4. Check vertical crop, visible subject, duplicate status, and content accuracy.
5. Deliver completed assets to the agreed destination. Use `G:\マイドライブ\Masao_SNS\YYYY-MM-DD` for the normal shared SNS handoff; the hideout may use its approved local-direct path.
6. Record platform states separately: selected, rendered, delivered, posted, retired, reusable.

Drive delivery reserves the scene from accidental reuse, but it is not the same state as a confirmed public post.
For a local-direct hideout output, the confirmed local destination may reserve the scene under the same inventory rule. The legacy ledger field named `drivePath` may contain that local path until the ledger schema is migrated.

## Playlist and Metadata

- Playlist review is a weekly Sunday task, not a daily growth task.
- New metadata templates apply to future content by default.
- Do not bulk-edit historical videos or Live archives without an approved item list.
- Hideout titles and descriptions use the quiet, factual, bilingual profile in `D:\MD\context\projects\masao\HIDEOUT_METADATA_STYLE.md`.
- Main-channel Shorts use the action-first, factual, bilingual profile in `D:\MD\context\projects\masao\MAIN_SHORTS_METADATA_STYLE.md`, with a concise Live route in the description.

## Measurement

- Channel analysis remains read-only unless a separate write is authorized.
- Compare format, duration, first visual, scene type, traffic source, subscriber contribution, and 24/48-hour result.
- Do not increase volume because of one isolated result. Look for repeatability across multiple posts.
