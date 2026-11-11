---
name: asset-read
owner: framework
description: "Extract text from assets of any format by path (md read directly / pdf via PyMuPDF / docx and xlsx unpacked with the standard library); outputs are cached in wiki/tmp and marked with stale_after — the unified channel and caching convention for source-origin reads. Triggers on: asset-read, 读资产, 回源, 提取文本, 读课件原文, read asset."
---

# asset-read: source-origin asset reading

Read the text of assets of any format by path — the unified channel for source-origin reads: vault assets, bb/ fetched artifacts, and relative paths outside the repository are all eligible. Reading augments registration rather than replacing it: the proxy page's one-line description covers the overview; only a deep question goes back to the source.

## Scope

Read: assets of any format (file system outside wiki, read-only)
Write: `wiki/tmp/` extraction cache (the only landing spot)

## Steps

1. Locate the asset path and extension; md / txt / csv are read directly and done — no cache is written
2. Check the cache: if `wiki/tmp/<asset name>.txt` is present and not past stale_after → read the cache directly, do not re-extract
3. On a miss, extract:
   - pdf: PyMuPDF (`import fitz`; if missing, install it per the host's Python package manager — e.g. pip on dev desktops, uv on PEP 668 hosts; instance-level environment declarations in AGENTS.md take precedence); for large files, extract by page range or keyword location — never feed the whole book into context
   - docx / xlsx: pure standard-library zipfile + xml text-node extraction
   - other binaries: no deep read; report honestly "text extraction not supported"
4. Write the output to `wiki/tmp/<asset name>.txt`, with a three-line comment header: source path / extraction date / stale_after = extraction date + 7 days
5. Report key points with provenance (page number or section name)

## Prohibitions

- Never modify asset originals (the read-only discipline holds in whatever domain they live)
- No bulk full extraction — single items on demand; one-off views are not cached
- Cache expiry is reported as a list by check, and disposal requires confirmation (an existing rule of the tmp plugin; this command does not clean up on its own)

## Language

Output language takes the default key of the language declaration page `wiki/language.md` (a missing page or missing key falls back to the session language); asset originals keep their original language and form.

## Parameters

- Asset path (root-relative); optional page range or locating keyword
