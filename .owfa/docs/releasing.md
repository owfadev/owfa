# Releasing

> Reader: maintainers of OWFA Core and of owfa-* packages. This page replaces the maintainer half of the old distribution.md (the install/upgrade half lives in [deployment.md](deployment.md)). Every step below is checked against the actual pipeline files — `.github/workflows/publish.yml`, `scripts/verify-release.js`, `scripts/sync-blessed.sh`, `bin/owfa.js` — not against an idealized process.

## The release invariant

A framework release is exact equality across five carriers:

```
.owfa/VERSION  ==  package.json "version"  ==  git tag vA.B.C  ==  npm owfadev@A.B.C  ==  GitHub Release vA.B.C
```

The gate is [`scripts/verify-release.js`](https://github.com/owfadev/owfa/blob/master/scripts/verify-release.js). It runs locally, on `npm publish` (prepublishOnly), and as the first CI step — and it **fails closed** on any drift:

- package version must equal `.owfa/VERSION` exactly (VERSION carries the full `A.B.C`);
- in CI (`GITHUB_REF_TYPE=tag`), the tag must equal `v${version}`;
- package name must be `owfa` or `owfadev`, with `bin.owfa` **and** `bin.<pkg.name>` both pointing at `bin/owfa.js`;
- no `preinstall`/`install`/`postinstall` scripts;
- the actual packlist (`npm pack --dry-run --json`) must contain the required payload — including `.owfa/VERSION`, the kernel, `payloads/personal/PKG.yaml`, the embedded suite masters — and must not contain dev/local state (`test/`, `scripts/`, `.github/`, `__pycache__`, `pending.json`, `kernel-journal.log`, `registry-cache.yaml`, instance `vault/`/`wiki/`, `.owfa/plugins/core/`, or the suite-owned command masters under `.owfa/command/`).

A release that would break the equation is refused before publish, not repaired after. Current line: read `.owfa/VERSION` (or `owfa version`); do not pin release numbers in docs.

## Framework release runbook

1. **Land the changes.** Everything reaches `master` through a PR (see merge discipline below). No direct pushes, no release branches that live past the merge.
2. **Sync the blessed suite** (see next section) so `payloads/personal/` carries the suite content this release should embed.
3. **Bump both carriers in one commit**: `.owfa/VERSION` and `package.json` `"version"` — same full `A.B.C`, e.g. `0.4.1` → `0.4.2`.
   ```bash
   node scripts/verify-release.js   # gate on the working tree
   node test/smoke.js               # end-to-end channel smoke (init / doctor / upgrade)
   npm pack --dry-run               # eyeball the tarball
   ```
4. **Tag `vX.Y.Z` — after verifying what the tag points at.** This is written into discipline the hard way: a tag pushed onto the wrong commit fires the whole pipeline against that wrong content, and npm versions are immutable. Before `git tag`:
   - `git log --oneline -5` — the bump commit is the tip, nothing landed after it;
   - `git show <commit>:package.json | grep version` and `git show <commit>:.owfa/VERSION` — the commit you are about to tag actually carries the new versions;
   - `git status` — clean tree, so the tag names committed content, not the working directory.
   The lesson behind the rule: in this project's own session history a tag was cut without checking the target commit's contents, and the mismatch was only caught downstream. Check first; the tag is the trigger, not a draft.
   ```bash
   git tag v0.4.2
   git push origin v0.4.2
   ```
5. **The tag drives the pipeline** — [`publish.yml`](https://github.com/owfadev/owfa/blob/master/.github/workflows/publish.yml) triggers on `push: tags: v*` and runs, in order:
   1. `node scripts/verify-release.js` — release gate (re-checks version/tag/packlist in CI);
   2. `node test/smoke.js` — channel smoke: init / doctor / upgrade against the tarball;
   3. `npm publish --provenance --access public` — publishes **owfadev** (requires the `NPM_TOKEN` repository secret; `id-token: write` gives npm provenance);
   4. GitHub Release creation (`softprops/action-gh-release@v2`, `generate_release_notes: true`, body linking `owfadev@<tag>`).

   The GitHub Release is created by the same run, so the Release set can never drift from the npm version set. The notes are a placeholder — curated notes belong in the tag/commit message.

A manual `npm publish --provenance` is the documented fallback only when CI itself is broken; the gate still runs via `prepublishOnly`.

## Suite sync (payloads/personal/)

The default `owfa init` is a two-stage bootstrap: kernel tree, then the personal suite installed **offline** from the embedded copy — `kernel install personal --path payloads/personal` (`bin/owfa.js` cmdInit). That embedded copy is refreshed by [`scripts/sync-blessed.sh`](https://github.com/owfadev/owfa/blob/master/scripts/sync-blessed.sh):

- source: `owfadev/owfa-personal`, latest tag matching `personal-v[0-9]*` (version-sorted, first hit);
- downloads that tag's tarball, refuses it if the repo root has no `PKG.yaml`;
- `rm -rf payloads/personal/` and replaces it wholesale; `README.md` is channel-owned — the suite's copy is dropped and a channel README re-created;
- prints the tag and the plugin-master count.

Run it before step 2 of the framework runbook. The embedded copy rides the framework version: a suite release reaches users either through the next framework release's tarball or via `kernel upgrade personal` — the suite repo tagging alone does not change what `owfa init` installs. Note the gate consequence: verify-release refuses to publish **without** `payloads/personal/PKG.yaml`, so "forgot to sync" fails the release rather than shipping an unbootstrappable tarball.

## Package release runbook (each owfa-* package)

For suite/domain packages (owfa-personal, owfa-cuhksz, owfa-lark, …) the flow is deliberately **two small steps, separately**:

1. **In the package repo**: bump `PKG.yaml` `version` (A.B.C), tag `<pkg>-vA.B.C` (e.g. `personal-v0.1.1`), push. The tag pattern is what `sync-blessed.sh` and the registry tooling key on.
2. **In `owfadev/owfa-registry`**: open a PR updating the package's `INDEX.yaml` line (repo / version / compat / trust / members / summary, needs/provides, commit SHA pin).

Why separated: the registry does not freeze with the framework. A package tag is a fact about one repository at one commit; the registry line is a human-reviewed promotion of that fact (one line, one package, easy review). Neither step triggers publish.yml — that workflow is the framework's npm channel only. Tying them together would force registry edits into framework release commits and make a bad INDEX line block or ride a framework release.

## Merge and branch-protection discipline

- All changes — code, docs, release bumps — go through PRs: **1 approving review** to merge, `enforce_admins` on. Maintainers are not exempt from their own gate; that is the point of the setting.
- `gh pr merge --admin` is therefore blocked by design. When it genuinely must happen (time-critical fix, no second reviewer awake), the standard sequence is:
  1. temporarily lift the protection via the API — `gh api -X PUT repos/owfadev/owfa/branches/master/protection -f ...` with `enforce_admins=false` restored settings — or edit exactly that one switch in the repo settings;
  2. merge;
  3. **restore the exact prior protection state immediately**, and say so in the PR/commit trail.
  The exception is the pause, not the new normal; a protection left off overnight is an incident.
- Release bump PRs follow the same rule as any PR — the runbook's "one commit" is about the two version files moving together, not about skipping review.

## npm naming, one paragraph

`owfa` is frozen by npm's name-similarity policy (too close to `ow`/`ora`), so `npx owfa` does not exist and every install example must say `npx owfadev`. **`owfadev` is the real package name** (the gate accepts `owfa` only for the future where the freeze lifts); one package, two bins — `owfa` and `owfadev` — both required by verify-release. See [naming.md](naming.md).
