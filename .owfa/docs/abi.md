# The Protocol ABI

> Reader: protocol package authors, bridge/connector authors, and anyone building cross-protocol retrieval over an OWFA instance. This page fixes the **calling contract** (abi-spec §2) and the **compat interval grammar** (abi-spec §4) as implemented since framework 0.4.6. The kernel enforces presence and shape (R11); it implements no retrieval — the mechanism belongs to each protocol package.

## 1. What the ABI is

The ABI is the **only legal access surface** a protocol exposes to the outside: connectors, bridges and (later) federated search never read another protocol's internal structure — they call the four semantics. Mechanism lives with the protocol package (the implementation ships inside the package); the kernel defines only the calling contract and the in-place validation. One more application of the adapter-class rule: the kernel (standard parts) presumes no structure, the retrieval implementation travels with the protocol package.

The execution channel is the **package-root script `proto_query.py`** (the `pipeline.py` precedent: package-root scripts travel with the whole package and are invoked by path, bypassing the command binding system — that surface is for agent skills, not machine calls). A `command/proto-query` skill is optional sugar, not part of the qualification line.

## 2. The four semantics

Uniform entry: `proto_query.py <semantic> [args]`. **JSON-lines output is the only contract surface**; `--pretty` output is best-effort convenience, not a contract.

| Semantic | Input | Output (normalized tuple) | Constraints |
|---|---|---|---|
| `list` | `--kind <k>` (optional filter; **parameter name normalized, vocabulary is protocol sovereignty**) | each item `{addr, title, kind, mtime}` | addr = the protocol's **native addressing**, never an invented intermediate; unknown kind → empty result, not an error (the smoke test depends on this) |
| `get` | `<addr>` | `{addr, title, kind, mtime, content}` | content = the full original text, untruncated; read-only, never writes |
| `search` | `<expr>` (protocol-native syntax) | same tuple as `list` | semantics per protocol; the protocol must state its search semantics in one sentence in its `abi:` block |
| `recent` | `--window <N><d\|m>` (positive integer + unit, default 7d; illegal value → `bad_request`) | `{addr, title, kind, mtime, op}` | op ∈ `create\|update\|unknown`, best-effort; the protocol declares its precision in its abi.md |

**What normalization does not cover**: only the envelope, the field names, and the two parameter names `--kind` / `--window` are normalized. Address syntax, search syntax and kind vocabulary are protocol sovereignty.

**Common envelope**: every output line carries `protocol` (the protocol id) + `proto_ver` (the **PKG.yaml `version`** — the single value source; the org capability's `vN` is an unrelated lease vocabulary). Batch results: `{ok, semantic, count, items}`.

**Error envelope**: a query-level failure exits **0** and prints `{ok: false, error_code, message}` with error_code ∈ `not_found / bad_request / unsupported_semantic / internal`. A nonzero exit means the command itself is dead — consumers (e.g. the bridge stale ladder) distinguish "query failed" from "command died" on exactly this split.

## 3. compat: one version vocabulary and the interval grammar

`proto_ver` is PKG.yaml `version` (X.Y.Z). Breaking-change adjudication: at major ≥ 1 a **major change is presumed breaking**; during 0.x **minor doubles as major** (0.1 → 0.2 is presumed breaking; patch never breaks). Envelope fields only grow; removing or re-semanticizing a field is a breaking change.

The interval grammar (bridge connection declarations / landing-template version anchors / registry references — this vocabulary is bridge-only; PKG `compat` floors remain `>= X.Y` single lower bounds):

```
interval   := comparator { " " comparator }        ; space = AND
comparator := op version                            ; op glued to version, no space
op         := ">=" | "<=" | ">" | "<" | "="
version    := major [ "." minor [ "." patch ] ]     ; digit segments
```

Missing-segment semantics, per op:

| op | Missing segments | Example |
|---|---|---|
| `>=` / `>` / `<=` / `<` | take the **lowest value** at that precision (1 = 1.0.0; 2.0 = 2.0.0) | `<2.0` ⇔ excludes 2.0.0 and above; `>=0.8` ⇔ includes 0.8.0 |
| `=` | **prefix match** | `=1.2` ⇔ 1.2.* |

Canonical examples: `>=1.0 <2.0`, `=1.2.3`, `>=0.8`. A landing-template version anchor may be narrower than the declared compat, never wider. Python side: `compat_match(version, interval)` in `owfa_kernel.py` is the **single parser** — bridge, template validation and registry references all call it; a second Python implementation is forbidden.

## 4. R11: the qualification line (two-state validation)

A `kind: protocol` package declares its ABI in PKG.yaml:

```yaml
abi:
  semantics: [list, get, search, recent]   # exactly these four
  search_lang: "full-name prefix + grep substring"   # one sentence, for humans
  addr_doc: docs/abi.md                    # addressing-rules pointer (optional, recommended)
```

Two-state validation since 0.4.6:

- **Block absent** → warning through the 0.4.x window (existing protocol packages and unupgraded workspaces are unaffected); becomes an **error at 0.5.0** — no grandfather clause.
- **Block present but** semantics not exactly the four / package-root `proto_query.py` missing / illegal fields → **error** (declaring is promising; a wrong promise is wrong).

The kernel's `audit` additionally runs the **ABI smoke** for every installed `kind:protocol` package that declares the block: `proto_query.py list --kind __abi_smoke`, expecting exit 0 (empty result is legal — unknown kind never errors). Unrunnable or timed out = a failed check item.

## 5. What each protocol ships

The implementing package carries everything: the package-root `proto_query.py` (self-contained — a protocol package may not assume another protocol's machinery), an `abi.md` documenting its addressing rules and its `recent` op precision, minimal self-tests, and the `abi:` block above. The framework side (this page) carries nothing but the contract and the validation.
