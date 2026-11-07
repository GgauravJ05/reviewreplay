# M1 pilot — findings

Run: 10 cases (5 Python, 5 ML) × 3 subjects × 3 runs = **90 reviews**, model `claude-sonnet-5-5`,
Claude Code 2.1.309, subscription login, flag-only isolation (see `spikes/m0/RESULTS.md`).
Dates: started 2026-11-06, interrupted by the subscription session limit after 13 reviews,
resumed and finished 2026-11-07.

Files: `summary.md` (current grades), `summary-v1.md` (first grading, kept for the record),
`labels.csv` (hand-label sheet), `raw/` `findings/` `grades/` (every review, extraction, grade).

Estimated API-equivalent usage: reviews $4.31, extraction $1.54, judging $1.31 (first grading) + a re-grade.

## Headline

| | Recall | Clean pass | Decoy trap | Skill used by itself | Median est. cost |
|---|---|---|---|---|---|
| baseline | 100% | 100% | 0% | — | $0.038 |
| code-review-skill, natural | 100% | 100% | 0% | **0 / 30 runs** | $0.040 |
| code-review-skill, invoked | 100% | 100% | 0% | (forced) | $0.059 (+55%) |

## What we learned

1. **The cases are too easy: every reviewer scores at the ceiling.** Even cross-file bugs (units defined
   in another file, a 1-based helper, a docstring invariant, a schema note) were found in all 90 reviews,
   and no decoy was flagged as a serious problem. With no spread, these cases can't show whether a skill
   helps. M2 needs much harder cases (see below).
2. **code-review-skill never triggered by itself: 0 of 30 natural runs.** Installed and visible, but with a
   plain "review the uncommitted changes" prompt Claude reviewed without loading it. In practice a user
   who installs it and asks for a review gets the baseline. Relevant to awesome-skills/code-review-skill#32
   (impact) and #35 (trigger description).
3. **Invoked explicitly, it costs ~55% more per review** (median $0.059 vs $0.038, from loading its
   instructions) with **no measurable gain on these cases**. Because of finding 1, this does not show
   the skill doesn't help; it shows these cases can't tell.
4. **The grader needed a fix, and the pilot caught it.** The first grading (`summary-v1.md`) gave the skill
   −8 pts precision [−13, −3]. Reading the "false alarms" showed most were real problems the answer
   key didn't list (inner join dropping orders, zero-variance scaling, limit above the page cap) or fair
   "the tests miss this bug" remarks. Fixes: answer keys now carry `related_valid` (shown to the judge),
   and the judge rubric counts test-gap remarks about a real bug as valid. After re-grading, all
   precision is 100%. Lesson: a single grading pass would have published a false "skill hurts
   precision" result.
5. **Low-severity noise is invisible in the headline metrics.** Reviewers raised 54 minor/note concerns
   on the clean and decoy cases (baseline 20, natural 19, invoked 24). They don't count as false alarms
   (only blocking/important do), but they cost the author time. M2 should report "nitpicks per clean
   review" as its own metric.
6. **Operations:** a long run can exhaust the subscription session limit. The runner now stops on
   usage-limit or login errors and resumes cleanly; test runs can use a `claude setup-token` login so the
   desktop app's login refreshes don't log the CLI out.

## Grader check (second rater)

Claude (Opus 5.5) labelled all 189 findings blind, with the same view the `label` command shows
(answer key, finding, code, no judge label, no subject): `labels-claude.csv`.

| | |
|---|---|
| Agreement | 95.2% (180 / 189) |
| Cohen's κ | **0.93** (bar: 0.8) |
| Disagreements | 9, all minor/note severity; 7 are judge `unsure` → rater `false_alarm` |

No disagreement involves a `hit` or a serious finding, so no headline number in this pilot would
change. The pattern: the judge says `unsure` for speculative remarks ("if order_id can be null…")
where the rater says `false_alarm`. Both labels count against clean pass the same way, so this
matters only for low-severity noise counts.

**Caveat — this is not a human check.** The second rater is the same model family as the judge, so
shared blind spots wouldn't show up as disagreement. It also saw the answer-key changes made
during this pilot. Treat κ = 0.93 as a consistency check. A human pass with
`python3 -m reviewbench label results/m1-pilot/labels.csv` (`labels.csv` is still unlabelled) is
still needed before any public claim.

## Changes for M2

- **Harder cases.** Larger `base/` (several hundred lines, more files) so the relevant context isn't
  obvious; bugs that need two hops of reasoning; plausible-but-wrong fixes; concurrency and ordering
  bugs; subtler decoys (code that violates a common rule of thumb for a documented reason).
  Pilot new cases against the baseline first: keep only cases it misses at least sometimes.
- **Real bugs (pulled forward from M3)** are the most likely source of difficulty.
- **New metric:** minor/note findings per clean or decoy review.
- **Keep both skill conditions** (natural and invoked); the natural-trigger rate is itself a result.
