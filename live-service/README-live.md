# Ghostwriter — Live Service (paste any PR)

Runs your 3 Bob-designed-and-validated subagent prompts + synthesis against
a real PR, on demand, without spending Bobcoins per request.

## What this is / isn't

- **Is:** the same prompts you built and proved in Bob (`prompts/*.md`),
  replayed against a general model API for anyone who pastes a PR.
- **Isn't:** Bob itself running live. Be explicit about this distinction
  in your Bob Usage Statement — "designed and validated in Bob 2.0; the
  public live demo reuses those exact prompts against [provider] for
  quota reasons" is the honest, still-strong framing.

## Setup

1. Copy your actual prompt files in:
   ```
   cp ../prompts/technical-truth-teller.md live-service/prompts/
   cp ../prompts/scope-auditor.md live-service/prompts/
   cp ../prompts/reviewers-ghost.md live-service/prompts/
   cp synthesis.md live-service/prompts/    # the updated one from earlier
   ```
2. `cp .env.example .env`. The default is Google's Gemini API — free,
   no credit card: go to https://aistudio.google.com/apikey, sign in
   with any Google account, click "Create API key", paste it in as
   `LLM_API_KEY`. Takes under 2 minutes. Gemini's endpoint is
   OpenAI-compatible, so `server.js` needs no special auth dance —
   just the key.
   (If your watsonx billing verification clears later and you still
   want it: swap `LLM_API_BASE_URL`/`LLM_MODEL` back, but note watsonx's
   native API isn't OpenAI-shaped — you'd need the IAM-token version of
   `callModel()` again, not this one.)
3. `npm install`
4. `npm start` → open `http://localhost:3000`

If you skip the `.env`, the page still loads but every audit returns a
503 telling you what's missing — the server prints the same list at boot.

### Picking a model

`LLM_MODEL` must be a model ID your API key can actually reach. The default
`gemini-3.5-flash-lite` is verified working. Older 2.x IDs such as
`gemini-2.5-flash-lite` now return `404 "no longer available to new users"`,
which fails every audit — if you see that error, the model is the problem,
not the key. To list what your key can call:

```
curl "https://generativelanguage.googleapis.com/v1beta/models" \
     -H "x-goog-api-key: $LLM_API_KEY"
```

## Docker (this is what your teammate's image is actually for, if you want it)

```
docker build -t ghostwriter-live .
docker run -p 3000:3000 --env-file .env ghostwriter-live
```

Or via compose (needs the `.env` in place first):

```
docker compose up --build        # -> http://localhost:3000
```

The build is reproducible: it installs from the committed
`package-lock.json` with `npm ci`, and `.dockerignore` keeps your local
`node_modules` out of the image so it can't overwrite the container's own
Linux copy. The image runs as a non-root user.

This is a genuinely good use of a Docker image — it's not the dashboard
(which stays static, per earlier decision), it's specifically this live
audit endpoint. If you deploy it somewhere reachable (Render, Fly.io,
etc.), your dashboard's "paste a PR" box points at that URL instead of
`localhost`.

## The bundled dataset

`GET /api/dataset-diff/<prNumber>` serves a diff from the Bob-audited
dataset, so a UI can pull one on demand instead of embedding all 11.
It resolves `./dataset` first, then `../dataset`, and honours
`DATASET_DIR` in `.env`. Note the Docker image only contains
`live-service/`, so set `DATASET_DIR` (and mount that folder in) if you
want this endpoint to work in a container.

## "Re-verify against Gemini" (dashboard)

Every row in the **Validated audits** tab has a button that re-runs the
same 3 subagents + synthesis against the live PR (via `prUrl`) and puts
Gemini's score next to the one Bob produced in Bob 2.0:

| Metric | Bob 2.0 | Gemini live | Δ |
|---|---|---|---|
| Communication debt /100 | 68 | 50 | -18 |
| Description gap /40 | 30 | 25 | -5 |
| Scope creep /30 | 14 | 15 | +1 |
| Unanswered risk /30 | 24 | 10 | -14 |

Cost is 4 model calls and ~10–15s per click (Review Composer is skipped
because the score comparison doesn't need it).

**Read the delta as directional, not exact.** Two runs of the same PR
through the same prompts produced 50 and 38. The synthesis step is a
long reasoning task, so scores vary run to run even at temperature 0
(temperature only rises on a JSON-parse retry). The component-level
columns are the more stable signal — on the PR above, Bob and Gemini
agreed closely on *scope creep* (14 vs 15) and diverged most on
*unanswered risk* (24 vs 10). If you demo this, show the breakdown
rather than leaning on the single headline number, or run it a few times
and show the spread.

## Known limits worth knowing before the demo

- **GitHub rate limits**: unauthenticated PR lookups are capped at 60/hour
  per IP. Fine for a live demo, set `GITHUB_TOKEN` if you'll test a lot.
- **No auto-ticket-linking**: pasting a PR URL fetches the diff + description
  automatically, but the linked ticket must still be pasted manually — GitHub
  doesn't expose a reliable "linked issue" API field for arbitrary repos.
- **No repo-wide context**: Bob's subagents had full-repo access via `/init`;
  this endpoint only sees the diff + description + (optional) ticket text.
  Technical Truth-Teller in particular may be slightly less sharp on
  cross-file implications than it was inside Bob. Worth a line in your
  statement rather than a surprise on stage.
- **Cost**: every paste = 4 model calls (3 subagents + synthesis). Fine for
  a demo, but don't leave this publicly exposed with no rate limiting if
  you deploy it past the hackathon.
