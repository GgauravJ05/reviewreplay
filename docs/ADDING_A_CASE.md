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
- `occurrence` (optional, 1-based): which match to use when the anchor text repeats verbatim in the file.
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

## Real cases

A real case reviews a bug-introducing commit from a public repo, in the full project.

1. Find candidates: `python3 -m reviewbench mine https://github.com/<owner>/<repo> [--since 2025-06-01]`.
   Prefer rows marked `agree` (the fix message's reference and `git blame` point at the same commit)
   and ≤ 300 changed lines.
2. Read the fix commit, its issue and the introducing diff. Keep it only if the fix clearly repairs a
   behaviour bug introduced by that commit (not a feature, refactor or typing change).
3. Write `cases/real/<id>/case.json` with `kind: "real"`, `repo`, `commit` (introducing; for a merged
   PR, the merge commit), `fix`, and `issue` if any; `source` is `<repo url>@<commit>`; `license` is the
   repo's license (permissive only).
4. Write `truth.json` against the code at `commit` (anchors are resolved in the exported tree under
   `.cache/real/`). Use whole-function spans and list every copy of the bug in `also`. Put the fix's
   own evidence (message, tests) in `trigger`, and anything else the reviewer may fairly report in
   `related_valid`.
5. `python3 -m reviewbench check` exports the code and validates the case. We never run third-party
   code, so say in NOTES.md what the evidence is.
