#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from common_line import (
    append_jsonl,
    clone_resolved_config,
    load_config,
    read_jsonl,
    resolve_config_path,
    write_jsonl_atomic,
)
from generate_metadata_win_yolo_ptz_20s import generate_metadata


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def run_cmd(cmd: List[str], timeout: int = 1800) -> bool:
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if res.returncode != 0:
        log(f"CMD_ERROR: {' '.join(cmd)}")
        if res.stderr:
            log(res.stderr.strip())
        return False
    return True


def escape_drawtext(s: str) -> str:
    return s.replace("\\", "\\\\").replace("\n", r"\n").replace(":", r"\:").replace("'", r"\'")


def get_median_cx(raw_yolo_path: Path, start_abs: int, end_abs: int) -> float:
    cxs: List[float] = []
    if not raw_yolo_path.exists():
        return 320.0

    with raw_yolo_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            sec = int(obj.get("sec", -1))
            if not (start_abs <= sec <= end_abs):
                continue
            bb = obj.get("bbox_xyxy")
            if not (isinstance(bb, list) and len(bb) == 4):
                continue
            cxs.append((float(bb[0]) + float(bb[2])) / 2.0)

    return float(statistics.median(cxs)) if cxs else 320.0


def calculate_crop_x(cx: float) -> int:
    target_w_in_360 = 202
    crop_x = int(cx - (target_w_in_360 / 2))
    return max(0, min(crop_x, 640 - target_w_in_360))


def export_cropped_previews(
    conf: Dict[str, Any],
    raw_path: Path,
    out_dir: Path,
    start_abs: int,
    dur: int,
    crop_x_360: int,
) -> bool:
    ffmpeg = str(conf.get("ffmpeg", "ffmpeg"))
    cmd = [
        ffmpeg,
        "-y",
        "-ss",
        str(start_abs),
        "-t",
        str(dur),
        "-i",
        str(raw_path),
        "-vf",
        f"fps=1,crop=ih*9/16:ih:{crop_x_360 * 3}:0,scale=225:400",
        str(out_dir / "frame_%03d.jpg"),
    ]

    for attempt in range(1, 4):
        try:
            if out_dir.exists():
                shutil.rmtree(out_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            log(f"preview dir reset failed (attempt {attempt}/3): {e}")
            if attempt < 3:
                time.sleep(0.5)
                continue
            return False

        if run_cmd(cmd, timeout=1200):
            return True

        if attempt < 3:
            log(f"retry export_cropped_previews ({attempt}/3)")
            time.sleep(0.8)
    return False


def prepare_review_artifacts(conf: Dict[str, Any], frames_dir: Path) -> List[Path]:
    src = sorted(frames_dir.glob("frame_*.jpg"))
    if not src:
        return []

    review_dir = frames_dir.parent / "images_review"
    review_dir.mkdir(parents=True, exist_ok=True)

    out: List[Path] = []
    for sec in [0, 5, 10, 15]:
        idx = min(max(sec, 0), len(src) - 1)
        dst_path = review_dir / f"review_{sec:02d}s.jpg"
        try:
            shutil.copy2(src[idx], dst_path)
            out.append(dst_path)
        except FileNotFoundError:
            continue

    ffmpeg = str(conf.get("ffmpeg", "ffmpeg"))
    contact_sheet = review_dir / "contact_sheet.jpg"
    cmd = [
        ffmpeg,
        "-y",
        "-start_number",
        "1",
        "-i",
        str(frames_dir / "frame_%03d.jpg"),
        "-frames:v",
        "1",
        "-vf",
        "tile=5x4:padding=6:margin=8",
        str(contact_sheet),
    ]
    if run_cmd(cmd, timeout=300) and contact_sheet.exists():
        out.append(contact_sheet)
    return out


def build_vf(conf: Dict[str, Any], crop_x_raw: int) -> str:
    tel = conf.get("telop", {})
    fontfile = str(conf.get("fontfile", r"C:\Windows\Fonts\meiryo.ttc"))
    ff_fontfile = fontfile.replace("\\", "/").replace(":", r"\:")
    out_w = int(conf.get("out_w", 720))
    out_h = int(conf.get("out_h", 1280))
    t1 = escape_drawtext(str(tel.get("top1", "AI AUTO SHORT")))
    t2 = escape_drawtext(str(tel.get("top2", "See description")))
    bottom_raw = str(
        tel.get("bottom3", "Subscribe for more\\nWatch Masao live\\nYou may catch him there")
    ).replace("\\n", "\n")
    bottom_lines = [escape_drawtext(x.strip()) for x in bottom_raw.splitlines() if x.strip()]
    if not bottom_lines:
        bottom_lines = [escape_drawtext("Subscribe for more")]

    filters = [
        f"crop=ih*9/16:ih:{crop_x_raw}:0",
        f"scale={out_w}:{out_h}",
        f"drawtext=text='{t1}':fontsize=54:fontcolor=white@0.45:x=(w-text_w)/2:y=180:fontfile='{ff_fontfile}'",
        f"drawtext=text='{t2}':fontsize=36:fontcolor=white@0.38:x=(w-text_w)/2:y=260:fontfile='{ff_fontfile}'",
    ]

    for idx, line in enumerate(bottom_lines[:3]):
        y_expr = f"h-{430 - (idx * 54)}"
        filters.append(
            "drawtext="
            f"text='{line}':fontsize=38:fontcolor=white@0.9:"
            "borderw=3:bordercolor=black@0.8:shadowx=2:shadowy=2:shadowcolor=black@0.7:"
            "box=1:boxcolor=black@0.16:boxborderw=10:"
            f"x=(w-text_w)/2:y={y_expr}:fontfile='{ff_fontfile}':"
            "alpha='if(lt(t,16),0,min(0.78,(t-16)*0.39))'"
        )

    return ",".join(filters)


def build_logo_overlay_filter_complex(vf_main: str) -> str:
    return (
        f"[0:v]{vf_main}[vmain];"
        "[1:v]format=rgba,loop=loop=-1:size=1:start=0,trim=duration=2,setpts=N/(30*TB),fade=t=out:st=1:d=1:alpha=1[logo_faded];"
        "[logo_faded][vmain]scale2ref=w=main_w*0.70:h=ow/mdar[logo][vref];"
        "[vref][logo]overlay=x=(main_w-overlay_w)/2:y=(main_h-overlay_h)/2:format=auto:enable='lt(t,2)'[vout]"
    )


def render_video(conf: Dict[str, Any], raw_path: Path, out_path: Path, start_abs: int, dur: int, crop_x_360: int) -> bool:
    ffmpeg = str(conf.get("ffmpeg", "ffmpeg"))
    bgm_path = Path(str(conf["bgm_path"]))
    logo_raw = str(conf.get("logo_png", "")).strip()
    logo_path = Path(logo_raw) if logo_raw else None
    crop_x_raw = crop_x_360 * 3
    vf_main = build_vf(conf, crop_x_raw)

    cmd = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-ss",
        str(start_abs),
        "-t",
        str(dur),
        "-i",
        str(raw_path),
    ]

    has_logo = logo_path is not None and logo_path.is_file()
    if has_logo:
        cmd += ["-i", str(logo_path)]

    cmd += ["-stream_loop", "-1", "-i", str(bgm_path)]

    if has_logo:
        cmd += ["-filter_complex", build_logo_overlay_filter_complex(vf_main), "-map", "[vout]"]
    else:
        cmd += ["-vf", vf_main, "-map", "0:v:0"]

    cmd += ["-map", "2:a:0" if has_logo else "1:a:0"]
    cmd += [
        "-c:v",
        "libx264",
        "-crf",
        "20",
        "-preset",
        "veryfast",
        "-pix_fmt",
        "yuv420p",
        "-af",
        "afade=t=in:st=1:d=1,volume=0.16",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-shortest",
        str(out_path),
    ]
    return run_cmd(cmd, timeout=2400)


def parse_action(args_action: str) -> str:
    val = args_action.strip().lower()
    if val not in {"approve", "defer", "reject", "prompt"}:
        raise ValueError("review action must be approve|defer|reject|prompt")
    return val


def review_action(action: str, event_name: str, review_paths: List[Path], frames_dir: Path) -> str:
    if review_paths:
        print("-" * 60)
        print("Review artifacts:")
        for p in review_paths:
            print(f"  {p}")

    if action != "prompt":
        return action

    print("-" * 60)
    print(f"Review required: {event_name}")
    print(f"JPEG dir: {frames_dir}")
    print("Choose action [a]pprove / [d]efer / [r]eject")
    while True:
        try:
            s = input("> ").strip().lower()
        except EOFError:
            return "defer"
        if s in ("a", "approve"):
            return "approve"
        if s in ("d", "defer"):
            return "defer"
        if s in ("r", "reject"):
            return "reject"


def artifact_root_for_event(conf: Dict[str, Any], event_dir: Path) -> Path:
    return event_dir / str(conf.get("line_artifact_dirname", "_win_yolo_ptz_20s"))


def main() -> None:
    ap = argparse.ArgumentParser(description="Event queue pipeline for WIN_YOLO_PTZ_20S")
    ap.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "config.json"))
    ap.add_argument("--max", type=int, default=5)
    ap.add_argument("--event-dir", default="", help="manual single event dir")
    ap.add_argument("--no-api", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--review-before-api", action="store_true")
    ap.add_argument("--review-action", default="prompt", help="approve|defer|reject|prompt")
    args = ap.parse_args()

    conf = clone_resolved_config(load_config(args.config))
    event_queue_path = resolve_config_path(conf, "event_queue")
    upload_queue_path = resolve_config_path(conf, "upload_queue")
    deferred_queue_path = resolve_config_path(conf, "deferred_queue")
    rejected_queue_path = resolve_config_path(conf, "rejected_queue")
    raw_video_name = str(conf.get("raw_video_name", "raw.mkv"))
    raw_yolo_name = str(conf.get("raw_yolo_name", "raw_yolo.jsonl"))
    duration = int(conf.get("render_duration_sec", 20))
    route_default = str(conf.get("route", "win_yolo_ptz_20s"))

    action_mode = parse_action(args.review_action)
    lock_path = event_queue_path.with_suffix(event_queue_path.suffix + ".lock")
    lock_fd: int | None = None
    try:
        lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(lock_fd, str(os.getpid()).encode("utf-8"))
    except FileExistsError:
        log(f"another pipeline process is running (lock exists): {lock_path}")
        return

    if args.event_dir:
        ev_dir = Path(args.event_dir).resolve()
        if not ev_dir.exists():
            log(f"event dir not found: {ev_dir}")
            return
        sess_dir = ev_dir.parent.parent
        ev_name = ev_dir.name
        work_items = [
            {
                "event_dir": str(ev_dir),
                "session_dir": str(sess_dir),
                "event_name": ev_name,
                "publishAt": (datetime.now() + timedelta(hours=1)).isoformat(),
                "route": route_default,
            }
        ]
        rem_lines: List[Dict[str, Any]] = []
        queue_mode = False
    else:
        lines = read_jsonl(event_queue_path)
        if not lines:
            log("event queue empty")
            return
        work_items = lines[: args.max]
        rem_lines = lines[args.max :]
        queue_mode = True

    retry_items: List[Dict[str, Any]] = []
    try:
        for item in work_items:
            ev_dir = Path(item["event_dir"]).resolve()
            sess_dir = Path(item["session_dir"]).resolve()
            ev_name = str(item["event_name"])
            publish_at = item.get("publishAt")
            route = str(item.get("route", route_default))
            artifact_root = artifact_root_for_event(conf, ev_dir)

            log(f"Processing {ev_name}")
            start_abs = int(ev_name.split("_")[0])
            raw_yolo = sess_dir / raw_yolo_name
            raw_video = sess_dir / raw_video_name
            if not raw_video.exists():
                log(f"[ERROR] raw video missing: {raw_video}")
                retry_items.append(item)
                continue

            med_cx = get_median_cx(raw_yolo, start_abs, start_abs + duration)
            crop_x_360 = calculate_crop_x(med_cx)
            log(f"median_cx={med_cx:.1f} crop_x_360={crop_x_360}")

            frames_dir = artifact_root / "images_cropped"
            if not export_cropped_previews(conf, raw_video, frames_dir, start_abs, duration, crop_x_360):
                log("[ERROR] failed to create cropped JPEG")
                retry_items.append(item)
                continue

            review_paths = prepare_review_artifacts(conf, frames_dir)
            if args.review_before_api:
                act = review_action(action_mode, ev_name, review_paths, frames_dir)
                if act == "defer":
                    append_jsonl(
                        deferred_queue_path,
                        {
                            "event_dir": str(ev_dir),
                            "session_dir": str(sess_dir),
                            "event_name": ev_name,
                            "publishAt": publish_at,
                            "route": route,
                            "reason": "manual_defer",
                            "at": datetime.now().isoformat(),
                        },
                    )
                    log("deferred")
                    continue
                if act == "reject":
                    append_jsonl(
                        rejected_queue_path,
                        {
                            "event_dir": str(ev_dir),
                            "session_dir": str(sess_dir),
                            "event_name": ev_name,
                            "publishAt": publish_at,
                            "route": route,
                            "reason": "manual_reject",
                            "at": datetime.now().isoformat(),
                        },
                    )
                    log("rejected")
                    continue

            try:
                if args.no_api:
                    log("skip metadata generation (--no-api)")
                    decision_json = artifact_root / "api" / "v1" / "decision.json"
                else:
                    decision_json = generate_metadata(
                        conf=conf,
                        artifact_root=artifact_root,
                        event_name=ev_name,
                        frames_dir=frames_dir,
                        crop_x=crop_x_360,
                        start_sec_rel=0,
                        end_sec_rel=duration,
                        force=args.force,
                    )
            except Exception as e:
                log(f"[ERROR] metadata failed: {e}")
                retry_items.append(item)
                continue

            if not decision_json.exists():
                log(f"[ERROR] decision not found: {decision_json}")
                retry_items.append(item)
                continue

            out_mp4 = artifact_root / "shorts" / f"{ev_name}_v1_bgm_V1.mp4"
            if out_mp4.exists() and not args.force:
                log(f"[SKIP] already exists: {out_mp4}")
            else:
                out_mp4.parent.mkdir(parents=True, exist_ok=True)
                if not render_video(conf, raw_video, out_mp4, start_abs, duration, crop_x_360):
                    log("[ERROR] render failed")
                    retry_items.append(item)
                    continue

            append_jsonl(
                upload_queue_path,
                {
                    "video_path": str(out_mp4),
                    "decision_path": str(decision_json),
                    "published_flag_path": str(decision_json.parent / ".published"),
                    "publishAt": publish_at,
                    "route": route,
                },
            )
            log(f"[OK] rendered and enqueued upload: {out_mp4}")

        if queue_mode:
            new_queue = retry_items + rem_lines
            write_jsonl_atomic(event_queue_path, new_queue)
            log(f"queue updated rem={len(new_queue)}")
    finally:
        if lock_fd is not None:
            os.close(lock_fd)
        try:
            lock_path.unlink(missing_ok=True)
        except OSError:
            pass


if __name__ == "__main__":
    main()
