DST wall-clock subtraction. `sessions.py` (unchanged) stores start/end as local times via
`astimezone(ZoneInfo)`; both share the same cached `ZoneInfo`, so `end - start` is computed on wall
clock time (Python's documented rule for same-tzinfo aware datetimes). Before this change the
duration was never used (flat fee per session). Verified by execution: a 3-hour session across the
2026-11-01 fall-back bills 2 hours; a 50-minute session across 2026-03-08 bills 2. Tests use July
sessions only. Fix: `(end.astimezone(timezone.utc) - start.astimezone(timezone.utc))`, or keep UTC
in Session and convert only for display.
