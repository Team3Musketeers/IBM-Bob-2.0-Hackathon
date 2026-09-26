# Project Documentation Context (Non-Obvious Only)

- **`block3-dataset-log.md`** is the canonical PR curation log — it contains the category tagging rationale and sanity-check checklist. Check it before adding or discussing dataset PRs.
- **`bob_sessions/`** is currently empty — it is a required deliverable folder (hackathon screenshots), not a code or config directory.
- **Dataset scope narrowing**: the original plan was `client/` from freeCodeCamp; it was narrowed to `client/src/` because `client/` is dominated by `i18n/locales/` translation-sync commits that have no useful description-vs-diff signal.
- **PR categories** used in this project: `thin`, `scope-creep`, `good-control`, `has-ticket`, `demo standout` — these are the project's own taxonomy, not GitHub's labels.
- **No src/ yet** — orchestration code and dashboard are planned for Sprint 1 but do not exist in the repo. Do not assume any source files exist beyond the dataset.
