# Masao Current Operations

Updated: 2026-07-20
Status: current

This file answers one question: what is operating now?

## Goal

```text
Reach 10,000 YouTube subscribers by 2027-05-12.
```

The immediate operating goal is to protect Live, keep external SNS lightweight, and search for a repeatable new-viewer entry format without returning to high-volume Shorts production.

## Current Status

| area | status | current operation |
| --- | --- | --- |
| YouTube Live | active | Three daily parts; protect Part 3 night/dinner as the strongest slot |
| OBS daily operation | active | Part 1 manual start; Part 2 and Part 3 use the established schedule flow |
| PTZ / V7 tracking | active | Existing runtime and presets continue; no structural change |
| Tapo / KEECE fallback | active | Existing location preset and tracking-state behavior continue |
| Room temperature overlay | active | SwitchBot Hub / Cloud API path remains the production method |
| Live chatbot | active as a separate operation | Existing GPT Taro/Goro chat behavior is not the paused video-production line |
| Kodeko daily/regular video | paused | Do not generate or publish on a daily schedule |
| Taro Selection video | paused | Do not generate or publish the 45-60 second selection line routinely |
| YouTube regular video | paused as a scheduled routine | Publish only after a separate proposal and approval for a strong story |
| YouTube Shorts | active + experimental | Main channel continues morning/evening posts; `まさおの隠れ家` targets one post per day at 20:00 JST without forced make-up posts |

`まさおの隠れ家` outputs use existing approved vertical stock by default so the accepted framing is preserved. OBS overlays are allowed; no-telop rebuilding is explicit-request-only. RAW and existing stock files remain immutable. Its normal delivery path is local PC generation followed by the guarded hideout API uploader; Drive is optional for handoff, device transfer, or explicit archive.
| X | active, lightweight | Live-start post plus self-reply with a short `current Masao` clip |
| TikTok | active, lightweight | Approximately two posts per day using prepared reusable assets |
| Instagram | active, lightweight | Approximately one post per day using prepared reusable assets |
| SNS clip inventory / delivery | active | Select, render, deduplicate, log, and deliver completed assets to the agreed Drive or local destination |
| Playlist maintenance | weekly | Review on Sunday; do not treat as a daily growth task |
| note | optional support | Use for worldview, story, and behind-the-scenes context |

## Important Distinction

`Taro paused` means the Taro Selection video-production line is paused.
It does not mean that the existing live chatbot must be stopped.

`Kodeko paused` means routine Kodeko daily/regular video generation and publishing are paused.
Kodeko remains an internal role for investigation, organization, QA, and documentation.

## Live Baseline

- Part 1: morning monitoring; stable middle tier.
- Part 2: daytime/nap monitoring; relatively weak and not a growth priority.
- Part 3: night and approximately 18:30 dinner time; strongest core slot.
- New Live reservations created after 2026-07-15 use these public titles:

```text
Part 1: うさぎライブ｜ミニレッキスのまさお放牧中・朝の警備 / Relaxing Rabbit Live Cam
Part 2: うさぎライブ｜ミニレッキスのまさお放牧中・お昼寝中？ / Relaxing Rabbit Live Cam
Part 3: うさぎライブ｜ミニレッキスのまさお放牧中・18:30ごろごはん / Relaxing Rabbit Live Cam
```

- Part numbers remain internal labels and description text. Do not put part numbers, dates, or hashtags in the public title.
- Do not retroactively edit Live reservations that already existed on 2026-07-15.
- All three parts use the coordinated bright thumbnail series adopted on 2026-07-15. Runtime files are `masao_thumb_part1_morning.jpg`, `masao_thumb_part2_noon.jpg`, and `masao_thumb_part3_night.jpg` under `C:\Users\alche\Desktop\OBS\サムネ` (all 1280x720 JPEG). Each image is slot-specific: morning patrol, daytime nap, and dinner around 18:30.
- Do not redesign Live merely because Shorts distribution changes.
- Keep public Live changes inside the daily live-prep authorization described in `ABSOLUTE_RULES.md`.

Detailed runbook:

```text
D:\MD\context\projects\masao\RUNBOOK_morning_live_prep.md
```

## Content Baseline

- The subject is Masao. AI characters remain supporting editors and operators.
- The 10,000-subscriber story may remain in Live overlays and descriptions, but it must not replace Masao as the first visual hook.
- Do not publish merely to satisfy a daily count.
- A paused line may be investigated or drafted, but generation, Drive delivery, upload, and public posting are separate permissions.
- Main-channel Shorts generation should attach draft title/description JSON and TXT to the Drive `YouTube` folder using `D:\MD\context\projects\masao\MAIN_SHORTS_METADATA_STYLE.md`.
- Hideout generation should also create a draft post package using `D:\MD\context\projects\masao\HIDEOUT_METADATA_STYLE.md`; it must not upload or schedule without explicit approval.

## Current Analytics Reference

Latest consolidated channel status:

```text
D:\MD\context\projects\masao\2026-07-09_channel_current_status_video_shorts_live.md
D:\MD\context\projects\masao\2026-07-09_external_media_inflow_check.md
```

Current interpretation:

- Regular videos remain too weak for daily publication.
- Shorts have improved from the late-June bottom but have not recovered to a repeatable winning pattern.
- Live remains functional, especially Part 3.
- External traffic exists but is still small; keep SNS lightweight and measure it.

## Change Rule

Update this file when a standing operation starts, stops, changes frequency, changes owner, or changes its default permission. Do not append daily logs here.
