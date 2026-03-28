from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


PATH_KEYS = {
    "base_dir",
    "event_queue",
    "deferred_queue",
    "rejected_queue",
    "upload_queue",
    "bgm_path",
    "logo_png",
    "api_env_file",
    "prompt_file",
    "youtube_token",
}


def load_config(config_path: str | Path) -> Dict[str, Any]:
    p = Path(config_path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"config file not found: {p}")
    with p.open("r", encoding="utf-8-sig") as f:
        conf = json.load(f)
    conf["__config_path__"] = str(p)
    conf["__config_dir__"] = str(p.parent)
    return conf


def config_dir(conf: Dict[str, Any]) -> Path:
    return Path(str(conf["__config_dir__"]))


def resolve_path_value(conf: Dict[str, Any], value: str | Path) -> Path:
    p = Path(value)
    if p.is_absolute():
        return p
    return (config_dir(conf) / p).resolve()


def resolve_config_path(conf: Dict[str, Any], key: str) -> Path:
    raw = str(conf.get(key, "") or "").strip()
    if not raw:
        raise KeyError(f"config path missing: {key}")
    return resolve_path_value(conf, raw)


def resolve_optional_path(conf: Dict[str, Any], key: str) -> Path | None:
    raw = str(conf.get(key, "") or "").strip()
    if not raw:
        return None
    return resolve_path_value(conf, raw)


def clone_resolved_config(conf: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(conf)
    for key in PATH_KEYS:
        raw = str(conf.get(key, "") or "").strip()
        if raw:
            out[key] = str(resolve_path_value(conf, raw))
    return out


def ensure_parent(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


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
