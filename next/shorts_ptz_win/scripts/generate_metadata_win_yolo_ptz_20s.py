#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from common_line import clone_resolved_config, load_config, resolve_optional_path


def read_text_any(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def read_env_file(path: Path) -> Dict[str, str]:
    vals: Dict[str, str] = {}
    if not path.exists():
        return vals
    for raw in read_text_any(path).splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        vals[key] = value.strip().strip('"').strip("'")
    return vals


def get_api_key(conf: Dict[str, Any]) -> str:
    env_name = str(conf.get("api_key_env_name", "OPENAI_API_KEY")).strip() or "OPENAI_API_KEY"
    direct = str(conf.get("api_key", "")).strip()
    if direct:
        return direct

    env_path = resolve_optional_path(conf, "api_env_file")
    if env_path is not None:
        env_vals = read_env_file(env_path)
        key = env_vals.get(env_name, "").strip()
        if key:
            return key

    key = os.environ.get(env_name, "").strip()
    if key:
        return key
    raise RuntimeError(f"{env_name} not found in env or api_env_file")


def list_jpegs(frames_dir: Path) -> List[Path]:
    files = sorted(frames_dir.glob("*.jpg"))
    files += sorted(frames_dir.glob("*.jpeg"))
    files += sorted(frames_dir.glob("*.png"))
    return [p for p in files if p.is_file()]


def next_version(api_dir: Path) -> int:
    vers: List[int] = []
    for d in api_dir.glob("v*"):
        if d.is_dir() and d.name[1:].isdigit():
            vers.append(int(d.name[1:]))
    return max(vers) + 1 if vers else 1


def find_latest_decision(api_dir: Path) -> Path | None:
    vers = []
    for d in api_dir.glob("v*"):
        if d.is_dir() and d.name[1:].isdigit():
            vers.append((int(d.name[1:]), d))
    if not vers:
        return None
    vers.sort(key=lambda x: x[0])
    dec = vers[-1][1] / "decision.json"
    return dec if dec.exists() else None


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def extract_json_object(raw: str) -> Dict[str, Any]:
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    mm = re.search(r"\{.*\}", raw, flags=re.S)
    if not mm:
        raise RuntimeError("metadata response did not contain a JSON object")
    obj = json.loads(mm.group(0))
    if not isinstance(obj, dict):
        raise RuntimeError("metadata response JSON was not an object")
    return obj


def build_crop_context(crop_x: int) -> str:
    return (
        "These frames are cropped from the original 640x360 video.\n"
        f"The fixed crop starts at X = {crop_x}.\n"
        "Only this portrait crop is visible.\n\n"
        "Do not imagine anything outside the crop.\n"
        "Judge the title and description only from the cropped frames."
    )


def call_openai_chat_images(
    api_key: str,
    model: str,
    system: str,
    user_text: str,
    image_paths: List[Path],
    max_tokens: int,
) -> str:
    content: List[Dict[str, Any]] = [{"type": "text", "text": user_text}]
    for img in image_paths:
        mime = "image/png" if img.suffix.lower() == ".png" else "image/jpeg"
        b64 = base64.b64encode(img.read_bytes()).decode("ascii")
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}"},
            }
        )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ],
        "max_tokens": max_tokens,
    }

    cmd = [
        "curl",
        "-sS",
        "https://api.openai.com/v1/chat/completions",
        "-H",
        f"Authorization: Bearer {api_key}",
        "-H",
        "Content-Type: application/json",
        "--data-binary",
        "@-",
    ]
    proc = subprocess.run(
        cmd,
        input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        capture_output=True,
        text=False,
        check=False,
    )

    stderr_text = proc.stderr.decode("utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(f"curl failed rc={proc.returncode}: {stderr_text[:500]}")

    raw = proc.stdout.decode("utf-8", errors="replace").strip()
    if not raw:
        raise RuntimeError(f"empty OpenAI response: {stderr_text[:500]}")

    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"invalid OpenAI response JSON: {e}") from e

    try:
        return str(obj["choices"][0]["message"]["content"])
    except Exception as e:
        raise RuntimeError(f"unexpected OpenAI response: {raw[:800]}") from e


def generate_metadata(
    conf: Dict[str, Any],
    artifact_root: Path,
    event_name: str,
    frames_dir: Path,
    crop_x: int,
    start_sec_rel: int,
    end_sec_rel: int,
    force: bool = False,
) -> Path:
    api_dir = artifact_root / "api"
    api_dir.mkdir(parents=True, exist_ok=True)

    latest = find_latest_decision(api_dir)
    if latest is not None and not force:
        return latest

    imgs = list_jpegs(frames_dir)
    if not imgs:
        raise RuntimeError(f"no JPEGs found in {frames_dir}")

    prompt_path = resolve_optional_path(conf, "prompt_file")
    if prompt_path is None or not prompt_path.exists():
        raise RuntimeError("prompt_file missing")

    system_prompt = build_crop_context(crop_x).strip() + "\n\n" + read_text_any(prompt_path).strip()
    user_text = (
        f"These are cropped still frames for event {event_name}.\n"
        "Return exactly one JSON object with title and description."
    )
    model = str(conf.get("api_model", "gpt-4.1-mini")).strip() or "gpt-4.1-mini"
    api_key = get_api_key(conf)

    version_dir = api_dir / f"v{next_version(api_dir)}"
    version_dir.mkdir(parents=True, exist_ok=True)

    save_json(
        version_dir / "api2_request.json",
        {
            "model": model,
            "system": system_prompt,
            "user_text": user_text,
            "images": [str(p) for p in imgs],
            "crop_x": crop_x,
            "start_sec_rel": start_sec_rel,
            "end_sec_rel": end_sec_rel,
        },
    )

    raw = call_openai_chat_images(
        api_key=api_key,
        model=model,
        system=system_prompt,
        user_text=user_text,
        image_paths=imgs,
        max_tokens=500,
    )
    save_json(version_dir / "api2_response.json", {"raw": raw})

    obj = extract_json_object(raw)
    save_json(version_dir / "api2_response_obj.json", obj)

    title = str(obj.get("title", "")).strip()
    description = str(obj.get("description", "")).strip()
    if not title:
        raise RuntimeError("metadata title was empty")
    if not description:
        raise RuntimeError("metadata description was empty")

    decision = {
        "crop_x": int(crop_x),
        "start_sec_rel": int(start_sec_rel),
        "end_sec_rel": int(end_sec_rel),
        "title": title,
        "description": description,
    }
    save_json(version_dir / "decision.json", decision)
    return version_dir / "decision.json"


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate metadata for WIN_YOLO_PTZ_20S from cropped JPEGs")
    ap.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "config.json"))
    ap.add_argument("--artifact-root", required=True)
    ap.add_argument("--event-name", required=True)
    ap.add_argument("--frames-dir", required=True)
    ap.add_argument("--crop-x", type=int, required=True)
    ap.add_argument("--start-sec-rel", type=int, default=0)
    ap.add_argument("--end-sec-rel", type=int, default=20)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    conf = clone_resolved_config(load_config(args.config))
    decision_path = generate_metadata(
        conf=conf,
        artifact_root=Path(args.artifact_root).resolve(),
        event_name=args.event_name,
        frames_dir=Path(args.frames_dir).resolve(),
        crop_x=args.crop_x,
        start_sec_rel=args.start_sec_rel,
        end_sec_rel=args.end_sec_rel,
        force=args.force,
    )
    print(decision_path)


if __name__ == "__main__":
    main()
