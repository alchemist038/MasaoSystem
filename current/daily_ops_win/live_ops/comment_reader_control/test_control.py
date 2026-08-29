import importlib.machinery
import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("masao_comment_control.pyw")
loader = importlib.machinery.SourceFileLoader("masao_comment_control", str(MODULE_PATH))
spec = importlib.util.spec_from_loader(loader.name, loader)
module = importlib.util.module_from_spec(spec)
sys.modules[loader.name] = module
loader.exec_module(module)


class DeriveModeTests(unittest.TestCase):
    def status(self, listener=True, private=True):
        return module.LocalStatus(True, True, private, listener)

    def test_stopped_if_listener_is_missing(self):
        self.assertEqual(module.derive_mode(self.status(listener=False), {}), "stopped")

    def test_stopped_if_private_bouyomi_is_missing(self):
        self.assertEqual(module.derive_mode(self.status(private=False), {}), "stopped")

    def test_private_when_obs_source_is_muted(self):
        obs = {"sourceExists": True, "sourceMuted": True}
        self.assertEqual(module.derive_mode(self.status(), obs), "private")

    def test_stream_when_obs_source_is_open(self):
        obs = {"sourceExists": True, "sourceMuted": False}
        self.assertEqual(module.derive_mode(self.status(), obs), "stream")


class BluetoothReconnectDetectorTests(unittest.TestCase):
    def test_disconnect_then_reconnect_triggers_once(self):
        detector = module.BluetoothReconnectDetector()
        self.assertIsNone(detector.observe(True))
        self.assertEqual(detector.observe(False), "disconnected")
        self.assertIsNone(detector.observe(False))
        self.assertEqual(detector.observe(True), "reconnected")
        self.assertIsNone(detector.observe(True))

    def test_starting_disconnected_arms_first_connection(self):
        detector = module.BluetoothReconnectDetector()
        self.assertEqual(detector.observe(False), "disconnected")
        self.assertEqual(detector.observe(True), "reconnected")


if __name__ == "__main__":
    unittest.main()
