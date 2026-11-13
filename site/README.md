# ReviewReplay website

Static landing page for ReviewReplay. No build step: plain HTML, CSS and JavaScript.

```bash
python3 -m http.server 4173 -d site   # preview at http://localhost:4173
```

**Deploy:** `.github/workflows/pages.yml` publishes `site/` to
https://ggauravj05.github.io/reviewreplay/ on every push to `main` that touches it. Turn it on once
under Settings → Pages → Source: GitHub Actions (the workflow skips while the repository is private).

Built with tasteskill 2.5.1 (design-taste-frontend), with the same section order as
tasteskill.dev and a look of its own: a centred hero over a real review diff (pallets/click,
real-003) on a grain-gradient frame; a live demo of the m2-real-more review list and report; four
"how it works" cards (mining, reviewers, replay lanes, grading) on painterly panels; a results
scorecard with a counter-rolls moment; FAQ; install tabs for Claude Code, Codex CLI and Gemini CLI.
Candy-on-black palette, Instrument Sans with DM Mono, arc mark. The kit's CSS and JS live in
`assets/`, pruned to the 61 files the page loads (1.1 MB).

Every number on the page comes from `results/m2-compare` and `results/m2-real-more` (12 real bugs,
36 reviews per reviewer, four judges plus code checks): precision 72% without vs 82% with
code-review-skill, +10 pts [+1, +16]. When those numbers change, update this page with the README.

Checks (run from `site/`, with `CHROME_PATH` set): `node ~/.claude/skills/design-taste-frontend/scripts/consistency.mjs index.html --page software`,
`assets/layout/check.mjs` and `scripts/perf.mjs` from the same skill. Waivers are in
`.taste-skill/waivers.json` (not committed).
