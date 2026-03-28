from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from common_reprocess_win import is_session_dir, load_config, now_jst, resolve_path, session_sort_key


def choose_next_session(root: Path) -> Optional[Path]:
    sessions = []
    for path in root.iterdir():
        if not is_session_dir(path):
            continue
        if not (path / "proxy_360.mp4").exists():
            continue
        if (path / "logs" / ".analyze_done").exists():
            continue
        sessions.append(path)
    if not sessions:
        return None
    return sorted(sessions, key=session_sort_key)[0]


def is_stable(file_path: Path, wait_seconds: int) -> bool:
    size1 = file_path.stat().st_size if file_path.exists() else -1
    time.sleep(max(wait_seconds, 0))
    size2 = file_path.stat().st_size if file_path.exists() else -1
    return size1 == size2 and size1 >= 0


def append_log(log_path: Path, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(message + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="Windows replacement for analyze cron entry")
    ap.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "config.json"))
    ap.add_argument("--session-dir", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    conf = load_config(args.config)
    root = resolve_path(args.config, conf["warehouse_root"])
    logs_dir = resolve_path(args.config, conf.get("logs_dir", "logs"))
    log_path = logs_dir / "run_analyze_next_session_win.log"
    stability_wait = int(conf.get("stability_check_seconds", 1))

    session_dir = Path(args.session_dir).resolve() if args.session_dir else choose_next_session(root)
    if session_dir is None:
        append_log(log_path, f"[{now_jst().isoformat()}] [INFO] no pending session")
        print("[INFO] no pending session")
        return

    proxy_path = session_dir / "proxy_360.mp4"
    if not proxy_path.exists():
        raise SystemExit(f"proxy missing: {proxy_path}")

    if not args.force and not is_stable(proxy_path, stability_wait):
        append_log(log_path, f"[{now_jst().isoformat()}] [SKIP] growing: {session_dir}")
        print(f"[SKIP] growing: {session_dir}")
        return

    script_path = Path(__file__).with_name("analyze_y2_events_win.py")
    cmd = [sys.executable, str(script_path), "--config", str(Path(args.config).resolve()), "--session-dir", str(session_dir)]
    if args.force:
        cmd.append("--force")

    append_log(log_path, f"[{now_jst().isoformat()}] [RUN] {session_dir}")
    print(f"[RUN] {session_dir}")
    if args.dry_run:
        print("[DRY] " + " ".join(cmd))
        return

    result = subprocess.run(cmd, text=True, capture_output=True)
    append_log(log_path, result.stdout.rstrip())
    if result.stderr.strip():
        append_log(log_path, result.stderr.rstrip())
    if result.returncode != 0:
        append_log(log_path, f"[{now_jst().isoformat()}] [ERROR] rc={result.returncode}")
        raise SystemExit(result.returncode)

    append_log(log_path, f"[{now_jst().isoformat()}] [DONE] {session_dir}")


if __name__ == "__main__":
    main()
