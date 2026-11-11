# vault: Default Domain

## Design Summary

- **Why it exists**: the first instance of domain, i.e. the **default domain** — a repository holding real assets: any format enters as-is, integrity registered by hash. Dual role: itself a local-file domain; and doubling as the general asset repository where other domains land on demand, the `url` field being the passthrough interface — bb and email attachment materialization goes through this channel
- **Key rulings**:
  - Append-only on the command side, freedom to delete and modify belongs to the human: agent writes only produce new files — immutable originals are the foundation of trust; proxies and indexes are all regenerable, only the original is the single truth
  - A concept-declaration plugin: it only states what vault is and what rules it sets — mapping rules belong to mapping, layout rules to structure, the domain contract to domain; a symmetric division of labor with the wiki side's "concept and structure"
  - Governance deferred, all three blocks claimed by 0.4: source preservation is the url field; structure rules moved to structure; lifecycle propagation belongs to mapping working with check — a paradigm of establishing the concept first and claiming after real use

## Structure

No structure or scripts of its own. The external territory is the root-level `vault/` container itself; the wiki-side territory is `wiki/vault/`, territory conventions belong to mapping.

## Invariants

- The command side is append-only toward vault: agent writes only produce new files, never modifying existing ones
- Freedom to delete and modify belongs to the human: deleting, modifying, moving are human rights, commands do not perform them
- Immutable originals are the foundation of trust: proxies and indexes are all regenerable, only the original is the single truth

## Changelog

- 0.7 2026-11-09: inject line rewritten to routing-pointer density (issue #49 phase 1, relieves the #48 budget): path + read/write trigger + the one easy-to-break invariant + pointer here; the dropped detail already lives in this file / the manifest
- 0.6 2026-10-02: global-domain batch one — added the trust and log mandatory-bridge edges; vault previously lacked even the trust edge, confirmed by audit; constitution principle 11, kernel verifies completeness
- 0.5 2026-09-22: domain-ization — depends gained domain, i.e. the default-domain positioning, and wiki, i.e. the territory declaration `wiki/vault/`; the dual role spelled out: doubling as the landing repository for other domains, the url field as the passthrough interface
- 0.4 2026-09-14: all three governance blocks claimed — source preservation, claiming the registry-reserved field `url`, provenance registration for URL-type assets, the write contract in mapping usage; structure rules moved to the structure plugin established at 0.1; lifecycle and change propagation go to mapping reference counting with recomputation audit trails, in coordination with check triage
- 0.3 2026-09-13: injection source moved to the manifest — removed Checks, Inject, Attachments sections, md returned to pure documentation
- 0.2 2026-09-13: purification — removed functional references to mapping and check, rules stated self-sufficiently
- 0.1 2026-09-12: established — concept-declaration plugin; governance deferred: source preservation, structure rules, and lifecycle suggestions to be claimed after real use
