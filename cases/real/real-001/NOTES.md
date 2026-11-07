Real bug from pallets/click (BSD-3-Clause). Introduced by PR #2934 (merge 262bdf0), fixed in
93c6966 ("Fix regression related to EOF introduced in 262bdf0", issue #2939). The miner found it
by both signals (fix message reference and blame of the deleted lines). Evidence: the upstream fix
commit message and issue; not reproduced locally (running cloned third-party code is not allowed
in this environment). The code is exported from git at review time, not stored here.
