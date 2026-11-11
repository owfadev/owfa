# domain: Domain Abstraction

## Design Summary

- **Why it exists**: the **outer root** of the dual-root concept — the ontological declaration of "outer": wiki recognizes only inner and outer; a domain is the form in which information sources outside wiki exist, i.e. an adapter contract waiting to be filled in. A concept-declaration plugin: it establishes the abstraction, laws, and disciplines; concrete domains are instantiated via depends edges — the source of the domain growth mechanism, see Section 8 of mechanics
- **Key rulings**:
  - Six contract questions: external territory, landing strategy, identity proof, wiki-side territory, write model, trust model. Designing a domain means answering them one by one
  - Three laws: landing is essentially a write-model choice; translation cost determines projection density; governance pages live inside wiki, governance targets outside
  - Two disciplines plus the admission ticket: borrowing vault or pointers is the default posture, self-standing containers are the exception — when to except: write-model divergence, or structural-rigidity divergence; domains must be discoverable within wiki; reconcilability is the admission ticket — relics whose source has already vanished do not establish a domain, they belong to the native territory
  - Instantiation is expressed entirely in the depends graph: domain bases connect directly to this plugin, in-domain plugins belong to their domain transitively; inner-side plugins attach to wiki, not to this plugin

## Structure

No structure or files of its own. Instantiation is expressed entirely in the depends graph: domain-base plugins depend directly on this plugin; in-domain plugins depend on their respective domains — e.g. structure depends on vault, lark-docs depends on lark — transitivity means membership; inner-side plugins such as notes and sessions attach to wiki, not to this plugin.

## Invariants

Six contract questions, each domain answers for itself:

- External territory — where the information lives: `vault/`, systems reachable via lark-cli, `projects/**`
- Landing strategy — materialize via vault, self-standing container, pointer without landing
- Identity proof — vault uses path plus hash; lark uses a one-to-one token-to-page mapping; project uses path plus a two-way diff against the declaration page
- Wiki-side territory — where the domain's projection pages live: `wiki/vault/`, `wiki/lark/<profile>/`, declaration pages; territory paths are self-disclosed by each domain's injection line
- Write model — append-only, full read/write, regenerable overwrite
- Trust model — immutable originals, lazy TTL refresh, living documents

Three laws:

- The landing choice is essentially a write-model choice: final-state assets go into an append-only repository, e.g. vault; process containers get full read/write, e.g. project; when truth lives elsewhere, use pointers, e.g. lark
- Translation cost determines projection density: arbitrary formats take a 1:1 mirror; behind APIs take pointer pages; md-native takes declaration-only disclosure
- Governance pages inside wiki, governance targets outside — structure.md and profile.md share the same shape

Two disciplines:

- Borrowing vault or pointers is the default posture, self-standing containers are the exception — when to except: write-model or structural-rigidity divergence; project landing in vault would be crippled, that is the paradigm case
- Domains must be discoverable within wiki: declaration page or injection line; unregistered means nonexistent
- A domain's admission ticket is reconcilability: the external territory is alive and accessible, identity proof can be established, and the wiki-side territory path is stated within the domain declaration — only when all three are in place may a domain be established; relics whose source has already vanished, e.g. session minutes — once the conversation runtime vanishes the page is the true body — do not establish a domain, they belong to the native territory

Where the entropy goes: cross-domain semantic disambiguation is completed at adapter write time, reads rely on path origin; within wiki the vocabulary stays unified and the link graph fully connected; the tag doctrine is untouched, free growth within domains keeps holding.

## Changelog

- 0.3 2026-11-11: the pointer line now carries the dual-track skill preference rule (v0.4 A4, work order #56) — core skills are `owfa-*` and preferred over same-type foreign skills (correctness: the framework defines what they mean); connectors pick the registered/best-fitting transport, the official one is only the default recommendation (capability fit wins). Core command skills renamed with the 0.4 layout batch (`owfa-check/docs/map/plugin/profile/query/save/kernel`); natural-language triggers keep the old words so muscle memory still fires.
- 0.2 2026-11-09: inject line rewritten to routing-pointer density (issue #49 phase 1, relieves the #48 budget): path + read/write trigger + the one easy-to-break invariant + pointer here; the dropped detail already lives in this file / the manifest
- 0.1 2026-09-22: established — distilled from the 2026-09-19 domain problem report and four rounds of discussion; the three instances vault, lark, and project brought into compliance first
