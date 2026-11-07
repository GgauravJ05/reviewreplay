# ReviewReplay website

Static landing page for ReviewReplay. No build step: plain HTML, CSS and JavaScript.

```bash
python3 -m http.server 4173 -d site   # preview at http://localhost:4173
```

**Deploy:** GitHub Pages (Settings → Pages → deploy from branch `main`, folder `/site` via a
Pages workflow, or copy to `docs/`). The canonical and `og:image` URLs assume
`https://ggauravj05.github.io/reviewreplay/`; update them if you use a custom domain.
Pages on a private repository needs a paid plan, so publish after the repository goes public.

Design follows the landing-page-design skill: Geist only, Tailwind type and spacing scale,
flat backgrounds, Phosphor icons, motion on `cubic-bezier(0.22, 1, 0.36, 1)` with
reduced-motion support. Every number on the page comes from `results/`.
