import unittest

from live_metrics_server import select_display_item


class SelectDisplayItemTests(unittest.TestCase):
    def test_selects_active_part(self):
        manifest = {
            "broadcasts": {
                "part1": {"id": "one"},
                "part2": {"id": "two"},
                "part3": {"id": "three"},
            }
        }
        items = [
            {
                "id": "one",
                "statistics": {"viewCount": "12"},
                "liveStreamingDetails": {
                    "actualStartTime": "2026-08-01T00:00:00Z",
                    "actualEndTime": "2026-08-01T03:00:00Z",
                },
            },
            {
                "id": "two",
                "statistics": {"viewCount": "7"},
                "liveStreamingDetails": {
                    "actualStartTime": "2026-08-01T03:00:00Z",
                    "concurrentViewers": "3",
                },
            },
        ]

        result = select_display_item(manifest, items)

        self.assertEqual(result["status"], "live")
        self.assertEqual(result["part"], "part2")
        self.assertEqual(result["concurrentViewers"], "3")
        self.assertEqual(result["viewCount"], "7")

    def test_selects_first_upcoming_part(self):
        manifest = {
            "broadcasts": {
                "part1": {"id": "one"},
                "part2": {"id": "two"},
            }
        }
        items = [
            {
                "id": "one",
                "liveStreamingDetails": {
                    "actualStartTime": "2026-08-01T00:00:00Z",
                    "actualEndTime": "2026-08-01T03:00:00Z",
                },
            },
            {"id": "two", "liveStreamingDetails": {}},
        ]

        result = select_display_item(manifest, items)

        self.assertEqual(result["status"], "waiting")
        self.assertEqual(result["part"], "part2")


if __name__ == "__main__":
    unittest.main()
