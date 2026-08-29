from __future__ import annotations

import argparse
import hashlib
import html
import json
import logging
from logging.handlers import RotatingFileHandler
import re
import socket
import struct
import tempfile
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
import winreg


URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
SPACE_RE = re.compile(r"\s+")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u200b-\u200f\u202a-\u202e\u2060\ufeff]")
HONORIFICS = ("さん", "ちゃん", "くん", "君", "さま", "様", "氏")


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReaderConfig:
    config_path: Path
    listen_host: str
    listen_port: int
    allowed_source_ips: frozenset[str]
    bouyomi_host: str
    bouyomi_port: int
    primary_bouyomi_host: str
    primary_bouyomi_port: int
    bluetooth_endpoint_registry_id: str
    obs_scene_collection_dir: Path
    require_obs_desktop_audio_muted: bool
    require_message_id: bool
    max_text_chars: int
    dedupe_capacity: int
    allowed_message_types: frozenset[str]
    excluded_author_names: frozenset[str]
    aliases_path: Path
    state_path: Path
    log_path: Path


def _absolute_from(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else base / path


def load_config(path: Path) -> ReaderConfig:
    raw = json.loads(path.read_text(encoding="utf-8"))
    base = path.parent
    required = (
        "listen_host",
        "listen_port",
        "bouyomi_host",
        "bouyomi_port",
        "primary_bouyomi_host",
        "primary_bouyomi_port",
        "bluetooth_endpoint_registry_id",
        "obs_scene_collection_dir",
    )
    missing = [key for key in required if key not in raw]
    if missing:
        raise ConfigError(f"Missing config keys: {', '.join(missing)}")

    return ReaderConfig(
        config_path=path,
        listen_host=str(raw["listen_host"]),
        listen_port=int(raw["listen_port"]),
        allowed_source_ips=frozenset(str(v) for v in raw.get("allowed_source_ips", [])),
        bouyomi_host=str(raw["bouyomi_host"]),
        bouyomi_port=int(raw["bouyomi_port"]),
        primary_bouyomi_host=str(raw["primary_bouyomi_host"]),
        primary_bouyomi_port=int(raw["primary_bouyomi_port"]),
        bluetooth_endpoint_registry_id=str(raw["bluetooth_endpoint_registry_id"]),
        obs_scene_collection_dir=_absolute_from(base, str(raw["obs_scene_collection_dir"])),
        require_obs_desktop_audio_muted=bool(raw.get("require_obs_desktop_audio_muted", True)),
        require_message_id=bool(raw.get("require_message_id", True)),
        max_text_chars=max(20, int(raw.get("max_text_chars", 140))),
        dedupe_capacity=max(100, int(raw.get("dedupe_capacity", 5000))),
        allowed_message_types=frozenset(str(v) for v in raw.get("allowed_message_types", ["textMessageEvent"])),
        excluded_author_names=frozenset(str(v).casefold() for v in raw.get("excluded_author_names", [])),
        aliases_path=_absolute_from(base, str(raw.get("aliases_path", "aliases.json"))),
        state_path=_absolute_from(base, str(raw.get("state_path", "state\\dedupe.json"))),
        log_path=_absolute_from(base, str(raw.get("log_path", "logs\\comment_reader.log"))),
    )


def build_logger(path: Path) -> logging.Logger:
    path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("masao.comment_reader")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    file_handler = RotatingFileHandler(path, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)
    return logger


def load_alias_data(path: Path) -> tuple[dict[str, str], frozenset[str]]:
    if not path.exists():
        return {}, frozenset()
    raw = json.loads(path.read_text(encoding="utf-8"))
    aliases = {str(k): str(v).strip() for k, v in raw.get("aliases", {}).items() if str(v).strip()}
    excluded = frozenset(str(v) for v in raw.get("excluded_author_channel_ids", []))
    return aliases, excluded


def clean_text(value: Any, max_chars: int) -> str:
    text = html.unescape(str(value or ""))
    text = CONTROL_RE.sub("", text)
    text = URL_RE.sub(" リンク ", text)
    text = SPACE_RE.sub(" ", text).strip()
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "。以下省略"
    return text


def spoken_author(name: str) -> str:
    normalized = SPACE_RE.sub(" ", CONTROL_RE.sub("", name)).strip() or "視聴者"
    if normalized.endswith(HONORIFICS):
        return normalized
    return normalized + "さん"


def format_spoken_text(author: str, text: str) -> str:
    return f"{spoken_author(author)}から。{text}"


class RecentMessageIds:
    def __init__(self, path: Path, capacity: int):
        self.path = path
        self.capacity = capacity
        self._ids: deque[str] = deque()
        self._set: set[str] = set()
        self._lock = threading.Lock()
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            for message_id in raw.get("message_ids", [])[-self.capacity :]:
                value = str(message_id)
                if value and value not in self._set:
                    self._ids.append(value)
                    self._set.add(value)
        except (OSError, json.JSONDecodeError):
            return

    def remember_new(self, message_id: str) -> bool:
        with self._lock:
            if message_id in self._set:
                return False
            self._ids.append(message_id)
            self._set.add(message_id)
            while len(self._ids) > self.capacity:
                expired = self._ids.popleft()
                self._set.discard(expired)
            self._save_locked()
            return True

    def _save_locked(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({"message_ids": list(self._ids)}, ensure_ascii=False, indent=2)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.path.parent, delete=False) as handle:
            handle.write(payload)
            temp_path = Path(handle.name)
        temp_path.replace(self.path)


class SafetyGate:
    RENDER_REGISTRY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render"

    def __init__(self, config: ReaderConfig):
        self.config = config
        self._obs_cache_time = 0.0
        self._obs_cache_result: tuple[bool, str] = (False, "obs_not_checked")

    def check(self) -> tuple[bool, str]:
        if not self._bluetooth_active():
            return False, "bluetooth_inactive"
        if self.config.require_obs_desktop_audio_muted:
            obs_ok, reason = self._obs_desktop_audio_safe()
            if not obs_ok:
                return False, reason
        return True, "safe"

    def _bluetooth_active(self) -> bool:
        subkey = f"{self.RENDER_REGISTRY}\\{self.config.bluetooth_endpoint_registry_id}"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey) as key:
                state, _ = winreg.QueryValueEx(key, "DeviceState")
            return int(state) == 1
        except OSError:
            return False

    def _obs_desktop_audio_safe(self) -> tuple[bool, str]:
        now = time.monotonic()
        if now - self._obs_cache_time < 1.0:
            return self._obs_cache_result

        candidates = sorted(
            (path for path in self.config.obs_scene_collection_dir.glob("*.json") if path.is_file()),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            result = (False, "obs_scene_collection_missing")
        else:
            try:
                raw = json.loads(candidates[0].read_text(encoding="utf-8-sig"))
                desktop = raw.get("DesktopAudioDevice1") or {}
                muted = desktop.get("muted") is True
                volume = float(desktop.get("volume", 1.0))
                result = (True, "obs_desktop_audio_muted") if muted and volume <= 0.0001 else (False, "obs_desktop_audio_not_muted")
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                result = (False, "obs_scene_collection_unreadable")

        self._obs_cache_time = now
        self._obs_cache_result = result
        return result


class BouyomiSender:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def send(self, text: str) -> None:
        payload = text.encode("utf-8")
        header = struct.pack("<hhhhhbi", 0x0001, -1, -1, -1, 0, 0, len(payload))
        with socket.create_connection((self.host, self.port), timeout=1.0) as sock:
            sock.sendall(header + payload)


class CommentProcessor:
    def __init__(
        self,
        config: ReaderConfig,
        logger: logging.Logger,
        gate: SafetyGate,
        sender: BouyomiSender,
        dedupe: RecentMessageIds,
        alias_loader: Callable[[Path], tuple[dict[str, str], frozenset[str]]] = load_alias_data,
    ):
        self.config = config
        self.logger = logger
        self.gate = gate
        self.sender = sender
        self.dedupe = dedupe
        self.alias_loader = alias_loader

    def process(self, payload: dict[str, Any]) -> str:
        message_id = str(payload.get("message_id") or "").strip()
        if not message_id and self.config.require_message_id:
            self.logger.warning("DROP reason=missing_message_id")
            return "missing_message_id"
        if not message_id:
            seed = "|".join(str(payload.get(k) or "") for k in ("author_channel_id", "published_at", "text"))
            message_id = "derived:" + hashlib.sha256(seed.encode("utf-8")).hexdigest()

        message_type = str(payload.get("message_type") or "textMessageEvent")
        if message_type not in self.config.allowed_message_types:
            self.logger.info("DROP id=%s reason=message_type type=%s", message_id, message_type)
            return "message_type"

        author_id = str(payload.get("author_channel_id") or "").strip()
        display_name = str(payload.get("author") or payload.get("author_display_name") or "").strip()
        aliases, excluded_ids = self.alias_loader(self.config.aliases_path)
        if author_id in excluded_ids:
            self.logger.info("DROP id=%s reason=excluded_author_id", message_id)
            return "excluded_author_id"
        if display_name.casefold() in self.config.excluded_author_names:
            self.logger.info("DROP id=%s reason=excluded_author_name", message_id)
            return "excluded_author_name"
        if bool(payload.get("is_owner")) or bool(payload.get("is_bot")) or bool(payload.get("is_system")):
            self.logger.info("DROP id=%s reason=owner_bot_or_system", message_id)
            return "owner_bot_or_system"

        text = clean_text(payload.get("text"), self.config.max_text_chars)
        if not text:
            self.logger.info("DROP id=%s reason=empty_text", message_id)
            return "empty_text"

        # Remember before the safety check so comments received while the earphones
        # are disconnected are discarded instead of spoken later as stale backlog.
        if not self.dedupe.remember_new(message_id):
            self.logger.info("DROP id=%s reason=duplicate", message_id)
            return "duplicate"

        safe, reason = self.gate.check()
        if not safe:
            self.logger.warning("DROP id=%s reason=%s", message_id, reason)
            return reason

        author = aliases.get(author_id) or display_name or "視聴者"
        spoken = format_spoken_text(author, text)
        try:
            self.sender.send(spoken)
        except OSError as exc:
            self.logger.error("DROP id=%s reason=bouyomi_send_error error=%s", message_id, type(exc).__name__)
            return "bouyomi_send_error"

        self.logger.info("SPOKEN id=%s author_id=%s chars=%d", message_id, author_id or "unknown", len(spoken))
        return "spoken"


def source_ip_allowed(config: ReaderConfig, peer_ip: str) -> bool:
    return (
        not config.allowed_source_ips
        or peer_ip in config.allowed_source_ips
        or peer_ip == config.listen_host
    )


def handle_client(
    connection: socket.socket,
    address: tuple[str, int],
    config: ReaderConfig,
    processor: CommentProcessor,
    logger: logging.Logger,
) -> None:
    peer_ip = address[0]
    if not source_ip_allowed(config, peer_ip):
        logger.warning("REJECT peer=%s reason=source_ip", peer_ip)
        connection.close()
        return

    logger.info("CONNECT peer=%s", peer_ip)
    try:
        with connection, connection.makefile("r", encoding="utf-8", errors="replace", newline="\n") as stream:
            for line in stream:
                if len(line) > 65_536:
                    logger.warning("DROP peer=%s reason=line_too_long", peer_ip)
                    continue
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning("DROP peer=%s reason=invalid_json", peer_ip)
                    continue
                if not isinstance(payload, dict):
                    logger.warning("DROP peer=%s reason=json_not_object", peer_ip)
                    continue
                processor.process(payload)
    except OSError as exc:
        logger.warning("DISCONNECT peer=%s error=%s", peer_ip, type(exc).__name__)
    finally:
        logger.info("DISCONNECT peer=%s", peer_ip)


def serve(config: ReaderConfig) -> None:
    logger = build_logger(config.log_path)
    gate = SafetyGate(config)
    sender = BouyomiSender(config.bouyomi_host, config.bouyomi_port)
    dedupe = RecentMessageIds(config.state_path, config.dedupe_capacity)
    processor = CommentProcessor(config, logger, gate, sender, dedupe)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((config.listen_host, config.listen_port))
        server.listen(16)
        logger.info("LISTEN address=%s:%d", config.listen_host, config.listen_port)
        while True:
            connection, address = server.accept()
            thread = threading.Thread(
                target=handle_client,
                args=(connection, address, config, processor, logger),
                daemon=True,
            )
            thread.start()


def main() -> None:
    parser = argparse.ArgumentParser(description="Masao private live-comment reader")
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    serve(load_config(args.config.resolve()))


if __name__ == "__main__":
    main()
