# Launch plan

Goal: a credible public launch of ReviewReplay that people star, use and cite. Trending can't be
guaranteed; GitHub Trending reflects stars gained in a short window, so the plan concentrates
attention into the first 24–48 hours and makes the first visit convincing.

## Before launch (must-haves)

- [ ] **Results worth sharing**: comparison of at least 3 reviewers (Claude Code baseline, a review
      skill, `/code-review`, ideally Codex or Gemini) on ≥ 20 cases, including ≥ 10 real bugs.
- [ ] **Human-checked grader**: hand labels on a sample, κ ≥ 0.8 (`reviewreplay label`).
- [ ] **Maintainers first**: share the code-review-skill results on
      awesome-skills/code-review-skill#32 and give them time to respond.
- [ ] **Rename done**: repo `GgauravJ05/reviewreplay`, package and CLI `reviewreplay`.
- [ ] **Installs in one line** on a clean machine: `pip install reviewreplay` (publish to PyPI) and
      `reviewreplay init` works on a fresh clone of a popular repo.
- [ ] **30-second demo**: terminal recording (asciinema or GIF) of `init` → `run` → scorecard,
      at the top of the README.
- [ ] **Social preview image** (Settings → Social preview): name, one-line pitch, a scorecard.
- [ ] **One headline finding** in plain words, e.g. "AI reviewers found every known bug — the
      difference was how many of their other claims were wrong."

## Launch day (Tuesday–Thursday, morning US Eastern)

1. Make the repo public; create release `v0.1.0` with notes.
2. Post, in this order, linking the repo and the write-up:
   - Show HN: "Show HN: ReviewReplay – would your AI code reviewer have caught your past bugs?"
   - r/programming and r/MachineLearning (follow each subreddit's self-promotion rules).
   - X / LinkedIn thread with the scorecard image and the headline finding.
   - dev.to / Medium / Hashnode article: method, results, how to run it on your repo.
3. Reply to every comment in the first hours; turn good suggestions into issues.

## After launch

- Weekly: add cases, publish an updated scorecard, tag the people whose tools were tested.
- Good-first-issues: new reviewer adapters, new languages, GitHub Action.
- A public leaderboard page on the shared benchmark.

## Search and discovery (done / ongoing)

- Description and 20 topics set (ai-code-review, llm-evaluation, claude-code, codex, gemini-cli, …).
- README: question-led title, install-and-run in the first screen, keywords used naturally,
  diagram, results table, citation file.
- PyPI keywords and classifiers in `pyproject.toml`.
