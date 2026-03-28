from __future__ import annotations

import argparse
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Dict, List, Set, Tuple

from common_reprocess_win import JST, append_jsonl, is_session_dir, load_config, now_jst, read_jsonl, resolve_path


def parse_hhmm(value: str) -> time:
    hh, mm = value.split(":")
    return time(int(hh), int(mm), 0, tzinfo=JST)


def parse_date_yyyy_mm_dd(value: str) -> date:
    yyyy, mm, dd = value.split("-")
    return date(int(yyyy), int(mm), int(dd))


def session_date_from_name(session_dir: Path) -> date:
    return parse_date_yyyy_mm_dd(session_dir.name[:10])


def list_frames_events(session_dir: Path) -> List[Tuple[str, Path]]:
    frames_root = session_dir / "frames_360"
    if not frames_root.exists():
        return []
    out: List[Tuple[str, Path]] = []
    for path in sorted(frames_root.iterdir()):
        if path.is_dir():
            out.append((path.name, path))
    return out


def load_existing_event_keys(event_queue_path: Path) -> Set[str]:
    keys: Set[str] = set()
    for row in read_jsonl(event_queue_path):
        session_dir = row.get("session_dir")
        event_name = row.get("event_name")
        if session_dir and event_name:
            keys.add(f"{session_dir}::{event_name}")
    return keys


def build_pool(root: Path, existing_keys: Set[str], date_filter) -> List[Dict[str, str]]:
    pool: List[Dict[str, str]] = []
    for session_dir in sorted((p for p in root.iterdir() if is_session_dir(p)), key=lambda p: p.name):
        try:
            session_date = session_date_from_name(session_dir)
        except Exception:
            continue
        if not date_filter(session_date):
            continue
        if not (session_dir / "logs" / ".analyze_done").exists():
            continue
        for event_name, frames_dir in list_frames_events(session_dir):
            event_dir = session_dir / "events" / event_name
            if event_dir.exists():
                continue
            key = f"{session_dir}::{event_name}"
            if key in existing_keys:
                continue
            pool.append(
                {
                    "session_dir": str(session_dir),
                    "event_name": event_name,
                    "frames_dir": str(frames_dir),
                    "event_dir": str(event_dir),
                }
            )
    return pool


def assign_times(target_date: date, start_hhmm: str, pitch_hours: float, count: int) -> List[str]:
    start_time = parse_hhmm(start_hhmm)
    base = datetime(target_date.year, target_date.month, target_date.day, start_time.hour, start_time.minute, 0, tzinfo=JST)
    return [(base + timedelta(hours=pitch_hours * idx)).isoformat() for idx in range(count)]


def main() -> None:
    ap = argparse.ArgumentParser(description="Windows inventory enqueue for historical 360 assets")
    ap.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "config.json"))
    ap.add_argument("--date", default="")
    ap.add_argument("--y", type=int, default=-1)
    ap.add_argument("--a", type=int, default=-1)
    ap.add_argument("--start-y", default="")
    ap.add_argument("--start-a", default="")
    ap.add_argument("--pitch-y", type=float, default=-1.0)
    ap.add_argument("--pitch-a", type=float, default=-1.0)
    ap.add_argument("--days-back", type=int, default=-1)
    ap.add_argument("--seed", type=int, default=-1)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conf = load_config(args.config)
    enqueue_conf = conf.get("enqueue", {})
    root = resolve_path(args.config, conf["warehouse_root"])
    event_queue = resolve_path(args.config, conf["event_queue"])

    y_count = int(enqueue_conf.get("y_count", 3) if args.y < 0 else args.y)
    a_count = int(enqueue_conf.get("a_count", 3) if args.a < 0 else args.a)
    start_y = str(enqueue_conf.get("start_y", "07:00") if not args.start_y else args.start_y)
    start_a = str(enqueue_conf.get("start_a", "19:00") if not args.start_a else args.start_a)
    pitch_y = float(enqueue_conf.get("pitch_y", 4.0) if args.pitch_y < 0 else args.pitch_y)
    pitch_a = float(enqueue_conf.get("pitch_a", 4.0) if args.pitch_a < 0 else args.pitch_a)
    days_back = int(enqueue_conf.get("days_back", 14) if args.days_back < 0 else args.days_back)
    seed = int(enqueue_conf.get("seed", 42) if args.seed < 0 else args.seed)

    random.seed(seed)
    target_date = parse_date_yyyy_mm_dd(args.date) if args.date else now_jst().date()
    yesterday = target_date - timedelta(days=1)

    existing_keys = load_existing_event_keys(event_queue)
    print(f"[INFO] event_queue={event_queue} existing_keys={len(existing_keys)}")
    print(f"[INFO] target_date={target_date} yesterday={yesterday} archive_days={days_back}")

    pool_y = build_pool(root, existing_keys, lambda session_date: session_date == yesterday)
    pool_a = build_pool(root, existing_keys, lambda session_date: 0 <= (target_date - session_date).days <= days_back)

    random.shuffle(pool_y)
    random.shuffle(pool_a)

    y_selected = pool_y[:y_count]
    y_keys = {f"{row['session_dir']}::{row['event_name']}" for row in y_selected}

    a_filtered = [row for row in pool_a if f"{row['session_dir']}::{row['event_name']}" not in y_keys]
    a_selected = a_filtered[:a_count]

    out_rows: List[Dict[str, str]] = []
    for row, publish_at in zip(y_selected, assign_times(target_date, start_y, pitch_y, len(y_selected))):
        row2 = dict(row)
        row2["publishAt"] = publish_at
        row2["route"] = "Y"
        out_rows.append(row2)

    for row, publish_at in zip(a_selected, assign_times(target_date, start_a, pitch_a, len(a_selected))):
        row2 = dict(row)
        row2["publishAt"] = publish_at
        row2["route"] = "A"
        out_rows.append(row2)

    print("[EVENT_QUEUE_PREVIEW]")
    if not out_rows:
        print("(empty)")
    else:
        for idx, row in enumerate(out_rows, 1):
            print(f"{idx:02d} {row['route']} {row['publishAt']} {row['session_dir']}\\events\\{row['event_name']}")

    if args.dry_run:
        print("[DRY] queue unchanged")
        return

    for row in out_rows:
        append_jsonl(event_queue, row)
    print(f"[OK] appended {len(out_rows)} rows -> {event_queue}")


if __name__ == "__main__":
    main()
