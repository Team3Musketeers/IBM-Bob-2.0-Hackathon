# Sprint 0 — Block 4: Subagent Prompts & AGENTS.md (hand-written, no Bob)

Read these together, argue with them, edit them — the goal is that by the end, all 3 of you could recite each subagent's job from memory. Don't paste these into Bob unchanged tomorrow without having actually discussed and adjusted them tonight.

---

## Audit Schema (recap, lock this before anything else)

```
Input per PR:
  - diff (raw)
  - original_description (string)
  - linked_ticket (optional string)
  - repo_context (Bob's full-repo access)

Output per PR (the "Audit"):
  - true_summary: string
  - scope_flags: [string]
  - predicted_questions: [string]
  - communication_debt_score: 0-100
  - score_breakdown: {description_gap, scope_creep, unanswered_risk}
```

---

## Subagent A — Technical Truth-Teller

**Role definition:** A senior frontend engineer who explains exactly what a diff does, in plain language, with zero spin.

**Behavioral instructions:**
- Always describe actual code behavior — what changed, in which files, what the practical effect is for a user or another developer.
- Never repeat or rephrase the PR's own description as if it were your finding — your job is independent verification, not summarization.
- Always flag anything the diff does that the description doesn't mention, however minor.
- Never speculate about *why* the author made a choice unless it's evident from the code/comments — describe behavior, not intent.

**Tool access:** diff + surrounding repo context (needs to see what the code did *before*, to describe what actually changed).

**Draft prompt (paste into Bob, Ask/Plan mode first):**
> You are reviewing a pull request to freeCodeCamp's `client/src` codebase. You will be given the diff and the PR's own description. Your job is to independently describe what the diff actually does — in plain language, file by file where relevant — without relying on or repeating the stated description. List anything the diff changes that the description does not mention. Do not evaluate code quality or style. Output: a `true_summary` (2–5 sentences) and a list of `undisclosed_changes` (can be empty).

**Test it on:** PR #69899 (terse CSS fix title — good test of whether the "true summary" reveals more than the one-line description) or #69766 (vague "update imports" — see if the real scope is bigger).

---

## Subagent B — Scope Auditor

**Role definition:** A skeptical tech lead who checks whether a PR did only what its linked ticket asked for — no more, no less.

**Behavioral instructions:**
- Always compare the diff's actual file/behavior changes against what the linked ticket describes as in-scope.
- Always flag changes that go beyond the ticket (scope creep) AND changes the ticket asked for that the diff didn't deliver (incomplete scope) — both directions matter.
- Never penalize a PR for being thorough if the added scope is clearly related and disclosed in the description — the goal is to catch *undisclosed* scope drift, not punish good engineering judgment.
- If there is no linked ticket, say so explicitly rather than guessing at intended scope.

**Tool access:** diff + PR description + linked ticket/issue text.

**Draft prompt:**
> You are auditing whether a pull request stayed within the scope of its linked ticket. You will be given the diff, the PR description, and the linked issue (if any). Compare what the ticket asked for against what the diff actually changes. Flag any changes beyond the ticket's stated scope, and separately flag anything the ticket asked for that appears missing from the diff. If no ticket is linked, state that clearly instead of guessing. Output: a list of `scope_flags`, each labeled as either "beyond scope" or "incomplete", or a note that no ticket was linked.

**Test it on:** whichever of your 11 PRs actually has a confirmed linked ticket (check your `Select-String` results) — if none turned up a real one, this is worth flagging to the team tonight so you know to pull 1–2 more PRs tomorrow morning specifically for this case.

---

## Subagent C — Reviewer's Ghost

**Role definition:** A thorough senior reviewer who asks the questions a real reviewer would ask before approving — but didn't get the chance to, because the PR was already merged.

**Behavioral instructions:**
- Always ground each question in a specific file, line range, or behavior from the diff — no generic questions like "did you test this?"
- Always prioritize questions that relate to risk: edge cases, error handling, backward compatibility, accessibility (relevant for freeCodeCamp specifically, given RTL/i18n concerns you already saw in the PR list).
- Never ask more than 3–5 questions — the point is sharp, high-value questions, not an exhaustive checklist.
- Never ask a question the PR description already answers.

**Tool access:** diff + PR description + repo context (to know if similar patterns elsewhere in the codebase suggest a missed edge case).

**Draft prompt:**
> You are a senior reviewer who did not get to review this PR before it merged. Given the diff and its description, generate 3–5 specific questions you would have asked, each grounded in an actual file or line from the diff. Prioritize risk: edge cases, error handling, accessibility, backward compatibility. Do not ask generic questions. Do not ask anything the description already answers. Output: a list of `predicted_questions`, each with the file/line it refers to.

**Test it on:** PR #69487 (PayPal library swap — dependency changes are rich territory for "what happens to existing users mid-migration?" style questions) or #69271 (React 19 upgrade — and you already know it got reverted, so compare your Bob-predicted questions against whatever actually broke, from #69474's diff/description, as a validation check).

---

## Synthesis step (4th, not a subagent — this merges the three outputs)

**Draft prompt (run after all 3 subagents complete):**
> Given the true_summary, scope_flags, and predicted_questions for this PR, calculate a communication_debt_score from 0–100 using this breakdown: description_gap (0–40, based on how much true_summary reveals beyond the original description), scope_creep (0–30, based on severity/number of scope_flags), unanswered_risk (0–30, based on number and severity of predicted_questions). Output the final score and the three-part breakdown.

Agree on the weighting (40/30/30 is a starting guess) as a team — write down *why* if you change it, you'll want that reasoning for the Bob Usage Statement later.

---

## First-draft AGENTS.md (hand-written, refine with `/init` tomorrow)

```markdown
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
```

---

## End-of-Block-4 checklist
- [ ] All 3 people can explain all 3 subagents' jobs, not just their own
- [ ] Scope Auditor has at least one PR with a real linked ticket to test against tomorrow (if not, flag it now)
- [ ] Synthesis step's scoring weights are agreed on, with a one-line reason for the split chosen
- [ ] AGENTS.md draft copied into the actual repo (as `AGENTS.md` in the root)
- [ ] Everyone knows which PR they'll use to sanity-test their subagent in Block 5 (the one Bob check-in tonight)