import unittest
from datetime import time

from youtube_live_broadcasts import broadcast_body, iso_at, parse_date, parts_for


class BroadcastBodyTests(unittest.TestCase):
    def test_all_parts_use_low_latency(self):
        day = parse_date("2026-09-07")
        parts = parts_for(time(7), time(17), time(17), time(23))
        self.assertEqual([part.key for part in parts], ["part1", "part2", "part3"])
        for part in parts:
            with self.subTest(part=part.key):
                body = broadcast_body(part, day, "public")
                self.assertEqual(body["contentDetails"]["latencyPreference"], "low")

    def test_schedule_privacy_and_recording_policy_are_preserved(self):
        day = parse_date("2026-09-07")
        for part in parts_for(time(7), time(17), time(17), time(23)):
            for privacy in ("public", "unlisted", "private"):
                with self.subTest(part=part.key, privacy=privacy):
                    body = broadcast_body(part, day, privacy)
                    self.assertEqual(body["snippet"]["title"], f"{part.title} 2026.09.07")
                    self.assertEqual(body["snippet"]["scheduledStartTime"], iso_at(day, part.start))
                    self.assertEqual(body["snippet"]["scheduledEndTime"], iso_at(day, part.end))
                    self.assertEqual(body["status"]["privacyStatus"], privacy)
                    self.assertFalse(body["status"]["selfDeclaredMadeForKids"])
                    details = body["contentDetails"]
                    self.assertTrue(details["enableAutoStart"])
                    self.assertFalse(details["enableAutoStop"])
                    self.assertTrue(details["enableDvr"])
                    self.assertTrue(details["recordFromStart"])
                    self.assertFalse(details["monitorStream"]["enableMonitorStream"])


if __name__ == "__main__":
    unittest.main()
