Decoy: three patterns that are often flagged but are correct here (backwards index deletion,
inclusive expiry, swallowed KeyError on idempotent logout). Correctness checked by execution:
unit tests plus 2,000 randomized stores comparing purge_expired against a filter by is_valid.
