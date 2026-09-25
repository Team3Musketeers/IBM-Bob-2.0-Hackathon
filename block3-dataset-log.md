# Block 3 — Dataset Curation Log

## Repo chosen
- **Name/URL:** freeCodeCamp/freeCodeCamp — https://github.com/freeCodeCamp/freeCodeCamp
- **License:** BSD-3-Clause for all code (verified in `LICENSE.md`). Note: `/curriculum` directory is separately copyrighted, NOT under BSD-3-Clause — we are scoping our dataset to code outside `/curriculum` to stay clean.
- **Chosen scope/component:** `client/src/` — freeCodeCamp's client application code (components/hooks/logic), under BSD-3-Clause, clear of the curriculum copyright carve-out
- **Why this repo:** Large, active open-source project with real, varied PR history — good mix of well-documented and thin PRs expected.
- **Note:** originally scoped to `client/`, but discovered most `client/`-path merges were `client/i18n/locales/...` translation-sync content, not real code changes. Narrowed to `client/src/` to get genuine application-logic PRs.
- **Date pulled:** September 26, 2026

---

## PR Tracking Table

Fill one row per PR. Aim for the spread described in Step 2: some thin descriptions, some scope-creepy ones, some genuinely good ones, a couple with linked tickets.

| # | PR link | Category (thin / scope-creep / good-control / has-ticket) | Description quality (1 line, your own read) | Linked ticket? | Diff saved? |
|---|---|---|---|---|---|
| 70153 | freeCodeCamp/freeCodeCamp#70153 | good-control (expected) | Narrow, title matches likely scope | none | [x] |
| 69851 | freeCodeCamp/freeCodeCamp#69851 | good-control (expected) | Very specific bug fix | none | [x] |
| 69784 | freeCodeCamp/freeCodeCamp#69784 | good-control + has-ticket | Narrow, likely honest | Closes #67697 | [x] |
| 69766 | freeCodeCamp/freeCodeCamp#69766 | thin (expected) | "update imports" — vague, worth checking diff breadth | none | [x] |
| 69899 | freeCodeCamp/freeCodeCamp#69899 | thin (expected) | Terse CSS fix title | none | [x] |
| 69571 | freeCodeCamp/freeCodeCamp#69571 | scope-creep + has-ticket | "proper component" refactor — check real diff size | Closes #68170 | [x] |
| 69487 | freeCodeCamp/freeCodeCamp#69487 | scope-creep (candidate) | Dependency swap, likely touches many files | none | [x] |
| 69455 | freeCodeCamp/freeCodeCamp#69455 | scope-creep (candidate) | Touches 3 named areas — test description-vs-diff match | none | [x] |
| 69775 | freeCodeCamp/freeCodeCamp#69775 | scope-creep (candidate) | "remove temp code" chore, cross-cutting (api/client) | none | [x] |
| 69271 | freeCodeCamp/freeCodeCamp#69271 | demo standout | React 19 upgrade — large feature PR, later reverted | none | [x] |
| 69474 | freeCodeCamp/freeCodeCamp#69474 | demo standout (pair) + has-ticket | Revert of #69271 — pairs for "promise vs. consequence" story | Closes #69473 | [x] |

**Sanity check before moving on:**
- [ ] At least 2 PRs are "thin description" — these should be your easiest wins tomorrow
- [ ] At least 2 PRs are "scope creep" — diff does more than description says
- [ ] At least 2 PRs are "good control" — Ghostwriter should correctly say these are fine (this matters for credibility — a tool that flags everything isn't trustworthy)
- [ ] At least 1–2 PRs have a linked ticket for Scope Auditor testing
- [ ] All diffs actually saved to `dataset/` folder, not just linked

---

## Repo skeleton checklist
- [ ] `git init` done
- [ ] `bob_sessions/` folder created
- [ ] `dataset/` folder created, diffs saved inside
- [ ] `LICENSE` file added (MIT)
- [ ] Repo pushed to a public remote (GitHub/GitLab) — check this now, not Sunday