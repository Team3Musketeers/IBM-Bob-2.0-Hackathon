# Ghostwriter — Sprint 1 Progress Update
**All 3 subagents built and individually validated. Repo pushed, 9 commits in.**

---

## ✅ What's Done Since Last Update

### All 3 subagents exist as real Bob custom modes
Created and configured in Bob IDE, exported to `bob-custom-modes.yaml` (version-controlled, matches our `AGENTS.md` convention):

- **`technical-truth-teller`** — Read-only. Independently describes what a diff actually does.
- **`scope-auditor`** — Read-only. Compares diff against linked ticket, flags scope creep or incomplete work.
- **`reviewers-ghost`** — Read-only. Predicts specific, risk-focused reviewer questions grounded in the diff.

Prompt source files also committed separately in `prompts/` (per our own documented convention: prompts live in the repo before being configured in Bob's UI).

### Every subagent has now been individually tested against real PRs — and they all work

**Technical Truth-Teller — 2/2 strong results:**
- **#69899** (terse "add missing rtl css rule"): correctly explained the actual CSS selector logic in detail — far beyond the one-line title.
- **#69766** (vague "update imports"): this is our best example so far. It caught a real behavioral change buried in a mechanical-looking refactor — a destructure moved from module scope into a component's render body, meaning values now re-evaluate on every render instead of once. The title gave zero hint of this.

**Scope Auditor — 3/3 correct, including a real catch:**
- **#69784** (good control, Closes #67697): correctly stayed clean — verified the fix against the actual ticket text and confirmed the CSS change matched exactly what was reported.
- **#69571** (Closes #68170, "proper component" refactor): **flagged real undisclosed scope** — a new 50-line test file was added that the ticket never asked for and the PR description never mentioned. This is a genuinely interesting edge case: is *adding good test coverage* actually a scope violation, or is Scope Auditor being too strict? **Open team decision, see below.**
- We also pulled the real ticket bodies (`dataset/issue_67697.json`, `68170.json`, `69473.json`) instead of relying on the PR description as a proxy — this sharpened the analysis quality on the retest.

**Reviewer's Ghost — 1/1, and it's our strongest single result of the night:**
- **#69487** (PayPal library swap): generated 5 sharp, specific questions. The standout: it noticed an old TODO comment flagging a suspected bug (`details` vs `data` confusion in the payment capture flow) and caught that **the exact same suspected bug was carried forward** into the new implementation. That's a real, provable finding — not a guess.

### Repo status (per your screenshot)
9 commits on `main`, everything pushed: `.bob/` (custom mode configs), `bob_sessions/`, `dataset/` (11 PR pairs + 3 ticket bodies), `prompts/`, `AGENTS.md`, `LICENSE`, `block3-dataset-log.md`, `block4-subagent-prompts.md`, `bob-custom-modes.yaml`.

---

## ⚠️ One Open Decision for the Team

Scope Auditor flagged #69571's new test file as "beyond scope" because it wasn't disclosed — but adding tests for a bug fix is generally *good practice*, not a red flag. We need to decide:
- **Option A:** keep strict disclosure rules — even good additions should be mentioned
- **Option B:** teach Scope Auditor to distinguish "concerning" undisclosed scope (behavior/dependency changes) from "benign" undisclosed scope (tests, comments) and weight them differently in the final score

This affects the Communication Debt Score formula in Sprint 2 — worth 5 minutes of discussion before we lock the scoring logic.

---

## 🔜 Next: Block H — Parallel Orchestration (the big one)

All three subagents work individually. The next step is wiring them to run **simultaneously via Agent mode** on the same PR, with no shared context between them, followed by a synthesis step that produces the final Communication Debt Score. This is the single most judge-visible piece of the whole project — it's the direct proof of the "parallel subagents" feature the hackathon brief explicitly asks for.

After that: dashboard wiring (Sprint 2) and the demo video.
