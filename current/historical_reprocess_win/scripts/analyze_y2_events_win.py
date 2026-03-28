from __future__ import annotations

import argparse
import csv
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Tuple

from common_reprocess_win import JST, load_config


def run_cmd(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(
            "command failed\n"
            f"cmd={' '.join(cmd)}\n"
            f"rc={result.returncode}\n"
            f"stdout={result.stdout[-2000:]}\n"
            f"stderr={result.stderr[-4000:]}"
        )
    return result


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def ffprobe_duration_sec(ffprobe_cmd: str, video_path: Path) -> float:
    cmd = [
        ffprobe_cmd,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    result = run_cmd(cmd)
    return float((result.stdout or "").strip())


RE_PTS = re.compile(r"pts_time:(\d+(?:\.\d+)?)")
RE_MEAN = re.compile(r"mean:\[([0-9]+)")


def parse_showinfo_mean_y_per_sec(showinfo_log: Path) -> List[Tuple[int, int]]:
    rows: List[Tuple[int, int]] = []
    with showinfo_log.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "showinfo" not in line:
                continue
            match_pts = RE_PTS.search(line)
            match_mean = RE_MEAN.search(line)
            if not (match_pts and match_mean):
                continue
            sec = int(round(float(match_pts.group(1))))
            mean_y = int(match_mean.group(1))
            rows.append((sec, mean_y))

    dedup: dict[int, int] = {}
    for sec, mean_y in rows:
        dedup[sec] = mean_y
    return sorted(dedup.items(), key=lambda x: x[0])


def compute_delta(rows: Iterable[Tuple[int, int]]) -> List[Tuple[int, int, float]]:
    out: List[Tuple[int, int, float]] = []
    prev = None
    for sec, mean_y in rows:
        dy = 0.0 if prev is None else float(mean_y - prev)
        out.append((sec, mean_y, dy))
        prev = mean_y
    return out


def detect_hits(delta_rows: Iterable[Tuple[int, int, float]], dy_threshold: float, min_len_sec: int) -> List[Tuple[int, int]]:
    hits: List[Tuple[int, int]] = []
    run_start = None
    last_sec = None
    for sec, _, dy in delta_rows:
        is_move = abs(dy) >= dy_threshold
        if is_move:
            if run_start is None:
                run_start = sec
            last_sec = sec
            continue
        if run_start is None or last_sec is None:
            continue
        run_end = last_sec + 1
        if (run_end - run_start) >= min_len_sec:
            hits.append((run_start, run_end))
        run_start = None
        last_sec = None

    if run_start is not None and last_sec is not None:
        run_end = last_sec + 1
        if (run_end - run_start) >= min_len_sec:
            hits.append((run_start, run_end))
    return hits


def hits_to_segments(hits: Iterable[Tuple[int, int]], pre_sec: int, seg_len_sec: int, duration_sec: float) -> List[Tuple[int, int]]:
    segments: List[Tuple[int, int]] = []
    max_end = int(duration_sec)
    for hit_start, _ in hits:
        start = max(hit_start - pre_sec, 0)
        end = min(start + seg_len_sec, max_end)
        if end > start:
            segments.append((start, end))
    return segments


def merge_overlaps(segments: Iterable[Tuple[int, int]]) -> List[Tuple[int, int]]:
    ordered = sorted(segments)
    if not ordered:
        return []
    merged: List[List[int]] = [[ordered[0][0], ordered[0][1]]]
    for start, end in ordered[1:]:
        last = merged[-1]
        if start <= last[1]:
            last[1] = max(last[1], end)
        else:
            merged.append([start, end])
    return [(start, end) for start, end in merged]


def apply_op_ed_exclusion(events: Iterable[Tuple[int, int]], duration_sec: float, op_sec: int, ed_sec: int) -> List[Tuple[int, int]]:
    dur = int(duration_sec)
    ed_start = max(dur - ed_sec, 0)
    out: List[Tuple[int, int]] = []
    for start, end in events:
        if start < op_sec:
            continue
        if end > ed_start:
            continue
        out.append((start, end))
    return out


def cap_and_interval(events: Iterable[Tuple[int, int]], max_len: int, min_gap: int) -> List[Tuple[int, int]]:
    out: List[Tuple[int, int]] = []
    last_end = None
    for start, end in sorted(events):
        if end - start > max_len:
            end = start + max_len
        if last_end is not None and start < last_end + min_gap:
            continue
        out.append((start, end))
        last_end = end
    return out


def event_name(start: int, end: int) -> str:
    return f"{start:05d}_{end:05d}"


def extract_frames(ffmpeg_cmd: str, proxy_path: Path, out_dir: Path, start: int, end: int, jpg_q: int) -> None:
    ensure_dir(out_dir)
    duration = max(end - start, 1)
    cmd = [
        ffmpeg_cmd,
        "-y",
        "-ss",
        str(start),
        "-t",
        str(duration),
        "-i",
        str(proxy_path),
        "-an",
        "-vf",
        "fps=1",
        "-q:v",
        str(jpg_q),
        str(out_dir / "%03d.jpg"),
    ]
    run_cmd(cmd)


def write_rows(path: Path, header: List[str], rows: Iterable[Iterable[object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in rows:
            writer.writerow(list(row))


def write_segments(path: Path, segments: Iterable[Tuple[int, int]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for start, end in segments:
            f.write(f"{start} {end}\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="Windows DeltaY analyzer for historical sessions")
    ap.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "config.json"))
    ap.add_argument("--session-dir", required=True)
    ap.add_argument("--dy-th", type=float, default=-1.0)
    ap.add_argument("--min-len", type=int, default=-1)
    ap.add_argument("--pre-sec", type=int, default=-1)
    ap.add_argument("--seg-len", type=int, default=-1)
    ap.add_argument("--max-event", type=int, default=-1)
    ap.add_argument("--gap", type=int, default=-1)
    ap.add_argument("--op", type=int, default=-1)
    ap.add_argument("--ed", type=int, default=-1)
    ap.add_argument("--jpg-q", type=int, default=-1)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    conf = load_config(args.config)
    analyze_conf = conf.get("analyze", {})
    ffmpeg_cmd = str(conf.get("ffmpeg", "ffmpeg"))
    ffprobe_cmd = str(conf.get("ffprobe", "ffprobe"))

    dy_th = float(analyze_conf.get("dy_th", 3.0) if args.dy_th < 0 else args.dy_th)
    min_len = int(analyze_conf.get("min_len", 4) if args.min_len < 0 else args.min_len)
    pre_sec = int(analyze_conf.get("pre_sec", 3) if args.pre_sec < 0 else args.pre_sec)
    seg_len = int(analyze_conf.get("seg_len", 15) if args.seg_len < 0 else args.seg_len)
    max_event = int(analyze_conf.get("max_event", 60) if args.max_event < 0 else args.max_event)
    gap = int(analyze_conf.get("gap", 60) if args.gap < 0 else args.gap)
    op = int(analyze_conf.get("op", 180) if args.op < 0 else args.op)
    ed = int(analyze_conf.get("ed", 180) if args.ed < 0 else args.ed)
    jpg_q = int(analyze_conf.get("jpg_q", 2) if args.jpg_q < 0 else args.jpg_q)

    session_dir = Path(args.session_dir)
    proxy_path = session_dir / "proxy_360.mp4"
    logs_dir = session_dir / "logs"
    frames_root = session_dir / "frames_360"
    analyze_done = logs_dir / ".analyze_done"

    if not proxy_path.exists():
        raise SystemExit(f"proxy_360.mp4 not found: {proxy_path}")
    if analyze_done.exists() and not args.force:
        print(f"[SKIP] already analyzed: {session_dir}")
        return

    ensure_dir(logs_dir)
    ensure_dir(frames_root)

    duration = ffprobe_duration_sec(ffprobe_cmd, proxy_path)

    showinfo_log = logs_dir / "showinfo_fps1.log"
    filter_graph = "crop=iw/2:ih/2:0:ih/2,fps=1,showinfo"
    cmd = [
        ffmpeg_cmd,
        "-y",
        "-i",
        str(proxy_path),
        "-an",
        "-vf",
        filter_graph,
        "-f",
        "null",
        "-",
    ]
    result = run_cmd(cmd, check=False)
    showinfo_log.write_text(result.stderr, encoding="utf-8", errors="ignore")
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg showinfo failed for {proxy_path}")

    mean_rows = parse_showinfo_mean_y_per_sec(showinfo_log)
    write_rows(logs_dir / "meanY_sec.csv", ["sec", "meanY"], mean_rows)

    delta_rows = compute_delta(mean_rows)
    write_rows(
        logs_dir / "deltaY_sec.csv",
        ["sec", "meanY", "deltaY"],
        ((sec, mean_y, f"{dy:.1f}") for sec, mean_y, dy in delta_rows),
    )

    hits = detect_hits(delta_rows, dy_th, min_len)
    write_segments(logs_dir / "hits_4sec.txt", hits)

    segments = hits_to_segments(hits, pre_sec, seg_len, duration)
    write_segments(logs_dir / "segments_15s.txt", segments)

    merged = merge_overlaps(segments)
    write_segments(logs_dir / "events_merged.txt", merged)

    no_op_ed = apply_op_ed_exclusion(merged, duration, op, ed)
    final_events = cap_and_interval(no_op_ed, max_event, gap)
    write_segments(logs_dir / "events_no_oped.txt", final_events)

    frame_log = logs_dir / "frames_extract.nohup.log"
    with frame_log.open("a", encoding="utf-8") as f:
        for start, end in final_events:
            name = event_name(start, end)
            out_dir = frames_root / name
            if out_dir.exists() and any(out_dir.glob("*.jpg")) and not args.force:
                f.write(f"[SKIP] frames exist: {name}\n")
                continue
            f.write(f"[EXTRACT] {name}\n")
            extract_frames(ffmpeg_cmd, proxy_path, out_dir, start, end, jpg_q)
            f.write(f"[OK] {name}\n")

    analyze_done.write_text(now_text(), encoding="utf-8")
    print(f"[OK] analyzed: {session_dir}")
    print(f"duration={duration:.1f}s events={len(final_events)} dy_th={dy_th} min_len={min_len}")


def now_text() -> str:
    return datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    main()
