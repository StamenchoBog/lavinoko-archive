"""Find forecast slots that are missing from the archive, or that were archived late.

Reads archive file names (one per line, as `git ls-tree -r --name-only HEAD weather` prints them) on stdin
and prints one line per problem. Run daily by .github/workflows/check.yml, which turns new lines into
an issue in this repository. Tests: `python3 -m unittest discover .github/scripts` (also run by check.yml).

A slot is a scheduled forecast: 06:00 and 15:00 UTC from October to June, 06:00 UTC on the 1st of July, August
and September (keep in step with .github/workflows/fetch.yml here and workers/archive-trigger/wrangler.jsonc in LavinOko).
Any file from the slot's start until the next slot starts covers it: the backup runs fetch only if nothing is
archived yet, so a covered slot has exactly one file. A slot is judged only once the next slot has started,
because until then a late backup run can still fill it.

    missing  no file at all: that forecast is lost for verification
    late     the file is from a later hour than the slot: the Cloudflare Worker did not start the run, and
             GitHub's backup schedule did (the Worker starts runs on time since ON_TIME_SINCE)
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

SEASON_MONTHS = {10, 11, 12, 1, 2, 3, 4, 5, 6}
SEASON_HOURS = (6, 15)
SUMMER_HOUR = 6  # on the 1st of July, August and September
ON_TIME_SINCE = datetime(2026, 11, 19, tzinfo=UTC)  # the Worker's first on-time run

NAME = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2})Z\.json\.gz$")


def slots_between(start: datetime, end: datetime) -> list[datetime]:
    """Scheduled slot times t with start <= t < end."""
    out = []
    day = start.replace(hour=0, minute=0, second=0, microsecond=0)
    while day < end:
        if day.month in SEASON_MONTHS:
            hours = SEASON_HOURS
        else:
            hours = (SUMMER_HOUR,) if day.day == 1 else ()
        out += [t for h in hours if start <= (t := day.replace(hour=h)) < end]
        day += timedelta(days=1)
    return out


def next_slot(t: datetime) -> datetime:
    """The first slot after t (summer slots are a month apart)."""
    for days in (2, 40):
        later = slots_between(t + timedelta(hours=1), t + timedelta(days=days))
        if later:
            return later[0]
    raise AssertionError("no slot within 40 days")


def file_times(names: Iterable[str]) -> list[datetime]:
    """Issue hours (UTC) from archive file names; other names are ignored."""
    times = []
    for name in names:
        m = NAME.search(name.strip())
        if m:
            times.append(datetime.strptime(m.group(1), "%Y-%m-%dT%H").replace(tzinfo=UTC))
    return sorted(times)


def problems(names: Iterable[str], now: datetime, lookback: timedelta) -> list[str]:
    """One line per missing or late slot that started within `lookback` and whose time to be filled is over."""
    times = file_times(names)
    out = []
    for slot in slots_between(now - lookback, now):
        end = next_slot(slot)
        if end > now:
            continue  # a backup run can still fill it
        covering = [t for t in times if slot <= t < end]
        label = slot.strftime("%Y-%m-%d %H:%M UTC")
        if not covering:
            out.append(f"missing: {label}, no forecast archived before the next slot")
        elif covering[0] > slot and slot >= ON_TIME_SINCE:
            out.append(f"late: {label}, archived at {covering[0]:%H}:xx UTC (the Worker did not start it)")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hours", type=int, default=72, help="how far back to look (default 72; the check runs daily)")
    ap.add_argument("--now", help="UTC time to judge at, e.g. 2026-11-21T07:00 (default: now)")
    args = ap.parse_args()
    now = datetime.fromisoformat(args.now).replace(tzinfo=UTC) if args.now else datetime.now(UTC)
    for line in problems(sys.stdin, now, timedelta(hours=args.hours)):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
