import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tunisian_day_status import tunisian_day_status


class TunisianDayStatusTests(unittest.TestCase):
    def test_friday_is_detected_after_utc_midnight_boundary(self):
        # 23:30 UTC Thursday is already 00:30 Friday in Tunisia.
        status = tunisian_day_status(datetime(2026, 11, 5, 23, 30, tzinfo=timezone.utc))
        self.assertEqual(status, {
            "is_friday": "true",
            "local_date": "2026-11-06",
            "local_time": "00:30:00",
        })

    def test_friday_is_detected_during_friday_daytime(self):
        status = tunisian_day_status(datetime(2026, 11, 6, 11, 10, tzinfo=timezone.utc))
        self.assertEqual(status["is_friday"], "true")
        self.assertEqual(status["local_date"], "2026-11-06")
        self.assertEqual(status["local_time"], "12:10:00")

    def test_monday_is_not_friday(self):
        status = tunisian_day_status(datetime(2026, 11, 2, 11, 10, tzinfo=timezone.utc))
        self.assertEqual(status["is_friday"], "false")
        self.assertEqual(status["local_date"], "2026-11-02")
        self.assertEqual(status["local_time"], "12:10:00")

    def test_rejects_naive_datetime(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            tunisian_day_status(datetime(2026, 11, 6, 12, 10))


if __name__ == "__main__":
    unittest.main()
