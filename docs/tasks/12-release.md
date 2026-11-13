# 12 — Release and community (Roadmap Phase 5)

**Goal:** v0.2.0 released with notes, good first issues ready for contributors, and the launch posts
from docs/LAUNCH.md done once the multi-reviewer results exist.

**Why:** a release and well-scoped issues turn visitors into users and contributors.

**Depends on:** 07 and 08 for the launch-sized results; the rest can happen any time.

## Steps

1. **Social preview image** (1280×640): name, one-line pitch, a scorecard. Claude makes the PNG
   under `docs/media/`; **your part:** upload it in GitHub → Settings → General → Social preview.
2. **Good first issues** (5–8): add a case from a named repo, add a reviewer adapter (e.g. Aider,
   Cursor CLI), add a language, improve an error message, site accessibility. Each with context,
   files and "done when". Label `good first issue`. Claude drafts; you approve before posting.
3. **CHANGELOG.md** from `git log` since v0.1.0 (features, results, fixes); bump `version` in
   `pyproject.toml` and `CITATION.cff`.
4. **Tag and release** `v0.2.0` with notes summarising results and how to upgrade (your part: approve
   and publish the release).
5. **PyPI**: only on your explicit go-ahead. Then: build (`python -m build`), check with
   `twine check`, publish with a trusted-publisher GitHub workflow (no API token in the repo).
6. **Launch posts** per [../LAUNCH.md](../LAUNCH.md) once 08 is done: Show HN, Reddit, LinkedIn/X,
   a write-up. Claude drafts in `docs/drafts/`; you post.

## Done when

- [ ] Social preview set, issues posted, CHANGELOG, v0.2.0 release published.
- [ ] PyPI only if you decided to.

## Don't

- Don't publish, post or tag without your go-ahead.
- Don't overstate results in posts; quote numbers with intervals.
