# mapping: vault Domain Mapping Rules

## Design Summary

- **Why it exists**: the mapping rules of the vault domain — maps every file in `vault/` to a proxy page in `wiki/vault/`, executed by the map command; projections of arbitrary-format assets take the 1:1 mirror density, the densest end of projection density, see Section 8 of mechanics. A proxy is the asset's representative in the md world: registration plus a one-line description to start, summaries are optional enhancements
- **Key rulings**:
  - 1:1 mirror with zero exceptions: md files also get proxies, preventing confusion between wiki-native and proxy; proxy name = original name plus .md, preventing name collisions
  - The hash is a mismatch detector, not an enforcer: disposition of original changes goes through check triage, and triage writes a log line when done — mapping does not adjudicate
  - Proxy pages belong to the regenerable zone: precious content goes into notes, not proxy pages; the body never copies the full original text — a proxy is not a copy

## Structure

- `wiki/vault/**` and `vault/**` in a one-to-one mirror: paths isomorphic; proxy file name = the original file's full name plus `.md` — e.g. `a.pdf` corresponds to `a.pdf.md`, preventing name collisions
- md files also get proxies, no exceptions

## Invariants

- The path is the origin proof: pages under `wiki/vault/` always have a vault counterpart; the origin-dichotomy concept belongs to the wiki plugin. Reserved name `index.md` exemption — directory indexes belong to the navigation layer, not concept pages; having no vault counterpart does not count as an orphan proxy
- The registration fields raw_file and raw_sha256 are mechanically recomputable from vault
- Proxy pages belong to the regenerable zone: pipelines may rerun and overwrite; precious content is written into notes, not kept in proxy pages
- A proxy body must not copy the full original text

## Changelog

- 0.8 2026-09-22: domain-ization — the first paragraph renamed from "bridge plugin" to "vault domain mapping rules", zero change in semantics and mechanism, positioning set right; depends keeps the two ends vault and wiki
- 0.7 2026-09-14: vault governance batch — orphan-proxy messages gained reference counts, see the impact surface before deleting; triage writes a log line right after recalculation, leaving an audit trail of changes — under the snapshot model, mismatch facts used to vanish silently; usage gained the url registration contract, the write side of vault source preservation
- 0.6 2026-09-13: attached audit gained the hard check for missing registration fields — expert review: the injection region said always-present while the attached audit silently skipped
- 0.5 2026-09-13: usage absorbed the diary-type exemption — moved in from the map command's prohibitions, removing the body echo
- 0.4 2026-09-13: injection source moved to the manifest — removed Fields, Checks, Usage, Inject, Attachments sections, md returned to pure documentation
- 0.3 2026-09-13: established the "Usage" section — the write-side contract is projected by the command's injection region, a single text source
- 0.2 2026-09-12: command ingest renamed map and slimmed — the polishing questions removed, pure registration; vault governance discussed separately
- 0.1 2026-09-12: renamed and established from the vault plugin, version restarted, old history in git — semantically depends on vault and wiki; the clause "commands are append-only toward vault, freedom to delete and modify belongs to the human" moved to the vault concept plugin's injection line; the origin-dichotomy concept moved to the wiki plugin
