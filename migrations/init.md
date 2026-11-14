---
verb: init
---
Framework first-run (deployment distilled for the agent). The npm channel performs this mechanically — `npx owfadev init <dir>` (package `owfadev`, dual bin `owfa`/`owfadev`; the name `owfa` is frozen on npm) — and this page stays the manual recipe it implements (and the reference for the git channel).

1. Copy `.owfa/` and `.agents/skills/` into the target vault root (v0.4 tree: kernel scripts + protocol + docs + VERSION + the six framework command masters; the release tree carries no plugins — the blessed suite ships embedded at `payloads/personal/`).
2. Write the target AGENTS.md shell (identity + layout paragraphs; the handwritten region is the user's) with the injection markers verbatim — see `.owfa/docs/agents-example.md`.
3. Install the embedded suite offline: `python .owfa/scripts/owfa_kernel.py install personal --path payloads/personal` — its `PKG.yaml` `skeleton:` creates `vault/` · `wiki/notes/` · `wiki/sessions/` · `wiki/vault/` mechanically; do not mkdir by hand.
4. `python .owfa/scripts/owfa_kernel.py all` — validate green, injection region built, skills in sync.
5. First-run verification: drop any file into `vault/`, say "owfa-map", then "owfa-check".
