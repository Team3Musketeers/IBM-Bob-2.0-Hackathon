# Audit Dashboard

Renders synthesis output as a browsable Communication Debt dashboard.

This directory is **self-contained and additive**. It adds no changes to
any existing file in the repository, which is deliberate: see
[Why this is one directory](#why-this-is-one-directory).

```
dashboard/
  render_dashboard.py       validates synthesis output, reshapes it for display
  static/index.html         the dashboard (Tailwind via CDN, no build step)
  static/dashboard_data.json  GENERATED - do not hand-edit
  Dockerfile                nginx:alpine, serves static/
  docker-compose.yml
```

## What this does and does not do

**It does not score anything.** The Communication Debt Score, the
40/30/30 weighting, and the severity judgement that `scope_creep`
requires all belong to the synthesis step specified in
[`prompts/synthesis.md`](../prompts/synthesis.md). This directory only:

1. **validates** a synthesis run is internally consistent, and
2. **renders** it.

That split is the point. A second scoring implementation would drift
from the team's and quietly produce numbers nobody approved.

## Usage

```bash
python dashboard/render_dashboard.py
cd dashboard && docker compose up     # http://localhost:8080
```

Standard library only, Python 3.10+. No dependencies, no build step for
the HTML.

`--check` validates without writing, and fails if the committed
`dashboard_data.json` is stale. Intended for CI:

```bash
python dashboard/render_dashboard.py --check
```

## What it validates

A synthesis run is rejected, not rendered, when:

- `score_breakdown` does not sum exactly to `communication_debt_score`
  (e.g. `28 + 22 + 26 = 76` ✓, anything else ✗)
- the score is not an integer in `0–100`
- a subagent key is missing (`true_summary`, `undisclosed_changes`,
  `scope_flags`, `predicted_questions`)
- `agent_consensus` is not one of `aligned` / `partial` / `diverged`
- a PR has no matching `pr_<N>_meta.json`, or the metadata's `number`
  disagrees with the filename
- `scope_flags` or `predicted_questions` contain an unrecognised shape

## Input shapes

Both the current batch file and per-PR v2 files are accepted, so a
partial re-run does not require rewriting the whole dataset.

| Source | Shape | Notes |
|---|---|---|
| `dataset/audit_results.json` | array of records with `pr_number` | `predicted_questions` as bare strings; no consensus fields |
| `dataset/audit_<N>_v2.json` | single record, no `pr_number` | number inferred from filename; questions as `{question, file, line}`; carries `agent_consensus` |

Where both cover a PR, the richer schema wins. PR metadata is read as
**UTF-16 LE** per the repo convention, and the freeCodeCamp contribution
checklist is stripped from the PR body so the dashboard shows the
author's actual claim rather than ten lines of boilerplate.

## Open item this surfaced

Two synthesis runs of the same PR currently disagree, and the renderer
refuses to publish until that is resolved:

```
PR #69487: audit_69487_v2.json scores 76 but audit_results.json scores 52
```

A 24-point swing on the same diff. The most likely cause is that
`synthesis.md` asks `scope_creep` to scale with *severity* while the
batch run appears to have counted flags without weighting them — #69487
gained 7 scope flags and richer `undisclosed_changes` in the v2 run, so
`28/40` on `description_gap` and `22/30` on `scope_creep` are plausible
under the new rule where `16` and `8` were not.

**This needs a team decision, not a code fix.** Either the v1 batch
scores should be regenerated under the current `synthesis.md`, or the
two should be kept as deliberately labelled different runs. The renderer
surfaces the conflict in a banner and publishes the richer run only when
given `--allow-score-conflicts`; it never silently picks one.

`audit_69455.json` is also superseded by `audit_results.json` with
identical scores — harmless duplicate, safe to delete.

## Why this is one directory

Everything lives under `dashboard/` so that this branch **adds one new
top-level path and modifies zero existing files**. A teammate's work and
this work then cannot produce a merge conflict, because there is no
shared path to disagree about. It also keeps the contribution reviewable
in one glance.

If the team later prefers a different location, moving the directory is a
self-contained rename.

## Related

- `prompts/synthesis.md` — authoritative synthesis specification
- `.bob/custom_modes.yaml` — the four subagent mode definitions
- `AGENTS.md` — subagent isolation rule
