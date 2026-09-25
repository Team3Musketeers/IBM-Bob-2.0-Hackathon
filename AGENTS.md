# AGENTS.md — Ghostwriter

## Project purpose
Ghostwriter audits the gap between what a pull request's description claims
and what its diff actually does, using three independent subagents plus a
synthesis step that produces a Communication Debt Score.

## Structure
- dataset/        curated real PRs from freeCodeCamp (client/src scope) as
                   diff + metadata JSON pairs, used as test/demo input
- bob_sessions/    required task session summary screenshots (hackathon deliverable)
- (to be added Sprint 1): src/ or similar, holding orchestration code and
  the dashboard

## Conventions
- Subagent prompts live in this repo as plain text/markdown before being
  configured as Bob custom modes — keep prompt source-of-truth in version
  control, not only inside Bob's UI config.
- Each subagent must run in isolation (no shared context between them) —
  this isolation is a deliberate design choice, not an accident, since it's
  what makes "parallel subagents" a real, demoable claim rather than one
  sequential chain pretending to be parallel.

## Data scope note
- Dataset sourced from freeCodeCamp/freeCodeCamp, client/src/ only
  (BSD-3-Clause licensed code, outside the separately-copyrighted
  /curriculum directory). Source: github.com/freeCodeCamp/freeCodeCamp