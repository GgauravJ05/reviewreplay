# 04 — Resolve or publish contested findings

**Goal:** every finding whose judges disagree is either settled with quoted evidence or listed in a
public "help label these" issue.

**Why:** the four-judge regrade left 12 of 195 real-bug findings contested, including one
real-012 (peft) finding the judge graded both ways. Hand-labelling by the author is not planned, so
contested items must be visible, not silently counted.

**Depends on:** 01 (multi-judge votes and `verify` on `main`).

## Context

- Grades with votes are in `results/m2-compare/grades/` and `results/m2-real-more/grades/` (after 01).
- `reviewreplay report` shows contested counts; `reviewreplay agreement` gives judge-vs-judge κ
  (Sonnet vs Opus κ was 0.74).
- `reviewreplay label` writes a blind yes/no sheet.

## Steps

1. List all contested findings: case, subject, run, finding text, each judge's vote, the truth spot.
2. For each, read the code at the case's commit (exported under `~/.cache/reviewreplay/real/`)
   and the upstream fix. If the evidence settles it, write the verdict with a quote.
3. Write the remaining ones into a GitHub issue "Help label these N findings", each with evidence,
   the two possible verdicts and a link to the case. Use the `good first issue` label.
4. Add a short note to the results README: how many were contested, how many settled, the issue link.

## Done when

- [ ] A table of contested findings with verdict or "open" committed under `results/`.
- [ ] Issue opened for open ones (after the author approves the text).
- [ ] Headline numbers both with and without contested findings are stated.

## Your part

- Approve the issue text before it is posted, and post it (or let Claude post it after your go-ahead).

## Don't

- Don't overwrite judge votes with your own verdicts; store settled verdicts in a separate file.
