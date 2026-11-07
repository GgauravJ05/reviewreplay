from datetime import datetime, timedelta, timezone

from auth.store import SessionStore

T0 = datetime(2026, 11, 1, tzinfo=timezone.utc)


def test_session_valid_until_expiry():
    store = SessionStore(ttl=timedelta(hours=1))
    s = store.create(7, T0)
    assert store.get(s.token, T0 + timedelta(minutes=59)) == s
    assert store.get(s.token, T0 + timedelta(hours=1)) is None
