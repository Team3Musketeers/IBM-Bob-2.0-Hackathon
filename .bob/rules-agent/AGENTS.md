# Project Coding Rules (Non-Obvious Only)

- **No build system** — do not create package.json, requirements.txt, or any build scaffolding unless explicitly asked. The repo is intentionally code-free right now.
- **Meta JSON files are UTF-16 LE** — if writing any script that reads `dataset/*_meta.json`, use UTF-16 LE decoding, not UTF-8. The BOM (`\xff\xfe`) is present.
- **Dataset naming is fixed**: `pr_<number>.diff` + `pr_<number>_meta.json` — do not introduce subdirectories or rename files.
- **Subagent prompts are the source of truth** — when implementing Bob custom modes, always write the prompt as a `.md` file in this repo first, then reference it in Bob config. Never author prompts only inside Bob's UI.
- **Subagents must be stateless with respect to each other** — the three analysis subagents (Description Auditor, Scope Auditor, Tone Auditor) must each receive only the PR diff + metadata as input, with no cross-talk before the synthesis step. Implementing shared state between them breaks the architectural guarantee.
- **Communication Debt Score is produced only at synthesis** — do not have individual subagents emit a score; they emit findings only.
