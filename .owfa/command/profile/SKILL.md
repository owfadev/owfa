---
name: profile
owner: user-profile
consumes: [user-profile, trust, index, hot, log]
description: "Maintain the user profile wiki/profile.md: recognize self-description and behavioral signals, update assertions convergently (new values replace old, changes leave traces in the body, evidence wikilinks); construction and consolidation go through a whole-page rewrite preview. Triggers on: profile, 更新画像, 画像更新, update profile."
---

# profile: profile update

Write the continuing cognition about the user into a checkable page: assertions carry evidence, preferences expire, updates leave traces. The direction is "inner → user cognition" — orthogonal to map (outer → inner translation) and save (sessions landing on disk); convergent across sessions, not a transactional one-shot. Write-side contracts (signal criteria, layered placement, assertion format, convergence traces) are in the injection region.

## Scope

Write: user-profile (wiki/profile.md), log, hot, index
Read: registry (`.owfa/protocol/registry.yaml`, field and value-set anchor), trust (generated / stale_after), the current profile page (may be absent)

## Steps

1. **Anchor (one-time read)**: read `.owfa/protocol/registry.yaml` and `wiki/profile.md` — a missing page = first creation (construction), no reliance on an initialization mechanism
2. **Judge signals** (criteria in the user-profile usage block below): if this session's and recent observations do not qualify, report and exit — never force a write
3. Assemble the update: incremental assertions (new value replaces old + body trace) or construction / consolidation (whole-page rewrite) — construction and consolidation **present a profile preview** (assertions / evidence / layers) and wait for user confirmation
4. Write the page (layered placement and stale_after renewal per the usage block below)
5. **Post-write pipeline** (deterministic, mechanical and automatic, no prompting): execute each plugin's write calls in injection-region order, then finish with `python .owfa/scripts/pipeline.py verify` (post-write self-verification; on failure, go back and fix); then commit per the commit discipline (`画像: <one line>`, see the vocabulary in `.owfa/protocol/actions.md`)
6. Report: what was updated / the evidence chain / which layer it landed in

## Prohibitions

- Privacy red line: profile content is instance data, never entering the framework repository or test-repo
- Diary-type assets contribute only meta-signals (presence, cadence); their content never enters the profile
- Evidence pages (session pages / vault proxy pages / lark archive pages) are referenced read-only, never rewritten

## Language

Output language takes the default key of the language declaration page `wiki/language.md` (a missing page or missing key falls back to the session language); proper nouns and paths keep their original form.

## Parameters

- No argument: judge recent signals and update; `<topic>`: process only that topic's assertions

## Injected Section (plugin usage blocks)

> This region is a owfa-kernel projection: consumes pulls merged with usage_routes source-side routing; disclosure order = owner first, routed blocks in the middle, pulled blocks last (rebuilt by inject / all); handwritten content does not belong here — to change the write-side contract, edit PLUGIN.yaml.

<!-- cmd-inject:start -->
<!-- usage:user-profile -->
- Dual-track triggering: the user explicitly invokes profile; the agent calls it spontaneously in any session upon recognizing significant signals — signal distillation uniformly goes through this command, not parasitic on other command flows
- Signal criteria: self-reported signals (preference expressions, corrections, background) and behavioral signals (subjects, fields, material habits); record only recurring subjects/fields, explicit preference expressions, corrections to output, and stable background facts (identity/tools/environment); one-off and instrumental content and uncertain observations are not recorded
- Evidence domain: any page inside wiki works (session pages, vault proxy pages, lark archive pages, notes) — a citation is a wikilink, no cross-domain dependencies established
- Layered placement: immutable identity facts go to the static layer; drifting interests and habits go to the dynamic layer with stale_after (renewed as observed)
- An assertion = one line of concrete, verifiable claim + inline evidence wikilink ('prefers concise Chinese replies' beats 'likes brevity'); a single incremental assertion is not directly promoted to a preference — preferences are patterns aggregated within the page
- Convergence-style updates: when a new value replaces an old one, a trace is left in the body (single line: who changed what, when); full-page rewrites are limited to profile construction/consolidation (preview shown, awaiting confirmation)
- First creation: the first trigger self-creates the page (frontmatter: type: profile + generated, dynamic layer carries stale_after), independent of any initialization mechanism
- Diary-type assets record only meta-signals (presence, cadence); content never enters the profile (the exemption followed mapping)
- Privacy red line: profile content is instance data, never entering the framework repo or test-repo
- Cognition bridge registration (a domain-plugin-side action, disclosed on this side): when a domain cognition plugin creates its archive and the profile is present, maintain one line in the profile's `## Domain Cognition` section (domain name + path-form wikilink); if the profile is absent, skip without proxy-creating it (on-demand bridge absence tolerance); multiple courses and archives register via the path-form wildcard (bb: <term>/<course> form)
<!-- /usage:user-profile -->

<!-- usage:trust -->
- When writing a page, write `generated` along the way (block style: `by: agent/<current-model>` / `at: <today>`)
- When a review action happens, append a `verified` event (single line `by: <actor>, at: <date>`), never fabricated to inflate the level
- Reviews are initiated by the user (triggered by human instruction); agents never append verified events on their own
<!-- /usage:trust -->

<!-- usage:index -->
- Post-write rebuild (mechanical, automatic): `python .owfa/scripts/pipeline.py index` (index — overflow-offloading scheme, including deletion of obsolete old indexes after merge-back) and the same script's `tags` (tag reverse index); LLMs never hand-write indexes
<!-- /usage:index -->

<!-- usage:hot -->
- Writing entries (mechanical, automatic): `python .owfa/scripts/pipeline.py hot <type> "<wikilink + one-sentence essence>"` (type value set same as log, see the log block of the AGENTS injection region); window eviction and truncation are performed by the script
<!-- /usage:hot -->

<!-- usage:log -->
- Writing lines (mechanical, automatic): `python .owfa/scripts/pipeline.py log <type> "<one sentence>" [--domain <domain>]` (type value set in the log block of the AGENTS injection region; domain tag = domain-plugin name such as bb/lark/vault, mandatory for in-domain transactions, omitted for framework and native transactions); rolling window and archiving are performed by the script
<!-- /usage:log -->
<!-- cmd-inject:end -->
