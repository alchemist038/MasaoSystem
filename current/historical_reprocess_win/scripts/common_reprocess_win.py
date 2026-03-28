from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

JST = timezone(timedelta(hours=9))
SESSION_NAME_RE = re.compile(r"^20\d{2}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$")


def load_config(config_path: str | Path) -> Dict[str, Any]:
    path = Path(config_path)
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def resolve_path(config_path: str | Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (Path(config_path).resolve().parent / path).resolve()


def ensure_parent(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def append_jsonl(path: str | Path, row: Dict[str, Any]) -> None:
    p = Path(path)
    ensure_parent(p)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_jsonl_atomic(path: str | Path, rows: Iterable[Dict[str, Any]]) -> None:
    p = Path(path)
    ensure_parent(p)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    tmp.replace(p)


def read_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.lstrip("\ufeff").strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def now_jst() -> datetime:
    return datetime.now(JST).replace(microsecond=0)


def session_sort_key(path: Path) -> str:
    return path.name


def is_session_dir(path: Path) -> bool:
    return path.is_dir() and bool(SESSION_NAME_RE.match(path.name))
