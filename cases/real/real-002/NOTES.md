Real bug from huggingface/datasets (Apache-2.0). PR #8056 (1bd0a5c, 2026-03-09) added safe-member
filtering to the zip, rar and 7z extractors by copying the tar extractor's `startswith(base)` check,
which lets sibling-prefix paths escape. Fixed in e693835 (#8490, 2026-08-31). Evidence: upstream fix
message and regression test; not executed locally. The tar copy (occurrence 1) predates this
change but is accepted as a location.
