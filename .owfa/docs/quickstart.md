# Quickstart

Reader: a first-time user who wants a working OWFA workspace in about five minutes.

## Prerequisites

- **Node 16.7+** — the installer CLI is Node (`npx owfadev`).
- **Python 3.9+** — the kernel is pure standard library; no pip, no venv.
- **An agent** that reads `AGENTS.md` and `.agents/skills/` (Claude Code, Cursor, dsh, Zcode…).

## The five-minute path

```bash
npx owfadev init my-workspace
cd my-workspace
```

The npm package is **`owfadev`** (the name `owfa` is frozen by npm's similarity policy, so `npx owfa` does not work — always use `npx owfadev`).

`init` is two-stage: stage ① bootstraps the kernel (the `.owfa/` tree plus an `AGENTS.md` seed — additive, existing content untouched), stage ② installs the embedded personal suite offline (`kernel install personal --path payloads/personal`), whose `skeleton:` declaration creates the workspace directories (`vault/`, `wiki/notes/`, `wiki/sessions/`, `wiki/vault/`).

**Stage ② is a protocol choice, not a silent default.** The embedded personal suite carries the
`vaultwiki` protocol — the personal-information protocol, the recommended shape for personal
knowledge workspaces (its design descends from llm-wiki, so an existing workflow ports over at
near-zero cost). It is what `init` picks for you when you say nothing; say otherwise with
`--core none` (a bare kernel workspace) and then install the protocol you actually want from the
registry before any plugin — e.g. the `project` protocol for development workspaces, with the
optional `owfadevelop` package on top for developing owfa itself (see [packages.md](packages.md)).

Now open an agent session at the workspace root, drop any file into `vault/`, and say **"owfa-map"** — the agent registers the asset as a wiki proxy page (SHA-256, mirror path, index/hot/log linkage). First run also builds the derived pages. Follow up with "owfa-check" to audit the instance's health.

That's it — the workspace is live. Daily usage is covered by the default protocol's [usage guide](https://github.com/owfadev/owfa-personal/blob/master/docs/usage.md).

## Manual deployment

Prefer the manual path (git clone, offline, or embedding into an existing vault)? One sentence: copy the framework trees, install the suite, write the `AGENTS.md` shell, converge — step by step in [deployment.md](deployment.md).
