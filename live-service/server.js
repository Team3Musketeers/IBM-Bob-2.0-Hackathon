// Ghostwriter — live audit service
// Replays the Bob-designed-and-validated prompts (prompts/*.md) against
// a configurable external model API, so a public "paste any PR" demo
// doesn't spend Bobcoins per request.
//
// Architecture note: the 3 subagent calls below are deliberately isolated
// (separate API calls, no shared context between them) to match the same
// "3 independent subagents + synthesis" pattern proven in Bob's Agent mode.

require('dotenv').config();
const express = require('express');
const fs = require('fs');
const path = require('path');
const { jsonrepair } = require('jsonrepair');

const app = express();
app.use(express.json({ limit: '2mb' }));
app.use(express.static(path.join(__dirname, 'public')));

// ---- Load the same prompt files used in Bob, as-is, as system prompts ----
const PROMPT_DIR = path.join(__dirname, 'prompts');
const loadPrompt = (file) => fs.readFileSync(path.join(PROMPT_DIR, file), 'utf8');

// ---- Bundled Bob-audited dataset (the 11 PRs) — used to regenerate a
// missing artifact (e.g. a Review Composer comment) for an already-Bob-
// audited PR WITHOUT re-running the 3 subagents. The scoring in
// audit_results.json was produced and validated inside Bob 2.0; this only
// re-runs the cheap, deterministic-shaped composition step on top of it. ----
const DATASET_DIR = path.join(__dirname, 'dataset');

// Serve a bundled diff by PR number, so the dashboard can request one
// on demand instead of embedding all 11 (some are 250KB+) into the page.
app.get('/api/dataset-diff/:prNumber', (req, res) => {
  const file = path.join(DATASET_DIR, `pr_${req.params.prNumber}.diff`);
  if (!fs.existsSync(file)) return res.status(404).json({ error: 'No bundled diff for this PR number.' });
  res.type('text/plain').send(fs.readFileSync(file, 'utf8'));
});

const PROMPTS = {
  truthTeller: loadPrompt('technical-truth-teller.md'),
  scopeAuditor: loadPrompt('scope-auditor.md'),
  reviewersGhost: loadPrompt('reviewers-ghost.md'),
  synthesis: loadPrompt('synthesis.md'),
  reviewComposer: loadPrompt('review-composer.md'),
};

// All 4 modes, in the order they're offered to the caller. reviewComposer
// runs after synthesis (it depends on the combined audit), never in
// parallel with the other 3 — this order is enforced below, not just
// documented here.
const SUBAGENT_KEYS = ['truthTeller', 'scopeAuditor', 'reviewersGhost'];
const ALL_MODES = [...SUBAGENT_KEYS, 'reviewComposer'];

// ---- Model call — OpenAI-compatible shape ----
// Defaults to Gemini's free, no-credit-card OpenAI-compatible endpoint.
// Get a key at aistudio.google.com (no card required). If you later swap
// to a different provider, only LLM_API_BASE_URL / LLM_API_KEY / LLM_MODEL
// in .env need to change, as long as it speaks the same /chat/completions shape.
async function callModel(systemPrompt, userContent, { attempt = 1, raw = false } = {}) {
  // Only escalate temperature on retries — at temperature 0 a retry after a
  // parse failure just reproduces the exact same (broken) output, since
  // there's no randomness to retry into.
  const temperature = attempt === 1 ? 0 : Math.min(0.5, 0.25 * attempt);

  const jsonInstruction = raw
    ? ''
    : '\n\nRespond with ONLY valid, strictly parseable JSON matching the Output schema above. No prose, no markdown fences, no trailing commas, no missing quotes. Double-check every key is quoted correctly before responding.';

  const res = await fetch(`${process.env.LLM_API_BASE_URL}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${process.env.LLM_API_KEY}`,
    },
    body: JSON.stringify({
      model: process.env.LLM_MODEL,
      temperature,
      messages: [
        { role: 'system', content: `${systemPrompt}${jsonInstruction}` },
        { role: 'user', content: userContent },
      ],
    }),
  });

  if (!res.ok) {
    throw new Error(`Model call failed (${res.status}): ${await res.text()}`);
  }

  const data = await res.json();
  let text = data.choices?.[0]?.message?.content ?? '';

  // Raw mode (Review Composer): return the Markdown as-is, no JSON parsing.
  if (raw) return text.trim();

  text = text.replace(/^```(?:json)?\s*/i, '').replace(/```\s*$/i, '').trim();

  // 1st attempt: parse as-is.
  try {
    return JSON.parse(text);
  } catch {
    // 2nd attempt: auto-repair common near-valid-JSON slips (missing
    // quotes around keys, trailing commas, etc.) before giving up on
    // this response entirely.
    try {
      return JSON.parse(jsonrepair(text));
    } catch (err) {
      if (attempt < 3) {
        return callModel(systemPrompt, userContent, { attempt: attempt + 1, raw });
      }
      throw new Error(`Model did not return valid JSON after ${attempt} attempts, even after repair:\n${text}`);
    }
  }
}

// ---- Fetch a PR's diff + description straight from GitHub if a URL is given ----
async function fetchFromGithub(prUrl) {
  const match = prUrl.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
  if (!match) throw new Error('Could not parse a GitHub PR URL (expected .../owner/repo/pull/123)');
  const [, owner, repo, number] = match;

  const headers = { Accept: 'application/vnd.github+json' };
  if (process.env.GITHUB_TOKEN) headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;

  const metaRes = await fetch(`https://api.github.com/repos/${owner}/${repo}/pulls/${number}`, { headers });
  if (!metaRes.ok) throw new Error(`GitHub PR lookup failed (${metaRes.status})`);
  const meta = await metaRes.json();

  const diffRes = await fetch(`https://api.github.com/repos/${owner}/${repo}/pulls/${number}`, {
    headers: { ...headers, Accept: 'application/vnd.github.v3.diff' },
  });
  if (!diffRes.ok) throw new Error(`GitHub diff fetch failed (${diffRes.status})`);
  const diff = await diffRes.text();

  return {
    title: meta.title,
    original_description: meta.body || '(no description)',
    diff,
  };
}

// ---- Main endpoint ----
// Body: EITHER { prUrl } OR { title, original_description, diff, linked_ticket }
// Plus optional `modes`: array of which of the 4 modes to run, from
// ['truthTeller','scopeAuditor','reviewersGhost','reviewComposer'].
// Defaults to all 4. This lets the caller run only the subagents they
// want — e.g. skip Scope Auditor if there's no linked ticket to compare
// against, or skip Review Composer if they just want the raw score.
app.post('/api/audit', async (req, res) => {
  try {
    let { prUrl, title, original_description, diff, linked_ticket, modes, precomputedAudit } = req.body;

    if (prUrl) {
      const fetched = await fetchFromGithub(prUrl);
      title = fetched.title;
      original_description = fetched.original_description;
      diff = fetched.diff;
    }

    const requestedModes = Array.isArray(modes) && modes.length ? modes : ALL_MODES;
    const invalid = requestedModes.filter((m) => !ALL_MODES.includes(m));
    if (invalid.length) {
      return res.status(400).json({ error: `Unknown mode(s): ${invalid.join(', ')}. Valid: ${ALL_MODES.join(', ')}` });
    }
    const runSubagent = (key) => requestedModes.includes(key);
    const runReviewComposer = requestedModes.includes('reviewComposer');

    // ---- Fast path: an already-Bob-validated audit was supplied directly
    // (from the "Bob-Audited Dataset" tab, for a PR that's missing e.g. a
    // Review Composer output). Skip the 3 subagents and synthesis entirely
    // - that scoring was already produced and validated inside Bob 2.0 -
    // and go straight to composing the requested missing artifact on top
    // of it. This keeps the Bob-produced numbers authoritative; only the
    // formatting/composition step is re-run live. Only needs a diff, not a
    // fresh description, since the cached audit already carries everything
    // Review Composer needs to know about the PR. ----
    if (precomputedAudit && runReviewComposer) {
      if (!diff) return res.status(400).json({ error: 'precomputedAudit requires diff.' });
      const review_comment = await callModel(
        PROMPTS.reviewComposer,
        JSON.stringify({ ...precomputedAudit, diff }),
        { raw: true }
      );
      return res.json({
        pr_title: title || null,
        original_description: original_description || null,
        ...precomputedAudit,
        review_comment,
        _source: 'precomputed_audit+live_composition',
      });
    }

    if (!diff || !original_description) {
      return res.status(400).json({ error: 'Provide either prUrl, or diff + original_description directly.' });
    }

    // The 3 audit subagents that CAN run in parallel — only the ones the
    // caller actually selected. Still fully isolated from each other,
    // matching the Block H parallel-dispatch pattern; the only difference
    // from before is that some may simply not run at all.
    const [truthTeller, scopeAuditor, reviewersGhost] = await Promise.all([
      runSubagent('truthTeller')
        ? callModel(PROMPTS.truthTeller, JSON.stringify({ diff, original_description }))
        : Promise.resolve('not_run'),
      runSubagent('scopeAuditor')
        ? callModel(PROMPTS.scopeAuditor, JSON.stringify({ diff, original_description, linked_ticket: linked_ticket || null }))
        : Promise.resolve('not_run'),
      runSubagent('reviewersGhost')
        ? callModel(PROMPTS.reviewersGhost, JSON.stringify({ diff, original_description }))
        : Promise.resolve('not_run'),
    ]);

    // Synthesis — the only step allowed to see all three outputs together.
    // Subagents that didn't run are passed through explicitly as "not_run"
    // rather than omitted, so synthesis can score around the gap instead
    // of silently treating a skipped check as a clean one.
    const synthesisInput = {
      technical_truth_teller: truthTeller === 'not_run' ? 'not_run' : {
        true_summary: truthTeller.true_summary,
        undisclosed_changes: truthTeller.undisclosed_changes,
        risk_level: truthTeller.risk_level,
      },
      scope_auditor: scopeAuditor === 'not_run' ? 'not_run' : {
        scope_flags: scopeAuditor.scope_flags,
        ticket_linked: scopeAuditor.ticket_linked,
        risk_level: scopeAuditor.risk_level,
      },
      reviewers_ghost: reviewersGhost === 'not_run' ? 'not_run' : {
        predicted_questions: reviewersGhost.predicted_questions,
        risk_level: reviewersGhost.risk_level,
      },
      original_description,
      diff,
    };
    const audit = await callModel(PROMPTS.synthesis, JSON.stringify(synthesisInput));
    audit.subagents_skipped = audit.subagents_skipped || SUBAGENT_KEYS.filter((k) => !runSubagent(k));

    // Review Composer runs strictly after synthesis — it depends on the
    // combined audit, never in parallel with the 3 audit subagents.
    let review_comment = null;
    if (runReviewComposer) {
      review_comment = await callModel(PROMPTS.reviewComposer, JSON.stringify({ ...audit, diff }), { raw: true });
    }

    res.json({
      pr_title: title || null,
      original_description,
      ...audit,
      review_comment,
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Ghostwriter live service running on :${PORT}`));