# Synthesis Step

This is not a subagent — it's the 4th, final step that combines the three
independent subagent outputs (Technical Truth-Teller, Scope Auditor,
Reviewer's Ghost) into one final audit result. It runs only after all
three subagents have completed, and it is the only place their outputs
are allowed to meet.

## Inputs

The three subagent JSON outputs for a single PR:
- Technical Truth-Teller: `{ true_summary, undisclosed_changes, risk_level }`
- Scope Auditor: `{ scope_flags, ticket_linked, risk_level }`
- Reviewer's Ghost: `{ predicted_questions, risk_level }`

Plus the PR's original description, for scoring the description_gap dimension.

## Part 1 — Communication Debt Score

Compute a `communication_debt_score` from 0-100, broken into three weighted
dimensions:

- **description_gap (0-40)**: scale with how much `true_summary` reveals
  beyond the original PR description. A description that covers everything
  Technical Truth-Teller found scores near 0; a description that omits
  significant behavior scores near 40.
- **scope_creep (0-30)**: scale with the *severity* of anything in
  `scope_flags`, not just their presence. Behavioral changes, new
  dependencies, or cross-cutting edits score high (near 30). Benign,
  disclosed-in-spirit additions like test coverage or comments score low
  (near 0-5) even if technically undisclosed. Scope Auditor itself does
  not judge severity - severity judgment belongs here, in synthesis, so
  that Scope Auditor can remain a pure, honest reporter of what it finds.
- **unanswered_risk (0-30)**: scale with the number and severity of
  `predicted_questions`. A single minor stylistic question scores low; a
  question touching a genuine production/security/data-integrity risk
  scores high, and multiple such questions compound toward the ceiling.

## Part 2 — Agent Disagreement Detection

Compare the three `risk_level` values (`low`/`medium`/`high`) from the
three subagents.

- **All three the same, or adjacent** (e.g. low/low/medium):
  `agent_consensus = "aligned"`, `human_review_recommended = false`
- **Two agree, one differs by one step** (e.g. low/low/high, or
  medium/medium/low): `agent_consensus = "partial"`,
  `human_review_recommended = false` unless the outlier is `"high"`, in
  which case `true`
- **Genuine conflict on what appears to be the same underlying change**
  (e.g. one agent treats an aspect of the change as routine/low-risk while
  another treats a related aspect as high-risk): `agent_consensus =
  "diverged"`, `human_review_recommended = true`

When consensus is `"partial"` or `"diverged"`, write a one-sentence
`disagreement_note` explaining specifically what the agents disagreed
about, referencing the actual finding each agent made - not just their
risk_level labels. If consensus is `"aligned"`, set `disagreement_note`
to `null`.

## Output Schema

Produce strictly this JSON:

```json
{
  "true_summary": "string",
  "undisclosed_changes": ["string", ...],
  "scope_flags": [{"type": "beyond scope" | "incomplete", "detail": "string"}],
  "predicted_questions": [
    {"question": "string", "file": "string", "line": "number or range"}
  ],
  "communication_debt_score": 0-100,
  "score_breakdown": {
    "description_gap": 0-40,
    "scope_creep": 0-30,
    "unanswered_risk": 0-30
  },
  "agent_consensus": "aligned" | "partial" | "diverged",
  "human_review_recommended": true | false,
  "disagreement_note": "string" | null
}
```

## Design principle

Each subagent runs isolated, with no shared context - this is a hard
architectural constraint, not a preference, and it's what makes "three
independent parallel subagents" a real, demoable claim rather than one
sequential conversation wearing three hats. Synthesis is the single point
where their independent judgments are allowed to meet, compared, and
combined. This is also why disagreement detection is meaningful here and
nowhere else: if the subagents could see each other's output during their
own analysis, any measured "agreement" would be circular rather than a
genuine sign that independent reasoning converged.