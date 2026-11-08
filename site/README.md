# ReviewReplay website

Static landing page for ReviewReplay. No build step: plain HTML, CSS and JavaScript.

```bash
python3 -m http.server 4173 -d site   # preview at http://localhost:4173
```

**Deploy:** `.github/workflows/pages.yml` publishes `site/` to
https://ggauravj05.github.io/reviewreplay/ on every push to `main` that touches it. Turn it on once
under Settings → Pages → Source: GitHub Actions (the workflow skips while the repository is private).

Built with tasteskill 2.5.1 (design-taste-frontend). The deal: a collage hero showing a real
review diff (pallets/click, real-003) on a grain-gradient sage frame; a dark green-black, bone and
mint palette; Instrument Sans with DM Mono; one liquid-type moment on the statement. The kit's
CSS and JS live in `assets/`, pruned to what the page loads. Every number on the page comes from
`results/` (m2-compare and m2-real-more: 12 real bugs, 72 real-bug reviews).

Checks (run from `site/`): `node ~/.claude/skills/design-taste-frontend/scripts/gate.mjs index.html`.
