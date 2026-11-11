# tmp: temporary zone

## Design Overview

- **Why it exists**: the wiki's /tmp — a legitimate home for drafts and parsing intermediates. All the framework's territories until now were formal: immutable, append-only, sources of truth; intermediate states had nowhere to go. This plugin fills the gap: failure allowed, incompleteness allowed
- **Key rulings**:
  - Invisible to the derived layer, treated like archive: absent from index and tags, never a link source, broken links exempt — [[a page not yet written]] in a draft is the normal state of 'not yet written down'; closure is required only upon promotion
  - No retention promise, yet no automatic cleanup: cleanable at any time; disposal goes through confirmation — check reports the over-age list; promotion or deletion belongs to the human. Deletion belongs to the human, breaking nothing
  - Delete the draft upon promotion: promote precious drafts promptly, via save into notes or merged into a project decision section; tmp hoards no treasures
  - The path is the territory: everything under `wiki/tmp/**` is tmp

## Structure

- `wiki/tmp/**` — the path is the territory; everything below is tmp; type optional, `type: tmp` landing outside the territory → error
- Flat layout tolerated, subdirectories free, no reserved-name constraints

## Invariants

- No retention promise, the /tmp contract: cleanable at any time; promote precious drafts promptly — via save into notes, merged into a project decision section, etc. — deleting the draft upon promotion
- Cleanup is never automatic: parsing intermediates set `stale_after` as they go, check reports the over-age list, disposal goes through confirmation; drafts without stale_after are not flagged — deletion belongs to the human, breaking nothing
- The invisibility triple: excluded from concept-page determination, unseen by index and tags; under link never a link source and exempt from graph checks; hot naturally uninvolved, being hand-written
- Sensitivity reminder: parsing intermediates may contain personal data such as chat transcripts; instances may gitignore `wiki/tmp/`

## Changelog

- 0.4 2026-11-09: inject line rewritten to routing-pointer density (issue #49 phase 1, relieves the #48 budget): path + read/write trigger + the one easy-to-break invariant + pointer here; the dropped detail already lives in this file / the manifest
- 0.3 (2026-10-06) inject line: code formatting restored on the territory path (issue #12 post-migration nit)- 0.2 (2026-10-06) inject line compressed to pointer density (issue #12 layer discipline) — procedural detail lives in usage / PLUGIN.md / skills- 0.1 2026-09-19: established — path-as-territory, invisible to the derived layer, stale_after cleanup prompts, delete upon promotion
