from __future__ import annotations

import argparse
import ctypes
import json
import os
import queue
import socket
import subprocess
import sys
import threading
import time
import uuid
import winreg
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import tkinter as tk
from tkinter import messagebox, ttk

import psutil


APP_TITLE = "まさお コメント読み上げ"
APP_VERSION = "1.1.0"
RUNTIME_DIR = Path(r"C:\masao\comment_reader")
CONTROL_DIR = Path(r"C:\masao\comment_reader_control")
CONTROL_LOG_PATH = CONTROL_DIR / "control.log"
CONFIG_PATH = RUNTIME_DIR / "config.json"
LOG_PATH = RUNTIME_DIR / "logs" / "comment_reader.log"
START_SCRIPT = RUNTIME_DIR / "start_comment_reader.ps1"
STOP_SCRIPT = RUNTIME_DIR / "stop_comment_reader.ps1"
OBS_BRIDGE = CONTROL_DIR / "obs_bridge.js"
POWERSHELL = Path(r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe")
NODE = "node.exe"
CREATE_NO_WINDOW = 0x08000000
ERROR_ALREADY_EXISTS = 183
_MUTEX_HANDLE: int | None = None


@dataclass(frozen=True)
class LocalStatus:
    shokz: bool
    stream_bouyomi: bool
    private_bouyomi: bool
    listener: bool


@dataclass
class BluetoothReconnectDetector:
    previous_active: bool | None = None
    reconnect_armed: bool = False

    def observe(self, active: bool) -> str | None:
        if self.previous_active is None:
            self.previous_active = active
            self.reconnect_armed = not active
            return "disconnected" if not active else None
        event = None
        if self.previous_active and not active:
            self.reconnect_armed = True
            event = "disconnected"
        elif not self.previous_active and active and self.reconnect_armed:
            self.reconnect_armed = False
            event = "reconnected"
        self.previous_active = active
        return event


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))


def write_control_log(message: str) -> None:
    CONTROL_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with CONTROL_LOG_PATH.open("a", encoding="utf-8") as stream:
        stream.write(f"{timestamp} {message}\n")


def listening_ports() -> set[int]:
    ports: set[int] = set()
    for connection in psutil.net_connections(kind="tcp"):
        if connection.status == psutil.CONN_LISTEN and connection.laddr:
            ports.add(int(connection.laddr.port))
    return ports


def bluetooth_active(endpoint_id: str) -> bool:
    path = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render\{endpoint_id}"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            state, _ = winreg.QueryValueEx(key, "DeviceState")
        return int(state) == 1
    except OSError:
        return False


def read_local_status() -> LocalStatus:
    config = load_config()
    ports = listening_ports()
    return LocalStatus(
        shokz=bluetooth_active(str(config["bluetooth_endpoint_registry_id"])),
        stream_bouyomi=int(config["primary_bouyomi_port"]) in ports,
        private_bouyomi=int(config["bouyomi_port"]) in ports,
        listener=int(config["listen_port"]) in ports,
    )


def run_command(command: list[str], timeout: float = 25.0) -> str:
    completed = subprocess.run(
        command,
        cwd=str(CONTROL_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        creationflags=CREATE_NO_WINDOW,
        check=False,
    )
    output = (completed.stdout or "").strip()
    error = (completed.stderr or "").strip()
    if completed.returncode != 0:
        raise RuntimeError(error or output or f"Command failed: {completed.returncode}")
    return output


def run_powershell(script: Path) -> str:
    command = (
        "[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false); "
        f"try {{ & '{script}' }} catch {{ "
        "[Console]::Error.WriteLine($_.Exception.Message); exit 1 }"
    )
    return run_command(
        [
            str(POWERSHELL),
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        timeout=35.0,
    )


def run_obs(command: str, allow_unavailable: bool = False) -> dict[str, Any]:
    try:
        output = run_command([NODE, str(OBS_BRIDGE), command], timeout=12.0)
        return json.loads(output)
    except RuntimeError as exc:
        unavailable = "WebSocket open error" in str(exc) or "ECONNREFUSED" in str(exc)
        if allow_unavailable and unavailable:
            return {"obsConnected": False}
        raise


def derive_mode(local: LocalStatus, obs: dict[str, Any]) -> str:
    if not local.listener or not local.private_bouyomi:
        return "stopped"
    if obs.get("sourceExists") and not obs.get("sourceMuted", True):
        return "stream"
    return "private"


def send_test_comment() -> None:
    config = load_config()
    payload = {
        "message_id": f"control-test-{uuid.uuid4().hex}",
        "message_type": "textMessageEvent",
        "author_channel_id": "masao-control-local-test",
        "author": "接続テスト",
        "text": "読み上げテストです",
        "published_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "is_owner": False,
        "is_bot": False,
        "is_system": False,
    }
    data = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
    with socket.create_connection(
        (str(config["listen_host"]), int(config["listen_port"])), timeout=1.0
    ) as client:
        client.sendall(data)


def tail_log(lines: int = 8) -> str:
    if not LOG_PATH.exists():
        return "ログはまだありません。"
    content = LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(content[-lines:])


class CommentControlApp:
    BG = "#f3f5f7"
    PANEL = "#ffffff"
    TEXT = "#17212b"
    MUTED = "#63707c"
    GREEN = "#16835f"
    RED = "#c43d3d"
    AMBER = "#b56a13"
    BLUE = "#2368a2"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"{APP_TITLE}  v{APP_VERSION}")
        self.root.geometry("760x620")
        self.root.minsize(700, 570)
        self.root.configure(bg=self.BG)
        self.root.protocol("WM_DELETE_WINDOW", self._close_app)
        self.events: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.busy = False
        self.polling = False
        self.requested_mode = ""
        self.bt_reconnect_pending = False
        self.bt_stop_event = threading.Event()
        self.status_labels: dict[str, tk.Label] = {}
        self.mode_buttons: dict[str, tk.Button] = {}
        self._build_styles()
        self._build_ui()
        self.root.after(100, self._drain_events)
        self.root.after(250, self.refresh_status)
        threading.Thread(target=self._bt_monitor_loop, daemon=True).start()

    def _build_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TProgressbar", thickness=4, troughcolor=self.BG, background=self.BLUE)

    def _panel(self, parent: tk.Widget, **kwargs: Any) -> tk.Frame:
        return tk.Frame(parent, bg=self.PANEL, highlightthickness=1, highlightbackground="#d9dee3", **kwargs)

    def _build_ui(self) -> None:
        header = tk.Frame(self.root, bg="#1f2933", height=78)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text=APP_TITLE,
            bg="#1f2933",
            fg="white",
            font=("Yu Gothic UI", 19, "bold"),
        ).pack(anchor="w", padx=24, pady=(13, 0))
        self.summary_label = tk.Label(
            header,
            text="状態を確認しています",
            bg="#1f2933",
            fg="#cbd5df",
            font=("Yu Gothic UI", 10),
        )
        self.summary_label.pack(anchor="w", padx=25, pady=(1, 0))

        body = tk.Frame(self.root, bg=self.BG)
        body.pack(fill="both", expand=True, padx=20, pady=16)

        mode_panel = self._panel(body)
        mode_panel.pack(fill="x")
        tk.Label(
            mode_panel,
            text="読み上げモード",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Yu Gothic UI", 12, "bold"),
        ).pack(anchor="w", padx=16, pady=(12, 8))
        mode_row = tk.Frame(mode_panel, bg=self.PANEL)
        mode_row.pack(fill="x", padx=14, pady=(0, 14))
        modes = [
            ("stopped", "停止", self.RED),
            ("private", "イヤホンのみ", self.GREEN),
            ("stream", "イヤホン＋配信", self.BLUE),
        ]
        for index, (key, label, color) in enumerate(modes):
            button = tk.Button(
                mode_row,
                text=label,
                command=lambda selected=key: self.set_mode(selected),
                bg="#e7ebef",
                fg=self.TEXT,
                activebackground=color,
                activeforeground="white",
                relief="flat",
                bd=0,
                font=("Yu Gothic UI", 11, "bold"),
                cursor="hand2",
                height=2,
            )
            button.grid(row=0, column=index, sticky="ew", padx=4)
            mode_row.grid_columnconfigure(index, weight=1, uniform="mode")
            self.mode_buttons[key] = button

        status_panel = self._panel(body)
        status_panel.pack(fill="x", pady=(12, 0))
        tk.Label(
            status_panel,
            text="接続状態",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Yu Gothic UI", 12, "bold"),
        ).pack(anchor="w", padx=16, pady=(12, 7))
        status_grid = tk.Frame(status_panel, bg=self.PANEL)
        status_grid.pack(fill="x", padx=16, pady=(0, 13))
        labels = [
            ("shokz", "BTヘッドセット"),
            ("stream_bouyomi", "太郎・五郎"),
            ("private_bouyomi", "コメント音声"),
            ("listener", "コメント受信"),
            ("obs", "OBS"),
        ]
        for index, (key, title) in enumerate(labels):
            cell = tk.Frame(status_grid, bg="#f7f8fa", padx=8, pady=8)
            cell.grid(row=0, column=index, sticky="nsew", padx=3)
            status_grid.grid_columnconfigure(index, weight=1, uniform="status")
            tk.Label(
                cell,
                text=title,
                bg="#f7f8fa",
                fg=self.MUTED,
                font=("Yu Gothic UI", 9),
            ).pack()
            value = tk.Label(
                cell,
                text="確認中",
                bg="#f7f8fa",
                fg=self.MUTED,
                font=("Yu Gothic UI", 10, "bold"),
            )
            value.pack(pady=(3, 0))
            self.status_labels[key] = value

        control_panel = self._panel(body)
        control_panel.pack(fill="x", pady=(12, 0))
        tk.Label(
            control_panel,
            text="操作",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Yu Gothic UI", 12, "bold"),
        ).pack(anchor="w", padx=16, pady=(12, 7))
        controls = tk.Frame(control_panel, bg=self.PANEL)
        controls.pack(fill="x", padx=14, pady=(0, 8))
        actions = [
            ("起動", lambda: self.set_mode("private")),
            ("再起動", self.restart_services),
            ("停止", lambda: self.set_mode("stopped")),
            ("読み上げテスト", self.test_audio),
            ("緊急ミュート", self.emergency_mute),
        ]
        for index, (label, command) in enumerate(actions):
            button = tk.Button(
                controls,
                text=label,
                command=command,
                bg="#e8edf1" if label != "緊急ミュート" else "#f7dddd",
                fg=self.TEXT if label != "緊急ミュート" else self.RED,
                activebackground="#d7dfe6",
                relief="flat",
                bd=0,
                font=("Yu Gothic UI", 9, "bold"),
                cursor="hand2",
                height=2,
            )
            button.grid(row=0, column=index, sticky="ew", padx=3)
            controls.grid_columnconfigure(index, weight=1, uniform="control")
        self.progress = ttk.Progressbar(control_panel, mode="indeterminate")
        self.progress.pack(fill="x", padx=17, pady=(2, 12))
        self.progress.pack_forget()

        log_panel = self._panel(body)
        log_panel.pack(fill="both", expand=True, pady=(12, 0))
        log_header = tk.Frame(log_panel, bg=self.PANEL)
        log_header.pack(fill="x", padx=16, pady=(10, 5))
        tk.Label(
            log_header,
            text="直近の動作",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Yu Gothic UI", 11, "bold"),
        ).pack(side="left")
        tk.Button(
            log_header,
            text="ログを開く",
            command=self.open_log,
            bg=self.PANEL,
            fg=self.BLUE,
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Yu Gothic UI", 9),
        ).pack(side="right")
        self.log_text = tk.Text(
            log_panel,
            height=7,
            bg="#111820",
            fg="#d5dde5",
            insertbackground="white",
            relief="flat",
            bd=0,
            padx=10,
            pady=8,
            font=("Consolas", 9),
            state="disabled",
            wrap="none",
        )
        self.log_text.pack(fill="both", expand=True, padx=16, pady=(0, 14))

    def _set_busy(self, busy: bool, text: str = "") -> None:
        self.busy = busy
        if busy:
            self.progress.pack(fill="x", padx=17, pady=(2, 12))
            self.progress.start(12)
            self.summary_label.configure(text=text or "処理しています")
        else:
            self.progress.stop()
            self.progress.configure(value=0)
            self.progress.pack_forget()

    def _run_background(
        self, label: str, action: Callable[[], Any], on_success: Callable[[Any], None] | None = None
    ) -> None:
        if self.busy:
            return
        self._set_busy(True, label)

        def worker() -> None:
            try:
                result = action()
                self.events.put(("success", (label, result, on_success)))
            except Exception as exc:  # UI boundary: show a concise operation error.
                self.events.put(("error", (label, str(exc))))

        threading.Thread(target=worker, daemon=True).start()

    def _drain_events(self) -> None:
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "status":
                    local, obs = payload
                    self._apply_status(local, obs)
                    self.polling = False
                elif kind == "success":
                    label, result, callback = payload
                    self._set_busy(False)
                    self.summary_label.configure(text=f"{label}が完了しました")
                    if callback:
                        callback(result)
                    self.refresh_status(force=True)
                    self._try_bt_reconnect()
                elif kind == "error":
                    label, detail = payload
                    self._set_busy(False)
                    self.summary_label.configure(text=f"{label}に失敗しました")
                    messagebox.showerror(APP_TITLE, f"{label}に失敗しました。\n\n{detail}")
                    self.refresh_status(force=True)
                    self._try_bt_reconnect()
                elif kind == "bt_disconnected":
                    write_control_log("Bluetooth disconnected; automatic restart armed")
                    if not self.busy:
                        self.summary_label.configure(
                            text="BT切断を検知しました。再接続時に音声を再起動します"
                        )
                elif kind == "bt_reconnected":
                    write_control_log("Bluetooth reconnected; automatic restart requested")
                    self.bt_reconnect_pending = True
                    self._try_bt_reconnect()
        except queue.Empty:
            pass
        self.root.after(100, self._drain_events)

    def _bt_monitor_loop(self) -> None:
        try:
            endpoint_id = str(load_config()["bluetooth_endpoint_registry_id"])
            detector = BluetoothReconnectDetector()
            while not self.bt_stop_event.is_set():
                event = detector.observe(bluetooth_active(endpoint_id))
                if event:
                    self.events.put((f"bt_{event}", None))
                self.bt_stop_event.wait(1.0)
        except Exception as exc:
            write_control_log(f"Bluetooth monitor stopped: {type(exc).__name__}: {exc}")

    def _try_bt_reconnect(self) -> None:
        if not self.bt_reconnect_pending or self.busy:
            return
        self.bt_reconnect_pending = False

        def action() -> dict[str, Any]:
            local = read_local_status()
            if not (local.listener and local.private_bouyomi):
                write_control_log("Bluetooth reconnect restart skipped; private reader is stopped")
                return {"skipped": True}
            obs = run_obs("status", allow_unavailable=True)
            restore_stream = bool(
                obs.get("obsConnected")
                and obs.get("sourceExists")
                and not obs.get("sourceMuted", True)
            )
            write_control_log(
                f"Bluetooth reconnect restart started; restore_stream={restore_stream}"
            )
            run_obs("stream-off", allow_unavailable=True)
            run_powershell(STOP_SCRIPT)
            time.sleep(1.5)
            run_powershell(START_SCRIPT)
            if restore_stream:
                run_obs("stream-on")
            else:
                run_obs("ensure-private", allow_unavailable=True)
            write_control_log(
                f"Bluetooth reconnect restart completed; restore_stream={restore_stream}"
            )
            return {"skipped": False, "restore_stream": restore_stream}

        self._run_background("BT再接続後の音声を再初期化", action)

    def _close_app(self) -> None:
        self.bt_stop_event.set()
        self.root.destroy()

    def refresh_status(self, force: bool = False) -> None:
        if (self.polling or self.busy) and not force:
            self.root.after(2500, self.refresh_status)
            return
        self.polling = True

        def worker() -> None:
            try:
                local = read_local_status()
                obs = run_obs("status", allow_unavailable=True)
                self.events.put(("status", (local, obs)))
            except Exception:
                self.polling = False

        threading.Thread(target=worker, daemon=True).start()
        self.root.after(5000, self.refresh_status)

    def _status_value(self, key: str, active: bool, good_text: str = "正常") -> None:
        label = self.status_labels[key]
        label.configure(text=good_text if active else "停止", fg=self.GREEN if active else self.RED)

    def _apply_status(self, local: LocalStatus, obs: dict[str, Any]) -> None:
        self._status_value("shokz", local.shokz, "接続中")
        self._status_value("stream_bouyomi", local.stream_bouyomi)
        self._status_value("private_bouyomi", local.private_bouyomi)
        self._status_value("listener", local.listener)
        obs_connected = bool(obs.get("obsConnected"))
        self._status_value("obs", obs_connected, "配信中" if obs.get("streamActive") else "接続中")

        mode = derive_mode(local, obs)
        colors = {"stopped": self.RED, "private": self.GREEN, "stream": self.BLUE}
        for key, button in self.mode_buttons.items():
            selected = key == mode
            button.configure(
                bg=colors[key] if selected else "#e7ebef",
                fg="white" if selected else self.TEXT,
            )
        summaries = {
            "stopped": "コメント読み上げは停止しています",
            "private": "コメントはイヤホンだけに流れています",
            "stream": "コメントはイヤホンと配信に流れています",
        }
        if not self.busy:
            self.summary_label.configure(text=summaries[mode])
        self._update_log()

        if mode == "stream" and obs_connected and not obs.get("sourceInCurrentScene", False):
            self._run_background("配信音声を現在のシーンへ接続", lambda: run_obs("stream-on"))

    def _update_log(self) -> None:
        try:
            content = tail_log()
        except OSError:
            content = "ログを読み込めません。"
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("1.0", content)
        self.log_text.configure(state="disabled")
        self.log_text.see("end")

    def set_mode(self, mode: str) -> None:
        labels = {"stopped": "停止", "private": "イヤホンのみへ切替", "stream": "配信へ切替"}

        def action() -> None:
            local = read_local_status()
            if mode == "stopped":
                run_obs("stream-off", allow_unavailable=True)
                if local.listener or local.private_bouyomi:
                    run_powershell(STOP_SCRIPT)
                return
            if not (local.listener and local.private_bouyomi):
                if local.listener or local.private_bouyomi:
                    run_obs("stream-off", allow_unavailable=True)
                    run_powershell(STOP_SCRIPT)
                run_powershell(START_SCRIPT)
            if mode == "private":
                run_obs("ensure-private", allow_unavailable=True)
            else:
                run_obs("stream-on")

        self._run_background(labels[mode], action)

    def restart_services(self) -> None:
        def action() -> None:
            run_obs("stream-off", allow_unavailable=True)
            local = read_local_status()
            if local.listener or local.private_bouyomi:
                run_powershell(STOP_SCRIPT)
            run_powershell(START_SCRIPT)
            run_obs("ensure-private", allow_unavailable=True)

        self._run_background("コメント音声を再起動", action)

    def emergency_mute(self) -> None:
        self._run_background("配信音声を緊急ミュート", lambda: run_obs("stream-off"))

    def test_audio(self) -> None:
        self._run_background("読み上げテストを送信", send_test_comment)

    def open_log(self) -> None:
        if not LOG_PATH.exists():
            messagebox.showinfo(APP_TITLE, "ログはまだありません。")
            return
        os.startfile(LOG_PATH)


def status_json() -> int:
    local = read_local_status()
    obs = run_obs("status", allow_unavailable=True)
    print(
        json.dumps(
            {
                "version": APP_VERSION,
                "mode": derive_mode(local, obs),
                "local": local.__dict__,
                "obs": obs,
            },
            ensure_ascii=True,
        )
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--status-json", action="store_true")
    return parser.parse_args()


def claim_single_instance() -> bool:
    global _MUTEX_HANDLE
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    handle = kernel32.CreateMutexW(None, False, "Local\\MasaoCommentReaderControl")
    if not handle:
        return False
    _MUTEX_HANDLE = int(handle)
    return kernel32.GetLastError() != ERROR_ALREADY_EXISTS


def main() -> int:
    args = parse_args()
    if args.status_json:
        return status_json()
    if not claim_single_instance():
        ctypes.windll.user32.MessageBoxW(
            None,
            "すでに起動しています。",
            APP_TITLE,
            0x00000040,
        )
        return 0
    root = tk.Tk()
    CommentControlApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
