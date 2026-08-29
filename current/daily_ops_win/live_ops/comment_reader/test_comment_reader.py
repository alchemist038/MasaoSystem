import json
import logging
from pathlib import Path
import socket
import struct
import tempfile
import threading
import unittest

from comment_reader import (
    BouyomiSender,
    CommentProcessor,
    ReaderConfig,
    RecentMessageIds,
    clean_text,
    format_spoken_text,
    handle_client,
    source_ip_allowed,
)


class FakeGate:
    def __init__(self, result=(True, "safe")):
        self.result = result

    def check(self):
        return self.result


class FakeSender:
    def __init__(self):
        self.messages = []

    def send(self, text):
        self.messages.append(text)


def config_for(root: Path) -> ReaderConfig:
    aliases = root / "aliases.json"
    aliases.write_text(
        json.dumps(
            {
                "aliases": {"channel-a": "つくねさん"},
                "excluded_author_channel_ids": ["bot-channel"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return ReaderConfig(
        config_path=root / "config.json",
        listen_host="127.0.0.1",
        listen_port=50002,
        allowed_source_ips=frozenset({"127.0.0.1"}),
        bouyomi_host="127.0.0.1",
        bouyomi_port=50003,
        primary_bouyomi_host="127.0.0.1",
        primary_bouyomi_port=50001,
        bluetooth_endpoint_registry_id="{test}",
        obs_scene_collection_dir=root,
        require_obs_desktop_audio_muted=True,
        require_message_id=True,
        max_text_chars=40,
        dedupe_capacity=100,
        allowed_message_types=frozenset({"textMessageEvent"}),
        excluded_author_names=frozenset({"gpt太郎"}),
        aliases_path=aliases,
        state_path=root / "state" / "dedupe.json",
        log_path=root / "logs" / "test.log",
    )


class CommentReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = config_for(self.root)
        self.logger = logging.getLogger(f"test.{id(self)}")
        self.logger.addHandler(logging.NullHandler())
        self.sender = FakeSender()
        self.dedupe = RecentMessageIds(self.config.state_path, self.config.dedupe_capacity)

    def tearDown(self):
        self.temp.cleanup()

    def processor(self, gate=(True, "safe")):
        return CommentProcessor(
            self.config,
            self.logger,
            FakeGate(gate),
            self.sender,
            self.dedupe,
        )

    def test_formats_alias_without_double_honorific(self):
        result = self.processor().process(
            {
                "message_id": "m1",
                "author_channel_id": "channel-a",
                "author": "unused",
                "text": "こんにちは",
                "message_type": "textMessageEvent",
            }
        )
        self.assertEqual(result, "spoken")
        self.assertEqual(self.sender.messages, ["つくねさんから。こんにちは"])

    def test_duplicate_is_spoken_once(self):
        payload = {
            "message_id": "m2",
            "author_channel_id": "channel-b",
            "author": "ポン太",
            "text": "かわいい",
            "message_type": "textMessageEvent",
        }
        processor = self.processor()
        self.assertEqual(processor.process(payload), "spoken")
        self.assertEqual(processor.process(payload), "duplicate")
        self.assertEqual(len(self.sender.messages), 1)

    def test_owner_and_bot_are_not_spoken(self):
        processor = self.processor()
        owner = {"message_id": "m3", "author": "まさお", "text": "test", "is_owner": True}
        bot = {"message_id": "m4", "author_channel_id": "bot-channel", "author": "bot", "text": "test"}
        self.assertEqual(processor.process(owner), "owner_bot_or_system")
        self.assertEqual(processor.process(bot), "excluded_author_id")
        self.assertEqual(self.sender.messages, [])

    def test_inactive_bluetooth_discards_without_backlog(self):
        payload = {"message_id": "m5", "author": "視聴者", "text": "今ゴロンした"}
        self.assertEqual(self.processor((False, "bluetooth_inactive")).process(payload), "bluetooth_inactive")
        self.assertEqual(self.processor().process(payload), "duplicate")
        self.assertEqual(self.sender.messages, [])

    def test_text_cleanup(self):
        self.assertEqual(clean_text("  URL https://example.com\nです  ", 40), "URL リンク です")
        self.assertEqual(format_spoken_text("ポン太", "こんにちは"), "ポン太さんから。こんにちは")

    def test_listener_accepts_only_configured_or_self_source(self):
        self.assertTrue(source_ip_allowed(self.config, "127.0.0.1"))
        self.assertFalse(source_ip_allowed(self.config, "100.124.36.99"))

        self_source_config = ReaderConfig(
            **{
                **self.config.__dict__,
                "listen_host": "100.106.183.15",
                "allowed_source_ips": frozenset({"100.124.36.15"}),
            }
        )
        self.assertTrue(source_ip_allowed(self_source_config, "100.106.183.15"))

    def test_json_line_reaches_separate_bouyomi_socket(self):
        received = []
        ready = threading.Event()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as fake_bouyomi:
            fake_bouyomi.bind(("127.0.0.1", 0))
            fake_bouyomi.listen(1)
            bouyomi_port = fake_bouyomi.getsockname()[1]

            def receive_bouyomi_packet():
                ready.set()
                connection, _ = fake_bouyomi.accept()
                with connection:
                    header = b""
                    while len(header) < 15:
                        header += connection.recv(15 - len(header))
                    _, _, _, _, _, _, text_length = struct.unpack("<hhhhhbi", header)
                    payload = b""
                    while len(payload) < text_length:
                        payload += connection.recv(text_length - len(payload))
                    received.append(payload.decode("utf-8"))

            bouyomi_thread = threading.Thread(target=receive_bouyomi_packet)
            bouyomi_thread.start()
            ready.wait(1)

            processor = CommentProcessor(
                self.config,
                self.logger,
                FakeGate(),
                BouyomiSender("127.0.0.1", bouyomi_port),
                self.dedupe,
            )
            receiver, sender = socket.socketpair()
            receiver_thread = threading.Thread(
                target=handle_client,
                args=(receiver, ("127.0.0.1", 12345), self.config, processor, self.logger),
            )
            receiver_thread.start()
            sender.sendall(
                (
                    json.dumps(
                        {
                            "message_id": "socket-m1",
                            "author_channel_id": "channel-b",
                            "author": "ポン太",
                            "text": "今ゴロンした",
                            "message_type": "textMessageEvent",
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                ).encode("utf-8")
            )
            sender.close()
            receiver_thread.join(2)
            bouyomi_thread.join(2)

        self.assertEqual(received, ["ポン太さんから。今ゴロンした"])


if __name__ == "__main__":
    unittest.main()
