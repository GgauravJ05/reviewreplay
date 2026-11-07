from datetime import datetime, timedelta, timezone

from auth.store import SessionStore

T0 = datetime(2026, 11, 1, tzinfo=timezone.utc)


def test_session_valid_until_expiry():
    store = SessionStore(ttl=timedelta(hours=1))
    s = store.create(7, T0)
    assert store.get(s.token, T0 + timedelta(minutes=59)) == s
    assert store.get(s.token, T0 + timedelta(hours=1)) is None


def test_revoke_is_idempotent():
    store = SessionStore()
    s = store.create(7, T0)
    store.revoke(s.token)
    store.revoke(s.token)
    assert store.get(s.token, T0) is None and len(store) == 0


def test_purge_removes_only_expired():
    store = SessionStore(ttl=timedelta(hours=1))
    old = [store.create(1, T0) for _ in range(3)]
    fresh = store.create(2, T0 + timedelta(minutes=30))
    assert store.purge_expired(T0 + timedelta(hours=1)) == 3
    assert len(store) == 1 and store.get(fresh.token, T0 + timedelta(hours=1)) == fresh
    assert all(store.get(s.token, T0) is None for s in old)
