# Developer guide: writing plugins & packages

> Where a plugin lives is decided by its `depends`, not by taste — and the dev loop is the same wherever it lives: clone → branch → hack → `--path` install into a sandbox → PR.

## Where does my plugin land?

| Your plugin is… | It lands… | Trust gate |
|---|---|---|
| a **domain member** (depends chain reaches a domain root, e.g. bb-family) | that domain package's repo — PR there. Not a choice: the family closure claims it mechanically (`PKG.members` must include you or validate errors) | package maintainers |
| a **new domain** of its own | your own repo as a package (`PKG.yaml`, see [packages.md](packages.md)) + a one-line PR to the [registry](https://github.com/owfadev/registry) | the registry PR — the human-review gate (inject text and connectors are the security faces, #12) |
| **cross-cutting / non-domain** (global piece) | the framework repo's `core/` — PR there | owner review (charter-level, highest bar) |

A single plugin never ships bare — the package is the distribution unit. A lone plugin is a single-member package (12 lines of PKG.yaml, see email/bili/project). Users prune with `--without` (subset grammar), so contributing into a big package never forces users to install all of it.

## The dev loop

1. **Clone the target repo** (package repo for domain work, framework for core) and branch: `module/topic`
2. **Hack** — manifest (PLUGIN.yaml) + PLUGIN.md + skills per the existing patterns; versions advance along the changelog
3. **Integration-test without a monorepo**: in the sandbox (or any instance),
   ```
   cd test-repo
   python .owfa/scripts/owfa_kernel.py install <pkg> --path /path/to/your/clone
   python .owfa/scripts/owfa_kernel.py validate --scope <pkg>
   ```
   `--path` installs the local clone (channel C); iterate freely — reinstall after uninstalling, or just re-copy
4. **PR** — one thing per commit, `模块: 概述`; self-check per [CONTRIBUTING](../../CONTRIBUTING.md) (framework root: `validate`; sandbox: `all`)
5. **Release** (package repos): bump PKG.yaml `version`, tag `<pkg>-v<X.Y>`, then bump the registry line — two small PRs, on purpose: the registry never freezes with the framework

## Discovery: how people (and agents) find your work

- **Before registration**: your repo is already installable (`kernel install <owner>/<repo> --yes`, trust: unknown) and findable via GitHub topics — tag the repo `owfa-package`
- **After the registry PR**: listed in `kernel list-remote` (the agent surface), installable without `--yes`, trust: reviewed-3rd-party
- **Write the summary for agents** — the registry `summary` line and your SKILL.md `description` fields are what agents actually match against; a vague summary is undiscoverable
