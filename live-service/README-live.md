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

## Docker (this is what your teammate's image is actually for, if you want it)

```
docker build -t ghostwriter-live .
docker run -p 3000:3000 --env-file .env ghostwriter-live
```

This is a genuinely good use of a Docker image — it's not the dashboard
(which stays static, per earlier decision), it's specifically this live
audit endpoint. If you deploy it somewhere reachable (Render, Fly.io,
etc.), your dashboard's "paste a PR" box points at that URL instead of
`localhost`.

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
