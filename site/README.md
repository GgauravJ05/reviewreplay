# ReviewReplay website

Static landing page for ReviewReplay. No build step: plain HTML, CSS and JavaScript.

```bash
python3 -m http.server 4173 -d site   # preview at http://localhost:4173
```

**Deploy:** `.github/workflows/pages.yml` publishes `site/` to
https://ggauravj05.github.io/reviewreplay/ on every push to `main` that touches it. Turn it on once
under Settings → Pages → Source: GitHub Actions (the workflow skips while the repository is private).

Light theme only, in the layout style of archify.si: pill nav, a hero with a serif-italic accent,
a "live" frame with four real interactive diagrams (`artifacts/`, made with Archify from the specs
in `docs/media/*.archify.json`), a stats row, then numbered sections: how it works, results, the
20 real bugs, grading, what you get, reviewers, quick start, FAQ. One stylesheet
(`assets/site.css`) and one script (`assets/site.js`); fonts are Geist, Instrument Serif and
JetBrains Mono from Google Fonts. The demo video and poster are in `media/`.

Every number on the page comes from a committed run: `results/m2-compare` and
`results/m2-real-more` (12 Python bugs) and `results/m3-js-go` (8 JavaScript and Go bugs). When
those numbers change, update this page with the README.

To rebuild a diagram: `node <archify>/bin/archify.mjs finalize workflow docs/media/pipeline.archify.json site/artifacts/pipeline.html --quality showcase`
(the diff-vs-damage diagram is type `architecture`).
