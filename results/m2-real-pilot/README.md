# Real-bug pilot — findings

Question: do real bugs, reviewed inside the full repository, separate reviewers where small planted
cases could not? Run: 3 real cases × baseline × 3 runs = **9 reviews**, `claude-sonnet-5-5`,
2026-11-07. Usage ≈ $0.53 for reviews plus extraction and two grading passes.

## How real cases work

- A case names a repo, the **bug-introducing commit** and the **fix commit**; no code is stored here.
- `reviewreplay` exports the parent and the introducing commit with `git archive` (no history, so
  the later fix can't leak), and the reviewer sees the whole project (143–341 files) with the
  introducing change uncommitted.
- Candidates come from `reviewreplay mine <repo>`: fix commits whose message signals a regression,
  traced back by (a) the commit/PR the message names and (b) `git blame` of the lines the fix
  rewrites (SZZ). Both agreeing is the strongest signal.
- Reviewers stay read-only (Read/Grep/Glob, `git diff/log/show/status`); third-party code is never
  executed, by reviewers or by us. The bugs are therefore **not reproduced locally**; the evidence is
  the upstream fix, its message and its tests.

| Case | Repo | Introduced | Bug |
|---|---|---|---|
| real-001 | pallets/click #2934 (2025-05) | `__next__` raising `EOFError` on the test stdin | `click.File('-')` commands abort under `CliRunner` |
| real-002 | huggingface/datasets #8056 (2026-03) | path check `startswith(base)` copied to zip/rar/7z | sibling-prefix paths escape the extraction dir |
| real-003 | pallets/click #3126 (2026-04) | fish completion fields separated by `\n` | fish splits output on newlines; completion breaks |

## Result

| | Recall | Precision | Serious findings: hit / valid / unsure / false alarm |
|---|---|---|---|
| baseline | 89% (8/9) | 56% [39–72] | 9 / 3 / 9 / 1 |

- **Recall is effectively 100%.** The one miss (real-002 run 3) described the exact bug but cited
  approximate lines ("`~212, ~265, ~345`, badpath in the zip, rar and 7z extractors"; real lines 208,
  261, 337), outside the ±3-line location gate. A human would credit it. The graded number is kept;
  better handling of approximate citations is a grader to-do.
- **The difference from planted cases is precision, not recall.** Reviews raised 9 serious claims the
  judge couldn't settle (`unsure`), e.g. "py7zr may treat an empty `targets` list as no filter" and
  "`file_redir` is `None` for RAR3 symlinks". These depend on third-party library behaviour that
  isn't in the repo. Some may be real bugs. Settling them needs a check against the library
  source, and the benchmark doesn't do that today.

## What we learned

1. Even real, full-repo regressions from 2025–2026 were found by the baseline every time (one by
   hand-credit). With this model, **finding the planted/known bug is not the bottleneck**; the signal
   is in **precision and in the unverifiable claims**.
2. Real cases need more answer-key work than planted ones: the first grading scored 43% precision
   until a test the PR loosened to hide the bug (real-001) was added to `related_valid` and real-002's
   locations were widened to whole functions.
3. Mining yield is low: 15 repos gave 3 usable cases. Regression-worded fix messages are rare, and
   blame over blobless clones is slow (~10 min per repo for a wide search).
4. **Contamination is unknown.** Two cases are from 2026; if the model saw the fixes in training,
   recall would be inflated. Report real and planted results separately, as planned.

## Next options

- **Score unsure claims properly.** Give the judge the third-party source it needs (the pinned
  dependency's code) or hand-check `unsure` findings; otherwise precision on real cases is mostly
  noise.
- **Compare reviewers on precision and noise**, not recall: run code-review-skill (invoked) on these
  cases and the M1/M2 sets; its verify-before-reporting step (PR #34) targets exactly this.
- **More real cases**: mine more repos in the background (`reviewreplay mine`), prioritising agreeing
  candidates; aim for 10–20.
