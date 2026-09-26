# Project Architecture Rules (Non-Obvious Only)

- **Parallel subagent isolation is a hard constraint, not a preference** — the three subagents (Description Auditor, Scope Auditor, Tone Auditor) must be runnable in parallel with no inter-subagent dependencies. Any design that requires one subagent's output as input to another before synthesis violates this.
- **Synthesis is a fourth, separate step** — the Communication Debt Score aggregates the three subagents' outputs. Plan for an explicit synthesis agent or function; do not collapse it into one of the three.
- **Dataset is fixed input, not dynamic** — 11 curated PRs in `dataset/`, each a `.diff` + `_meta.json` pair. No API calls to GitHub are needed for demo; everything is local.
- **Meta JSON encoding quirk**: files are UTF-16 LE (exported from a Windows tool). Any pipeline that reads them must handle this encoding explicitly.
- **No dashboard/UI exists yet** — Sprint 1 scope includes building `src/` and a dashboard. Current repo state is data-only. Plans should not assume existing infrastructure.
- **PR pair `#69271` / `#69474`** is intentionally included as a "promise vs. consequence" demo pair (React 19 upgrade + its revert). Design demos or presentations around this narrative.
