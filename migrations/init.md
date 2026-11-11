---
verb: init
---
Framework first-run (deployment, the deployment guide distilled for the agent). The npm channel performs this mechanically — `npx owfa init <dir>` — and this page stays the manual recipe it implements (and the reference for the git channel).

1. Copy `.owfa/` and `.agents/skills/` into the target vault root (minimal core variant: `plugins/core/` + protocol + scripts + docs + VERSION + command).
2. Write the target AGENTS.md shell (identity + layout paragraphs; the handwritten region is the user's) with the injection markers verbatim — see `.owfa/docs/agents-example.md`.
3. Create the four empty directories: `vault/` · `wiki/notes/` · `wiki/sessions/` · `wiki/vault/`.
4. `python .owfa/scripts/owfa_kernel.py all` — validate green, injection region built, skills in sync.
5. First-run verification: drop any file into `vault/`, say "owfa-map", then "owfa-check".
