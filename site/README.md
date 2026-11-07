# ReviewReplay website

Static landing page for ReviewReplay. No build step: plain HTML, CSS and JavaScript.

```bash
python3 -m http.server 4173 -d site   # preview at http://localhost:4173
```

**Deploy:** GitHub Pages (Settings → Pages → deploy from branch `main`, folder `/site` via a
Pages workflow, or copy to `docs/`). The canonical and `og:image` URLs assume
`https://ggauravj05.github.io/reviewreplay/`; update them if you use a custom domain.
Pages on a private repository needs a paid plan, so publish after the repository goes public.

Built with tasteskill 2.5.1 (design-taste-frontend). The deal: a collage hero showing a real
review diff (pallets/click, real-003) on a grain-gradient sage frame; a dark green-black, bone and
mint palette; Instrument Sans with DM Mono; one liquid-type moment on the statement. The kit's
CSS and JS live in `assets/`, pruned to what the page loads. Every number on the page comes from
`results/` (m2-compare: 19 cases, 114 reviews, 24 of them on real bugs).

Checks (run from `site/`): `node ~/.claude/skills/design-taste-frontend/scripts/gate.mjs index.html`.
