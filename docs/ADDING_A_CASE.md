# Adding a case

A case is a small project, one code change, and an answer key. Reviewers see the project
with the change applied as uncommitted edits; the answer key never leaves this repo.

## 1. Layout

```
cases/<track>/<id>/
  case.json      metadata
  base/          the project before the change
  after/         the project after the change
  change.patch   generated: base/ → after/
  truth.json     the answer key
  NOTES.md       why it's a bug (or why it isn't), related issues, source credit
```

`case.json`
```json
{
  "id": "py-006",
  "kind": "planted",
  "track": "python",
  "title": "Add retry to the payment client",
  "source": "original",
  "license": "MIT",
  "added": "2026-11-10"
}
```
`kind` is one of `planted` (we wrote the bug), `real` (from a public repo; set `source` to
`<repo url>@<commit>` and credit it in NOTES.md), `clean` (no bug), `decoy` (no bug, but code
that looks wrong).

## 2. The answer key

Locations use an **anchor** (a substring that appears on exactly one line of the file in `after/`)
plus a **span** (how many lines from there). Line numbers are computed, so editing a case never
silently breaks its key.

```json
{
  "bugs": [
    {
      "id": "b1",
      "file": "shop/checkout.py",
      "anchor": "if cart.subtotal_cents() >= FREE_SHIPPING_THRESHOLD:",
      "span": 2,
      "also": [{"file": "shop/config.py", "anchor": "FREE_SHIPPING_THRESHOLD = 50", "span": 1}],
      "class": "unit-mismatch",
      "severity": "blocking",
      "summary": "What is wrong and why, in one or two sentences.",
      "trigger": "A concrete input and the wrong result it produces."
    }
  ],
  "known_ok": [
    { "id": "ok1", "file": "...", "anchor": "...", "span": 1,
      "note": "Why this suspicious-looking code is correct." }
  ],
  "related_valid": ["Another real problem in this change that a reviewer may fairly report."]
}
```

- `also`: other places a reviewer may legitimately point to (the other side of a cross-file bug).
- `planted`/`real` cases need ≥1 bug; `clean`/`decoy` need none; `decoy` needs ≥1 `known_ok` with a note.
- `related_valid`: a list of other real problems in the change (one sentence each). The judge sees them
  and credits a finding that reports one as `valid_other`. Without this, a reviewer that spots a real
  secondary issue is scored as a false alarm (this happened in the M1 pilot).

## 3. What makes a good case

- **Not a textbook one-liner.** M1 showed that single-function bugs, and even simple cross-file ones,
  are caught every time. Aim for bugs that need the surrounding code: units or conventions defined in another file,
  an invariant stated in a docstring, a sibling method that does it right.
- **One planted bug per case.** If you find a second one, fix it or record it in NOTES.md.
- **Realistic change.** A feature or refactor a person would actually submit, ideally with a test that
  passes despite the bug.
- **Small.** ≤ 300 changed lines, `base/` ≤ 2,000 lines.

## 4. Check it

```bash
python3 -m reviewbench make-patch cases/<track>/<id>
python3 -m reviewbench check
```

Then **execute the case code** to prove the key: the bug's `trigger` must actually produce the wrong
result, and clean/decoy code must actually be correct. (In M1 this caught a wrong trigger in py-005.)
Running code leaves caches (`__pycache__`, `.pytest_cache`); the tools ignore them.
