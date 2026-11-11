# sessions: native sessions

## Design Overview

- **Why it exists**: the backbone structure for session distillation — the knowledge of one collaboration session is archived as a backbone page, high-value topics promoted to standalone notes. In the original wiki vision sessions were a first-class zone; when merged into notes on 2026-09-08 they were demoted to a type, with the structure lodged in the save command; once this plugin was established the structure returned home and the command went back to pure operation — an example of separating territory and command responsibilities
- **Key rulings**:
  - Session pages are minutes, not mirrors: once the conversation fades the page is the true copy, writing is birth — a specimen of wiki provenance determination
  - participants required, using the actor convention: recorded even for a single agent; multi-agent collaboration extends the list directly — reserved for the collaborative state
  - Promotion rule: standalone high-value topics rise to notes pages, whose provenance is knowledge rather than session record; the backbone page keeps a wikilink — distillates belong to notes
  - No-regeneration zone: append-only, never modified

## Structure

- `wiki/sessions/**`; default naming `YYYY-MM-DD-<topic>.md`
- type: session, value set in registry; participants required: YAML list, the actor convention being human:name, process:flow name, agent/model id — recorded even for a single agent; multi-agent collaboration extends this list directly
- Backbone page shape: Core Conclusions; Decisions & Rationale; Non-obvious Insights; Open Questions; Related Pages — promoted topics attached via wikilink
- Promotion rule: standalone high-value topics promoted to `wiki/notes/` pages, whose provenance is knowledge rather than session record; the backbone page keeps a wikilink

## Example

`wiki/sessions/2026-09-12-fog-harbor-art-style-finalized.md`:

```markdown
---
type: session
title: Fog Harbor art style finalized
participants: [human:Joss, agent/GLM-5.3]
created: 2026-09-12
tags: [game/art]
---
# Core Conclusions
Low-poly plus volumetric fog finalized; moving on to scene art outsourcing inquiries.

# Decisions & Rationale
Pixel art rejected: poor silhouette readability. See [[notes/fog-harbor-art-style-decision]].

# Non-obvious Insights
The budget-overrun risk concentrates in scene art outsourcing (quoted 168k, 40% over budget).

# Open Questions
The performance budget for volumetric fog on low-end machines?

# Related Pages
- [[notes/fog-harbor-art-style-decision]] (the decision page promoted out of this session)
```

## Invariants

- No-regeneration zone: pipelines and commands append-only, never modify
- Territory boundary complementary with notes: type: session must land in `wiki/sessions/`; all other native notes land in `wiki/notes/`
- Promoted pages belong to the notes territory; this plugin owns only backbone pages

## Changelog

- 0.10 2026-11-09: inject line rewritten to routing-pointer density (issue #49 phase 1, relieves the #48 budget): path + read/write trigger + the one easy-to-break invariant + pointer here; the dropped detail already lives in this file / the manifest
- 0.9 2026-09-23: added the wiki dependency edge — inner plugins attach to wiki, aligning with the domain 0.1 declaration; missed in the 2026-09-22 domainization batch
- 0.8 2026-09-13: made the usage sample pointer explicit — added the `.owfa/plugins/sessions/PLUGIN.md` path, zero priors
- 0.7 2026-09-13: inject source moved to the manifest — deleted the Checks, Usage, Inject, Attachments sections; md returns to pure documentation
- 0.6 2026-09-13: established the Usage section — write-side contracts handed to command injection regions for projection, single text source
- 0.5 2026-09-12: manifest dropped layer — layering abolished: injection order changed to dependency topology plus alphabetical, direction checks removed
- 0.4 2026-09-12: identifiers anglicized — section headers, attached-audit contract keys, type enumerations, pipeline call parameters
- 0.3 2026-09-12: disclosure repair — inlined the full-shape backbone page sample; a cold-start audit guess point: no instances in the zone
- 0.2 2026-09-11: manifest added commands: [save] — save is jointly driven by this plugin and notes
- 0.1 2026-09-10: established — extracted from the save command's long-session segment and the merged notes zone, a return of the 2026-09-08 'subdivision batch two'; territory `wiki/sessions/`; participants uses the actor convention, reserving a multi-agent extension point
