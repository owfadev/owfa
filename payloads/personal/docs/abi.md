# vaultwiki Protocol ABI — Addressing, Vocabulary, Precision

> Contract face: `proto_query.py` (package root, pipeline.py precedent). Envelope and
> semantics are defined by the framework ABI spec (abi-spec v2 §2); this page holds the
> protocol-sovereign parts: addressing rules, kind vocabulary, recent op precision, and
> the error envelope at a glance.

## Addressing (addr)

`addr` = the **wiki full name**: the page's path under `wiki/` minus the trailing `.md`
(same grammar as the `[[...]]` link syntax — see the link plugin). Examples:
`notes/idea`, `vault/a.pdf` (md proxy of a vault asset), `sessions/2026-11-15-topic`.
Addresses are case-sensitive and never invented outside this rule — no intermediate
addressing layer exists.

`wiki/tmp/` is **not on the ABI face** (tmp plugin invisible-to-derived-layer semantics):
drafts are neither listed, searched, nor recent-tracked, and `get` on a `wiki/tmp/` addr
answers `not_found`. `get` also never lies about existence: a page that exists but cannot
be decoded as UTF-8 (skipped by the listing walk) is still returned — read-only, decoded
with replacement characters.

## Kind vocabulary

`kind` = the page's frontmatter `type` field (open vocabulary — see the notes plugin for
the native-notes defaults; domain plugins bring their own types). Pages without a `type`
report the empty string. `list --kind K` filters on exact equality; an unknown kind
returns an **empty result, not an error** (ABI smoke relies on this).

## Search semantics

`search <expr>`: full-name **prefix** match (`notes/` matches every page under
`wiki/notes/`) OR **substring** match in the page body (frontmatter excluded). The
match is **case-sensitive**. Plain substring only — no regex, no operators.

## recent: op precision (best-effort declaration)

Window = `--window <N>d|m` (default 7d; a month counts as 30 days — a scan window, not a
calendar promise). Inclusion is by **mtime falling inside the window**. `op`:

- `create` — only when a dated line in `wiki/log.md` or `wiki/hot.md` inside the window
  names the page (full name or last segment) with a create verb (create/created/新建/建立/创设).
- `update` — a log/hot mention dated **before** the window proves the page already
  existed, so the in-window touch is an update.
- `unknown` — no evidence either way (the common case; mtime alone cannot tell).

Known mtime disturbance sources: `git checkout` / branch switches and whole-tree copies
rewrite mtimes in bulk — such windows will show spurious `update`/`unknown` entries.
Creation is never guessed from a young mtime (no lied `create`).

## Error envelope

Query-level failures exit **0** with `{"ok": false, "error_code": ..., "message": ...}`;
only a process crash exits non-zero.

| error_code | when |
|---|---|
| `not_found` | `get` on an addr with no page, or on one under `wiki/tmp/` |
| `bad_request` | missing/invalid arguments (invalid `--window`, missing `<addr>`/`<expr>`) |
| `unsupported_semantic` | first argument is not one of list/get/search/recent |
| `internal` | the package cannot serve the query (e.g. PKG.yaml unreadable) |

`proto_ver` in every item is read live from this package's `PKG.yaml` `version`.
