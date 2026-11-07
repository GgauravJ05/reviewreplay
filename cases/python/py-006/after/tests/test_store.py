from pricing import db
from pricing.models import Rule
from pricing.store import load_rules, save_rules


def test_rules_are_cached_per_tenant():
    load_rules.cache_clear()
    before = db.QUERIES
    first = load_rules("globex")
    second = load_rules("globex")
    assert first == second
    assert db.QUERIES == before + 1


def test_save_invalidates_cache():
    load_rules.cache_clear()
    load_rules("globex")
    save_rules("globex", [Rule(name="globex-partner", kind="percent_off", value=15)])
    assert load_rules("globex")[0].value == 15
    save_rules("globex", [Rule(name="globex-partner", kind="percent_off", value=12)])
