"""Tests for check_archive.py. Standard library only: python3 -m unittest discover .github/scripts"""

import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_archive import next_slot, problems, slots_between  # noqa: E402


def utc(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


def name(s: str) -> str:
    return f"weather/{s[:4]}/{s[5:7]}/{s}Z.json.gz"


class Slots(unittest.TestCase):
    def test_season_has_two_slots_a_day_and_summer_one_a_month(self):
        self.assertEqual(
            slots_between(utc("2026-11-20T00:00"), utc("2026-11-21T00:00")),
            [utc("2026-11-20T06:00"), utc("2026-11-20T15:00")],
        )
        self.assertEqual(
            slots_between(utc("2027-06-30T00:00"), utc("2027-10-02T00:00")),
            [
                utc("2027-06-30T06:00"),
                utc("2027-06-30T15:00"),
                utc("2027-07-01T06:00"),
                utc("2027-08-01T06:00"),
                utc("2027-09-01T06:00"),
                utc("2027-10-01T06:00"),
                utc("2027-10-01T15:00"),
            ],
        )
        self.assertEqual(next_slot(utc("2027-07-01T06:00")), utc("2027-08-01T06:00"))


class Problems(unittest.TestCase):
    def test_on_time_files_are_fine(self):
        files = [name("2026-11-20T06"), name("2026-11-20T15"), name("2026-11-21T06")]
        self.assertEqual(problems(files, utc("2026-11-21T07:30"), timedelta(hours=30)), [])

    def test_missing_and_late_slots_are_reported(self):
        files = [name("2026-11-20T08"), name("2026-11-21T06")]  # 06 late, 15 missing
        self.assertEqual(
            problems(files, utc("2026-11-21T07:30"), timedelta(hours=30)),
            [
                "late: 2026-11-20 06:00 UTC, archived at 08:xx UTC (the Worker did not start it)",
                "missing: 2026-11-20 15:00 UTC, no forecast archived before the next slot",
            ],
        )

    def test_a_slot_is_not_judged_while_a_backup_can_still_fill_it(self):
        self.assertEqual(problems([], utc("2026-11-21T10:00"), timedelta(hours=8)), [])  # open until 15:00

    def test_late_runs_before_the_worker_are_not_reported(self):
        files = [name("2026-11-18T07"), name("2026-11-18T16"), name("2026-11-19T06")]
        self.assertEqual(problems(files, utc("2026-11-19T10:00"), timedelta(hours=40)), [])

    def test_other_file_names_are_ignored(self):
        files = ["README.md", name("2026-11-20T06"), "weather/2026/11/notes.txt", name("2026-11-20T15")]
        self.assertEqual(problems(files, utc("2026-11-21T07:00"), timedelta(hours=26)), [])


if __name__ == "__main__":
    unittest.main()
