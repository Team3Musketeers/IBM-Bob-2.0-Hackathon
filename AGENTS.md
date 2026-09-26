# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project purpose
Ghostwriter audits the gap between what a pull request's description claims
and what its diff actually does, using three independent subagents plus a
synthesis step that produces a Communication Debt Score.

## Structure
- `dataset/`       — curated real PRs from freeCodeCamp (client/src scope) as
                     diff + metadata JSON pairs (`pr_<N>.diff` + `pr_<N>_meta.json`)
- `bob_sessions/`  — required task session summary screenshots (hackathon deliverable)
- `block3-dataset-log.md` — PR curation log; tracks category tagging and sanity checks

## No build/test/lint system
There is no package.json, Makefile, or test runner. Nothing to install or build.
All "code" is markdown, JSON metadata, and `.diff` files.

## Dataset conventions
- Meta JSON files are UTF-16 LE encoded (BOM present) — do NOT assume UTF-8 when reading them programmatically.
- Each PR is categorized as one of: `thin`, `scope-creep`, `good-control`, `has-ticket`, or `demo standout`.
- Dataset scope is **freeCodeCamp `client/src/` only** — not `client/` (which is dominated by i18n translation syncs).
- The `dataset/` directory uses only `pr_<number>.diff` / `pr_<number>_meta.json` naming — no subdirectories.

## Subagent isolation rule (non-negotiable)
Each of the three analysis subagents must run with **no shared context** between them.
This is intentional: parallel isolation is the core architectural claim of the project.
Do not pass context or intermediate results between subagents before synthesis.

## Conventions
- Subagent prompts live in this repo as plain text/markdown before being
  configured as Bob custom modes — keep prompt source-of-truth in version
  control, not only inside Bob's UI config.
- The Communication Debt Score is the synthesis output — it is not produced
  by any single subagent, only by the aggregation step.

## Data scope note
- Dataset sourced from freeCodeCamp/freeCodeCamp, client/src/ only
  (BSD-3-Clause licensed code, outside the separately-copyrighted
  /curriculum directory). Source: github.com/freeCodeCamp/freeCodeCamp
