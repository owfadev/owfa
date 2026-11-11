# Action discipline: path zones × action tiers

> The semantic shape of permissions: this table does not rely on code for "enforcement", but deterministic structural operations are entrusted to scripts (`.owfa/scripts/owfa_kernel.py`: compliance / dependencies / injection / registry / copy sync; `.owfa/scripts/pipeline.py`: index / tags rebuild, hot / log rolling, post-write self-attestation), while semantic judgment is entrusted to the LLM; the agent consults this table before acting, and check audits afterwards from script output and git traces.
> Four execution principles: deterministic structural operations go through scripts, semantic judgment through the LLM; rules spell out in plain text "how to do" rather than "what it is"; if one read suffices, there is no second scan (call frugality); write commands must close with `pipeline.py verify` self-attestation (the minimal attester form: the LLM executes, the script attests).

## Path zones

| Zone | Paths | Nature |
|---|---|---|
| Regenerable | `wiki/index.md`, `wiki/tags.md`, `wiki/hot.md`, the `.owfa/protocol/registry.yaml` plugins section | Derived projections, wholly rebuildable; the pipeline may rerun freely |
| Precious | `wiki/notes/**`, `.owfa/plugins/**`, `.owfa/command/**`, the AGENTS.md hand-written region | Append-only or human-edited |
| Immutable | existing entries of `wiki/log.md` and `wiki/archive/**`, `vault/**` (from the command's perspective) | Content must not be rewritten after writing |
| Workspace | `projects/**` | Full agent read-write authority (in contrast to the append-only vault); the self-describing `project.md` accompanies each project |
| Temporary | `wiki/tmp/**` | No retention promise, may be cleaned; invisible to the derived layer (index/tags/link graph), exempt from broken-link checks |

## Action tiers

| Tier | Typical actions | How executed |
|---|---|---|
| Mechanical-auto | index / tags / registry rebuild, injection-region rebuild, hot window eviction, log archival routing, hash recalculation, query log lines, command copy sync, post-write self-attestation | Execute directly (whatever scripts can do goes through scripts: `owfa_kernel.py` and `pipeline.py`), no asking |
| Mechanical-confirm | tag merges (batch edits to plugin fields), reserved-field migration, tmp over-age cleanup (present list, delete after confirmation) | Present the list, execute after confirmation |
| Semantic-report | note-merge suggestions, near-duplicate alerts, staleness judgments on proxy descriptions | Report the differences; the human decides |
| Always-human | deletion, history rewriting, changes to existing `vault/` files, rewriting note bodies | Commands never execute these; ghost-writing on explicit user instruction must leave a log trace |

The criterion: touching "plugin-owned fields or regenerable pages" → mechanical; touching "bodies or existing history" → human.

## Commit discipline

> In this framework git is process-layer infrastructure (version control / audit evidence / lockfile), not a plugin; this section gives the commit rules for data-zone writes—for the engineering side see constitution principle 8; the two domains do not encroach on each other.

- **One write operation = one commit**: one map / save / profile / check fix, together with all its derived products (pages + index / tags / hot / log + new vault assets), enters the commit atomically; commit only after verify passes—what is committed is what has been self-attested; no commit when nothing changed
- **Message format `module: summary`** (isomorphic with the engineering side; module word + half-width colon): the data-zone module vocabulary is taken from the commands, defined at this single point and not re-copied into command docs—`map: <asset name>`, `save: <page title>`, `profile: <one-liner>`, `check: <conclusion>`, `query: <topic>`
- **The agent only adds paths it has written; `git add -A` is forbidden**: commit rights over human hand edits (vault deletions/changes, manual wiki edits) belong to the human—the agent only reports; committing on someone's behalf requires explicit user instruction
- No pushing; history rewriting is forbidden (constitution principle 8, globally applicable)

## Rolling mechanisms (spelled out)

- **log**: main-file window ≤100 entries (about 14k characters). Write log entries via `pipeline.py log <type> "<one-liner>"`—on overflow, the oldest stretch is moved, grouped by entry month, into `wiki/archive/YYYY-MM/log.md`; entry content is unchanged to the character, only relocated; the archive directory falls into the immutable zone
- **hot**: ≤25 entries, <5 days, ≤200 characters per entry. Write hot entries via `pipeline.py hot <type> "<one-liner>"`—out-of-window entries are evicted and over-long entries truncated automatically before writing
- **Index / registry**: on deviation from reality → rebuild directly inside check (`pipeline.py index` / `tags`; `owfa_kernel.py all`), no asking
- **Vocabulary**: before writing tags, map / save first reads `wiki/tags.md` (the derived zone is the vocabulary), preferring to reuse existing words; near-duplicate merging is a mechanical-confirm item
- **Parameter ownership**: mechanical parameters such as rolling windows defer to the `pipeline.py` source (the script source is the rule list), while plugin PLUGIN.md files keep the semantic explanations—commands and docs do not re-copy the numbers
