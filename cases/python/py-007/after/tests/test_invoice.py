from billing.invoice import billable_hours, invoice_lines, invoice_total_cents
from billing.sessions import sessions_from_events

EVENTS = [
    {"account_id": "a-100", "gpu": "g1", "type": "start", "at": "2026-07-14T13:00:00+00:00"},
    {"account_id": "a-100", "gpu": "g1", "type": "stop", "at": "2026-07-14T14:30:00+00:00"},
    {"account_id": "a-100", "gpu": "g2", "type": "start", "at": "2026-07-15T09:00:00+00:00"},
    {"account_id": "a-100", "gpu": "g2", "type": "stop", "at": "2026-07-15T09:20:00+00:00"},
]


def test_sessions_pair_start_and_stop():
    sessions = sessions_from_events(EVENTS)
    assert [s.gpu for s in sessions] == ["g1", "g2"]
    assert sessions[0].start.hour == 9  # 13:00 UTC is 09:00 in New York in July


def test_invoice_lines_show_local_time():
    line = invoice_lines(sessions_from_events(EVENTS))[0]
    assert "2026-07-14 09:00 EDT" in line.description


def test_billed_per_started_hour():
    g1, g2 = sessions_from_events(EVENTS)
    assert billable_hours(g1) == 2   # 90 minutes
    assert billable_hours(g2) == 1   # 20 minutes


def test_invoice_total():
    # two sessions: 2 x 250 fee + (2 + 1) hours x 180
    assert invoice_total_cents(sessions_from_events(EVENTS)) == 500 + 540
