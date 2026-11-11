#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""owfa plugin lifecycle mechanical kernel ((un)install / compliance / dependencies / injection / registry / copy sync).

Positioning (see .owfa/protocol/actions.md execution principles): deterministic structural
operations go to this script; semantic judgment goes to the LLM. The script touches only
four places: plugin directories in and out, AGENTS.md injection-region marker blocks,
the registry.yaml plugin section, and .agents/skills/ command copies; the protocol /
reserved sections and handwritten regions are never touched.

Usage:
  python .owfa/scripts/owfa_kernel.py ls          # list + dependencies
  python .owfa/scripts/owfa_kernel.py validate    # compliance and dependency check (read-only, exit code 1 on errors)
  python .owfa/scripts/owfa_kernel.py audit       # plugin attached audits (discovery-style execution of each plugin's scripts/check.py)
  python .owfa/scripts/owfa_kernel.py inject      # rebuild AGENTS.md injection region, check inspection blocks and command usage blocks (idempotent)
  python .owfa/scripts/owfa_kernel.py registry    # rebuild the registry.yaml plugin section (idempotent)
  python .owfa/scripts/owfa_kernel.py deploy      # sync command and connector skill deployment copies (idempotent)
  python .owfa/scripts/owfa_kernel.py all         # validate + inject + registry + deploy
  python .owfa/scripts/owfa_kernel.py plan <pkg>  # dependency plan for a package about to land
  python .owfa/scripts/owfa_kernel.py install <pkg> [--yes] [--without ...]  # fetch from registry/path -> domains/<pkg>/ (owner/repo needs --yes)
  python .owfa/scripts/owfa_kernel.py uninstall <pkg> [--yes]  # remove package + projections; stages teardown (x->0) when declared
  python .owfa/scripts/owfa_kernel.py list-remote # registry catalog (INDEX.yaml): packages, versions, compat floors
  python .owfa/scripts/owfa_kernel.py migrate [<pkg>] [--clear] [--force]  # pending semantic migrations: status / clear (verify- and residual-gated)
  python .owfa/scripts/owfa_kernel.py upgrade [<pkg>]  # compare versions against the registry; apply updates
  python .owfa/scripts/owfa_kernel.py pkg         # installed packages: members, versions, connectors
  python .owfa/scripts/owfa_kernel.py residual <pkg>  # anchor-surface reference scan (the default teardown gate)

The manifest is a minimal YAML subset: top-level `key: value`, `key: []`, block lists
(`  - item`), one-level field dicts (`  name: description`); double-quoted values are
unquoted; inline comments (starting with ` #`) are stripped.

Dependencies and injection order:
- depends declares behavioral or semantic dependencies (a bridging piece depending on the
  concept plugins at both ends is a semantic dependency); validate checks existence and acyclicity
- injection order = dependency topology (dependees injected first) + alphabetical within
  the same batch; no layering concept

Injection tier and budget (issue #12 layer discipline, see protocol/experiments.md):
- optional manifest field inject_tier (full|member, default full) — member exits the AGENTS.md
  injection region; exposure rides on the family root's roster line, the skill catalog, and
  L-layer reads (the manifest inject field stays the full-disclosure home either way)
- validate requires a member to reach a full-tier domain root through depends (family
  membership, else it exits into invisibility)
- the projected plugin blocks carry a byte budget (INJECT_BUDGET): over-budget is a validate
  error (compress pointer lines or re-tier domain members) the region under budget
- each full-tier inject line carries a pointer-density guideline (INJECT_LINE_GUIDE, issue #49):
  a line over it is a validate warning — the line is a routing pointer (path + read/write trigger
  + the one easy-to-break invariant + pointer to PLUGIN.md), detail lives in PLUGIN.md / skills

Command-plugin binding (mutual declaration, validate checks consistency):
- command frontmatter adds owner: plugin id (multiple as an [a, b] list) or framework
  (cross-cutting, explicitly ownerless)
- plugin manifest adds the optional field commands: list of command names this plugin drives
- error cases: command missing owner, owner pointing at an uninstalled plugin, framework
  combined with other owners, plugin declaring a nonexistent command, one-sided declaration
  on either side (owner not claimed by commands, or the reverse)

Command injection (the third projection: plugin write-side contract -> command):
- command frontmatter adds optional consumes: list of plugin ids whose write-side contract
  it consumes (pull side, destination declaration); owner-driven commands must fill it in
  and include all owners
- manifest adds optional usage_routes: list of extra command names this plugin's usage
  lands on (source-side routing) — presence-as-registration on the push side: installing
  the plugin lands the projection, no need to edit hub commands; validate checks routing
  targets exist, routing plugins carry usage, and routing duplicating consumes is an error
- the manifest's usage / checks lists are the sole projection source of write-side contracts
  and inspection rules: checks project into the check command in injection order, usage
  projects into each command SKILL.md's cmd-inject marker block — disclosure order: owner
  blocks first (consumes order), routed blocks in the middle (dependency topology plus
  alphabetical), remaining consumes last; to change a contract, change PLUGIN.yaml —
  command bodies keep only the operational flow.
  PLUGIN.md returns to pure documentation (Role / Structure / Invariants / Changelog)

Global pieces and domain pieces (constitution principle 11):
- the optional manifest bridge key (必依|按需): the extension point and attach cardinality
  declared by a global piece; disclosure prose lands in PLUGIN.md's bridge section
- a domain piece = depends chain reaches domain; depending on domain directly makes a domain base
- validate checks: bridges may only be held by global pieces; a must-attach (必依) bridge
  requires every domain base to have the corresponding depends edge (missing edge is an error)

Plugin attached-audit contract (scripts/check.py, optional):
- must define check(ctx), returning an issue list: {"level": "error"|"warning"|"info", "message": str}
- ctx.root = repository root; ctx.pages = [(wiki-relative path, frontmatter dict, body)],
  shared across the single scan
- read-only with zero side effects: repair actions belong to commands/humans, attached
  audits only report; messages in Chinese, no third-party dependencies
"""
import ast
import importlib.util
import os
import re
import shutil
import sys
import types

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PLUGINS_DIR = os.path.join(ROOT, ".owfa", "plugins")
COMMANDS_DIR = os.path.join(ROOT, ".owfa", "command")
CONNECTORS_DIR = os.path.join(ROOT, "connectors")
SKILLS_DIR = os.path.join(ROOT, ".agents", "skills")
AGENTS_MD = os.path.join(ROOT, "AGENTS.md")
REGISTRY = os.path.join(ROOT, ".owfa", "protocol", "registry.yaml")
MIGRATIONS_DIR = os.path.join(ROOT, ".owfa", "migrations")   # kernel zone: staged migration declarations (use-and-delete)
LEDGER = os.path.join(MIGRATIONS_DIR, "pending.json")          # kernel-owned warning ledger (never a plugin surface)
JOURNAL = os.path.join(ROOT, ".owfa", "kernel-journal.log")    # mechanical event journal, one line per op

# manifest's seven fields (id / version / depends / updated / attachment / fields / inject) + optional commands
REQUIRED_KEYS = ["id", "version", "depends", "updated", "attachment", "fields", "inject"]
INJECT_START = "<!-- wiki-inject:start -->"
INJECT_END = "<!-- wiki-inject:end -->"
CHECK_SKILL = os.path.join(COMMANDS_DIR, "check", "SKILL.md")
CHECK_INJECT_START = "<!-- check-inject:start -->"
CHECK_INJECT_END = "<!-- check-inject:end -->"
CMD_INJECT_START = "<!-- cmd-inject:start -->"
CMD_INJECT_END = "<!-- cmd-inject:end -->"
# tier law (issue #12 layer discipline): full projects into AGENTS.md, member exits the injection
# region — exposure rides on the family root's roster line, the skill catalog, and L-layer reads
INJECT_TIERS = ("full", "member")
# injection budget on the projected plugin blocks: smallest mainstream whole-file AGENTS.md cap
# (Devin 16 KiB) minus ~1 KiB instance handwritten allowance; over-budget is a validate error
INJECT_BUDGET = 16 * 1024  # #12 layer discipline: raised 15->16 KiB at the conversion drill — five packages + core 21 project 15.7K; the 16K line stays the anchor (Devin floor)
# per-line pointer-density guideline for full-tier inject lines (issue #49): the budget is the pressure
# valve, this is the gauge — over-guideline lines warn, never block (third-party packages migrate at their pace)
INJECT_LINE_GUIDE = 256


def ordered_plugins(plugins):
    """Injection order = dependency topology (dependees injected first) + alphabetical within a batch; shared by projection regions.

    On cycles or dangling dependencies, falls back to alphabetical output (validate
    reports the error separately; not duplicated here).
    """
    remaining = dict(plugins)
    order = []
    while remaining:
        ready = sorted(p for p, m in remaining.items()
                       if all(d not in remaining for d in (m.get("depends") or [])))
        if not ready:
            order.extend(sorted(remaining))
            break
        order.extend(ready)
        for p in ready:
            del remaining[p]
    return order


def strip_quotes(s):
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    return s


def strip_comment(s):
    """Strip inline comments (from ` #` on) — a quoted value is protected up to its closing quote.

    The manifest contract says "quote the whole value first if it contains #"; this honors it:
    comment stripping never fires inside the quoted span (e.g. `## Section` names in disclosures).
    """
    if s.startswith('"'):
        end = s.find('"', 1)
        if end != -1:
            return s[:end + 1] + strip_comment(s[end + 1:])
    return re.split(r"\s+#", s, maxsplit=1)[0].strip()


def parse_manifest(path):
    """Parse the manifest's minimal YAML subset; raises ValueError on failure."""
    data, target = {}, None
    for raw in open(path, encoding="utf-8").read().splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith("  - "):
            if target is None:
                raise ValueError(f"list item before any key: {raw!r}")
            item = strip_quotes(strip_comment(raw.strip()[2:]))
            if not isinstance(data.get(target), list):
                data[target] = []
            data[target].append(item)
            continue
        m = re.match(r"^(\s*)([A-Za-z_][\w-]*):\s*(.*)$", raw)
        if not m:
            raise ValueError(f"unparsable line: {raw!r}")
        key, val = m.group(2), strip_comment(m.group(3))
        if m.group(1):  # indented line: fields dict item
            if target is None:
                raise ValueError(f"field item before any key: {raw!r}")
            if not isinstance(data.get(target), dict):
                data[target] = {}
            data[target][key] = strip_quotes(val)
        else:
            target = key
            if val == "":
                data[key] = None  # block style, filled by following lines
            elif val == "[]":
                data[key] = []
            elif val == "{}":
                data[key] = {}
            else:
                data[key] = strip_quotes(val)
    return data


def _plugin_dirs(base):
    """Yield (plugin_id, dir) across layouts: flat <p>/, core/<p>/, domains/<pkg>/<p>/."""
    for name in sorted(os.listdir(base)):
        pdir = os.path.join(base, name)
        if not os.path.isdir(pdir):
            continue
        if os.path.exists(os.path.join(pdir, "PLUGIN.yaml")):
            yield name, pdir
            continue
        for sub in sorted(os.listdir(pdir)):  # core/<p> or domains/<pkg>
            sdir = os.path.join(pdir, sub)
            if not os.path.isdir(sdir):
                continue
            if os.path.exists(os.path.join(sdir, "PLUGIN.yaml")):
                yield sub, sdir
                continue
            for sub2 in sorted(os.listdir(sdir)):  # domains/<pkg>/<p>
                s2dir = os.path.join(sdir, sub2)
                if os.path.isdir(s2dir) and os.path.exists(os.path.join(s2dir, "PLUGIN.yaml")):
                    yield sub2, s2dir


def load_plugins(base=None):
    """Read all plugin manifests (flat / core/ / domains/<pkg>/ layouts); returns (plugins, errors)."""
    plugins, errors = {}, []
    for name, pdir in _plugin_dirs(PLUGINS_DIR if base is None else base):
        yml = os.path.join(pdir, "PLUGIN.yaml")
        md = os.path.join(pdir, "PLUGIN.md")
        if not os.path.exists(md):
            errors.append(f"[error] {name}/: PLUGIN.yaml or PLUGIN.md missing")
            continue
        if name in plugins:
            errors.append(f"[error] {name}/: duplicate plugin id (two layouts declare it)")
            continue
        try:
            m = parse_manifest(yml)
        except ValueError as e:
            errors.append(f"[error] {name}/PLUGIN.yaml: {e}")
            continue
        m["_dir"] = pdir  # private: layout-aware path anchor (attached-audit contract etc.)
        plugins[name] = m
    return plugins, errors


def reaches_domain(plugins, pid, seen=None):
    """Does the depends chain of pid reach the domain concept plugin (domain-piece test, principle 11)?"""
    seen = set() if seen is None else seen
    if pid in seen or pid not in plugins:
        return False
    seen.add(pid)
    deps = plugins[pid].get("depends") or []
    return "domain" in deps or any(reaches_domain(plugins, d, seen) for d in deps)


def reaches_plugin(plugins, start, target, seen=None):
    """Does the depends chain of start reach target (transitive family-membership test)?"""
    seen = set() if seen is None else seen
    if start in seen or start not in plugins:
        return False
    seen.add(start)
    deps = plugins[start].get("depends") or []
    return target in deps or any(reaches_plugin(plugins, d, target, seen) for d in deps)


def build_inject_blocks(plugins):
    """AGENTS.md injection-region plugin blocks with member-tier exits applied; returns (blocks, exited)."""
    blocks, exited = [], 0
    for pid in ordered_plugins(plugins):
        if plugins[pid].get("inject_tier") == "member":
            exited += 1
            continue
        ver = plugins[pid].get("version")
        line = plugins[pid].get("inject", "")
        blocks.append(f"<!-- plugin:{pid} v{ver} -->\n- {line}\n<!-- /plugin:{pid} -->")
    return blocks, exited


def validate(plugins, errors, scope=None, warnings=None):
    """Compliance and dependency checks; errors are appended to errors (scope set → single-package tolerant mode, #20 D3)."""
    warnings = [] if warnings is None else warnings
    for name, m in sorted(plugins.items()):
        for k in REQUIRED_KEYS:
            if k not in m:
                errors.append(f"[error] {name}/PLUGIN.yaml: missing field {k}")
        if m.get("id") and m["id"] != name:
            errors.append(f"[error] {name}/: id ({m['id']}) != directory name")
        if m.get("version") and not re.fullmatch(r"\d+\.\d+", str(m["version"])):
            errors.append(f"[error] {name}/: version ({m['version']}) not X.Y")
        if m.get("updated") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(m["updated"])):
            errors.append(f"[error] {name}/: updated ({m['updated']}) not YYYY-MM-DD")
        deps = m.get("depends")
        if deps is not None and not isinstance(deps, list):
            errors.append(f"[error] {name}/: depends must be a list")
        if not m.get("inject"):
            errors.append(f"[error] {name}/: inject (projection line) empty")
        if m.get("inject_tier") is not None and m["inject_tier"] not in INJECT_TIERS:
            errors.append(f"[error] {name}/: inject_tier ({m['inject_tier']}) must be full or member")
        # stray-quote smell (post-parse): a value still carrying a quote edge means unbalanced
        # quoting — the classic artifact of a clipped value (issue #12 post-migration field report)
        if isinstance(m.get("inject"), str) and (m["inject"].startswith('"') or m["inject"].endswith('"')):
            print(f"[warning] {name}/: inject value carries a stray quote (unbalanced quoting — parse artifact or manifest typo)")
        # attached-audit contract (optional): if scripts/check.py exists it must define check(ctx) — checked statically via AST, not executed
        cpath = os.path.join(m.get("_dir", os.path.join(PLUGINS_DIR, name)), "scripts", "check.py")
        if os.path.exists(cpath):
            try:
                tree = ast.parse(open(cpath, encoding="utf-8").read())
            except SyntaxError as e:
                errors.append(f"[error] {name}/scripts/check.py syntax error: {e}")
            else:
                if not any(isinstance(n, ast.FunctionDef) and n.name == "check" for n in tree.body):
                    errors.append(f"[error] {name}/scripts/check.py: check(ctx) not defined (audit contract)")
    # tier law (issue #12): member-tier exits are legitimate only inside a family — the depends
    # chain must reach a full-tier domain root, else the plugin exits into invisibility
    roots = [p for p in sorted(plugins)
             if reaches_domain(plugins, p) and plugins[p].get("inject_tier") != "member"]
    for name, m in sorted(plugins.items()):
        if m.get("inject_tier") == "member" and not any(reaches_plugin(plugins, name, r) for r in roots):
            msg = f"{name}/: inject_tier member must reach a full-tier domain root through depends"
            if scope:
                warnings.append(f"{msg} — family root may live outside package {scope} (single-package mode)")
            else:
                errors.append(f"[error] {msg}")
    # injection budget (hard since the issue #12 tier migration landed): over-budget blocks mechanical actions
    blocks, _ = build_inject_blocks(plugins)
    size = sum(len(b.encode("utf-8")) for b in blocks)
    if size > INJECT_BUDGET:
        errors.append(f"[error] projected injection region {size} B over the {INJECT_BUDGET} B budget — compress pointer lines or re-tier domain members (issue #12 layer discipline)")
    for name, m in sorted(plugins.items()):
        n = len(str(m.get("inject") or "").encode("utf-8"))
        if m.get("inject_tier") != "member" and n > INJECT_LINE_GUIDE:
            warnings.append(f"{name}/: inject line {n} B over the {INJECT_LINE_GUIDE} B pointer guideline — keep path + read/write trigger + pointer to PLUGIN.md, move detail there (issue #49)")
    # dependency existence
    for name, m in sorted(plugins.items()):
        for dep in m.get("depends") or []:
            if dep not in plugins:
                if scope:
                    warnings.append(f"{name}/: dependency {dep} absent outside package {scope} (tolerated in single-package mode)")
                else:
                    errors.append(f"[error] {name}/: dependency {dep} not found")
    # cycle detection (DFS three-color marking)
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {k: WHITE for k in plugins}

    def dfs(node, path):
        color[node] = GRAY
        for dep in plugins[node].get("depends") or []:
            if dep not in plugins:
                continue
            if color[dep] == GRAY:
                errors.append(f"[error] dependency cycle: {' -> '.join(path + [node, dep])}")
            elif color[dep] == WHITE:
                dfs(dep, path + [node])
        color[node] = BLACK

    for k in sorted(plugins):
        if color[k] == WHITE:
            dfs(k, [])


def _owner_list(owner):
    """Normalize the owner value into an id list: lists as-is, strings split on commas (tolerating the [a, b] form)."""
    if isinstance(owner, list):
        vals = [str(v).strip() for v in owner]
    else:
        vals = [v.strip() for v in str(owner).replace("[", "").replace("]", "").split(",")]
    return [v for v in vals if v]


def validate_bindings(plugins, errors):
    """Command-plugin binding: owner × commands mutual consistency; consumes pull and usage_routes source-side routing."""
    import wikilib

    commands, claimed, consumes_map = [], {}, {}  # claimed: command -> owner set (framework excluded)
    for name in sorted(os.listdir(COMMANDS_DIR)):
        cdir = os.path.join(COMMANDS_DIR, name)
        path = os.path.join(cdir, "SKILL.md")
        if not os.path.isdir(cdir) or not os.path.exists(path):
            continue
        commands.append(name)
        fm = wikilib.parse_frontmatter(open(path, encoding="utf-8").read())
        if fm.get("owner") is None:
            errors.append(f"[error] command {name}/: frontmatter missing owner (plugin id or framework)")
            continue
        owners = _owner_list(fm["owner"])
        # consumes (optional; required for owner-driven commands and must include all owners): write-side contract pull declaration
        consumes = fm.get("consumes")
        consumes = _owner_list(consumes) if consumes else []
        consumes_map[name] = consumes
        if "framework" not in owners and not consumes:
            errors.append(f"[error] command {name}/: owner-driven command requires consumes (owner usage projects too)")
        for pid in consumes:
            if pid not in plugins:
                errors.append(f"[error] command {name}/: consumes {pid} is not an installed plugin")
                continue
            if not (plugins[pid].get("usage") or []):
                errors.append(f"[error] command {name}/: consumes {pid} but its manifest lacks a usage list")
        if "framework" not in owners:
            for pid in owners:
                if pid not in consumes:
                    errors.append(f"[error] command {name}/: owner {pid} not in consumes (owner usage projects too)")
        if "framework" in owners:
            if len(owners) > 1:
                errors.append(f"[error] command {name}/: framework cannot combine with other owners ({', '.join(owners)})")
            continue
        claimed[name] = set(owners)
        for pid in owners:
            if pid not in plugins:
                errors.append(f"[error] command {name}/: owner {pid} is not an installed plugin")
    for pid, m in sorted(plugins.items()):
        cmds = m.get("commands")
        if cmds is None:
            continue
        if not isinstance(cmds, list):
            errors.append(f"[error] {pid}/: commands must be a list")
            continue
        for c in cmds:
            if c not in commands:
                errors.append(f"[error] {pid}/: commands declares missing command {c} (.owfa/command/{c}/)")
            elif c not in claimed:
                errors.append(f"[error] command {c}/: {pid} one-sided claim (owner is framework or missing)")
            elif pid not in claimed[c]:
                errors.append(f"[error] command {c}/: {pid} one-sided claim (owner does not include {pid})")
    for c, owners in sorted(claimed.items()):
        for pid in owners:
            if pid in plugins and c not in (plugins[pid].get("commands") or []):
                errors.append(f"[error] command {c}/: owner {pid} not claimed in manifest commands (one-sided)")
    # source-side routing (usage_routes): installing a plugin lands the projection, no destination-command edit needed
    for pid, m in sorted(plugins.items()):
        routes = m.get("usage_routes")
        if routes is None:
            continue
        if not isinstance(routes, list):
            errors.append(f"[error] {pid}/: usage_routes must be a list")
            continue
        if not (m.get("usage") or []):
            errors.append(f"[error] {pid}/: usage_routes declared but manifest lacks a usage list")
        for c in routes:
            if c not in commands:
                errors.append(f"[error] {pid}/: usage_routes target command {c} not found (.owfa/command/{c}/)")
            elif pid in consumes_map.get(c, []):
                errors.append(f"[error] command {c}/: {pid} both routed and in consumes (duplicate routing)")


def validate_bridges(plugins, errors):
    """Global/domain piece bridge law (constitution principle 11): bridges are global-piece extension points; must-attach bridges check domain-base dependency completeness."""
    bases = [p for p, m in sorted(plugins.items()) if "domain" in (m.get("depends") or [])]
    for pid, m in sorted(plugins.items()):
        bridge = m.get("bridge")
        if bridge is None:
            continue
        if bridge not in ("必依", "按需"):
            errors.append(f"[error] {pid}/: bridge ({bridge}) must be 必依 (required) or 按需 (on-demand)")
            continue
        if reaches_domain(plugins, pid):
            errors.append(f"[error] {pid}/: bridge is global-only (depends chain reaches domain)")
            continue
        if bridge == "必依":
            for base in bases:
                if pid not in (plugins[base].get("depends") or []):
                    errors.append(f"[error] {base}/: missing depends {pid} (必依 bridge: every domain base must carry this edge)")


def do_audit(plugins, only=None):
    """Plugin attached audits: discovery-style execution of each plugin's scripts/check.py (contract in the module docstring).

    This is the mechanical shape of "code injection": a contract-compliant attached-audit
    script present in a plugin directory is automatically listed, and moving the directory
    out on uninstall automatically delists it — isomorphic to the AGENTS.md injection
    region (presence as registration), but the code does no text splicing (avoiding
    namespace and merge noise), using discovery + invocation instead.
    """
    import wikilib

    pages = list(wikilib.walk_pages(ROOT))  # single scan shared by all plugins (frugal invocation)
    ctx = types.SimpleNamespace(root=ROOT, pages=pages)
    counts = {"error": 0, "warning": 0, "info": 0}
    ran = 0
    for pid in sorted(plugins):
        if only and pid != only:
            continue
        cpath = os.path.join(plugins[pid].get("_dir", os.path.join(PLUGINS_DIR, pid)), "scripts", "check.py")
        if not os.path.exists(cpath):
            continue
        spec = importlib.util.spec_from_file_location(f"plugin_check_{pid}", cpath)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
            issues = mod.check(ctx) or []
        except Exception as e:  # a check script's own failure is reported as an error, without taking down the other plugins
            print(f"[error] ({pid}) check script failed: {e}")
            counts["error"] += 1
            ran += 1
            continue
        ran += 1
        for it in issues:
            level = str(it.get("level", "warning"))
            counts[level] = counts.get(level, 0) + 1
            print(f"[{level}] ({pid}) {it.get('message', '')}")
    if ran == 0:
        print("[audit] no plugin carries scripts/check.py (optional contract; currently semantic-only)")
        return 0
    print(f"[audit] {ran} plugins, error {counts['error']} / warning {counts.get('warning', 0)} / info {counts.get('info', 0)}")
    return 1 if counts["error"] else 0


def do_inject(plugins):
    """Rebuild the AGENTS.md injection region from manifests (preamble preserved, blocks in dependency topology + alphabetical order, idempotent)."""
    text = open(AGENTS_MD, encoding="utf-8").read()
    m = re.search(re.escape(INJECT_START) + r"\n(.*?)" + re.escape(INJECT_END), text, re.S)
    if not m:
        print("[error] AGENTS.md: inject markers (wiki-inject:start/end) not found")
        return False
    region = m.group(1)
    first = region.find("<!-- plugin:")
    preamble = region[:first].rstrip() if first != -1 else region.rstrip()
    blocks, exited = build_inject_blocks(plugins)
    new_region = preamble + "\n\n" + "\n\n".join(blocks) + "\n\n"
    if new_region == region:
        print("[inject] region unchanged")
        return True
    open(AGENTS_MD, "w", encoding="utf-8", newline="\n").write(
        text[: m.start(1)] + new_region + text[m.end(1):]
    )
    tail = f", {exited} member-tier exits skipped" if exited else ""
    print(f"[inject] rebuilt ({len(blocks)} plugin blocks{tail})")
    return True


def do_check_inject(plugins):
    """Rebuild the check command's injection region from each manifest's checks list (presence as registration, idempotent).

    Isomorphic to the AGENTS.md injection region: the manifest is the body, the check
    block is the projection — to change inspection rules, change the manifest's checks
    list, and drift between projection and handwritten blocks disappears.
    """
    if not os.path.exists(CHECK_SKILL):
        print("[check-inject] check command absent, skipped")
        return True
    text = open(CHECK_SKILL, encoding="utf-8").read()
    m = re.search(re.escape(CHECK_INJECT_START) + r"\n(.*?)" + re.escape(CHECK_INJECT_END), text, re.S)
    if not m:
        print("[error] check/SKILL.md: inject markers (check-inject:start/end) not found")
        return False
    blocks = []
    for pid in ordered_plugins(plugins):
        items = plugins[pid].get("checks") or []
        if not items:
            continue
        body = "\n".join(f"- {it}" for it in items)
        blocks.append(f"<!-- check:{pid} -->\n{body}\n<!-- /check:{pid} -->")
    new_region = "\n\n".join(blocks) + "\n" if blocks else "\n"
    if new_region == m.group(1):
        print("[check-inject] unchanged")
        return True
    open(CHECK_SKILL, "w", encoding="utf-8", newline="\n").write(
        text[: m.start(1)] + new_region + text[m.end(1):]
    )
    print(f"[check-inject] rebuilt ({len(blocks)} plugin blocks)")
    return True


def do_cmd_inject(plugins):
    """Rebuild command injection regions from manifests: consumes pull + usage_routes source-side routing (presence as registration, idempotent).

    The third projection: plugin write-side contract -> command. Disclosure order: owner
    blocks first (consumes order), routed blocks in the middle (dependency topology plus
    alphabetical), remaining consumes last. Each block is the corresponding manifest usage
    list verbatim — command bodies keep only the operational flow; (un)installing plugins
    adds and removes them automatically.
    """
    import wikilib

    routed = {}  # command -> [plugins] (source-side routing, topology + alphabetical)
    for pid in ordered_plugins(plugins):
        for c in plugins[pid].get("usage_routes") or []:
            routed.setdefault(c, []).append(pid)

    ok = True
    for name in sorted(os.listdir(COMMANDS_DIR)):
        path = os.path.join(COMMANDS_DIR, name, "SKILL.md")
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        fm = wikilib.parse_frontmatter(text)
        consumes = fm.get("consumes")
        if consumes is None:
            continue
        if not isinstance(consumes, list):
            consumes = _owner_list(consumes)
        m = re.search(re.escape(CMD_INJECT_START) + r"\n(.*?)" + re.escape(CMD_INJECT_END), text, re.S)
        if not m:
            print(f"[error] command {name}/: inject markers (cmd-inject:start/end) not found")
            ok = False
            continue
        owners = [o for o in _owner_list(fm.get("owner") or "") if o != "framework"]
        seq, seen = [p for p in consumes if p in owners], set()
        seen.update(seq)
        seq += [p for p in routed.get(name, []) if p not in seen]
        seen.update(seq)
        seq += [p for p in consumes if p not in seen]
        blocks = []
        for pid in seq:
            items = plugins.get(pid, {}).get("usage") or []
            if items:
                body = "\n".join(f"- {it}" for it in items)
                blocks.append(f"<!-- usage:{pid} -->\n{body}\n<!-- /usage:{pid} -->")
        new_region = "\n\n".join(blocks) + "\n" if blocks else "\n"
        if new_region == m.group(1):
            continue
        open(path, "w", encoding="utf-8", newline="\n").write(
            text[: m.start(1)] + new_region + text[m.end(1):]
        )
        print(f"[cmd-inject] {name}: rebuilt ({len(blocks)} usage blocks)")
    return ok


def do_registry(plugins):
    """Rebuild the registry.yaml plugin section from the manifests' fields (protocol / reserved sections untouched)."""
    text = open(REGISTRY, encoding="utf-8").read()
    m = re.search(r"^plugins:\n(.*?)^reserved:", text, re.S | re.M)
    if not m:
        print("[error] registry.yaml: plugins:/reserved: section structure not found")
        return False
    lines = []
    for pid in sorted(plugins):
        fields = plugins[pid].get("fields")
        if not fields:
            continue  # plugins with no fields of their own stay out of the registry plugin section
        lines.append(f"  {pid}:")
        for f in sorted(fields):
            lines.append(f"    {f}:")
            lines.append(f"      note: {fields[f]}")
    body = "\n".join(lines) + "\n\n"
    if body == m.group(1):
        print("[registry] plugin section unchanged")
        return True
    open(REGISTRY, "w", encoding="utf-8", newline="\n").write(
        text[: m.start(1)] + body + text[m.end(1):]
    )
    print("[registry] plugin section rebuilt")
    return True


def do_deploy():
    """Sync .owfa/command/*/SKILL.md and connectors/*/SKILL.md -> .agents/skills/*/SKILL.md; orphan copies are reported only."""
    sources = {}
    for base in (COMMANDS_DIR, CONNECTORS_DIR):
        if not os.path.isdir(base):
            continue
        for d in sorted(os.listdir(base)):
            src = os.path.join(base, d, "SKILL.md")
            if not os.path.isfile(src):
                continue
            if d in sources:
                print(f"[warning] skill name collision: {d}/ in both commands and connectors; commands win")
                continue
            sources[d] = src
    changed = 0
    for name, src in sorted(sources.items()):
        dst_dir = os.path.join(SKILLS_DIR, name)
        dst = os.path.join(dst_dir, "SKILL.md")
        os.makedirs(dst_dir, exist_ok=True)
        if not os.path.exists(dst) or open(src, "rb").read() != open(dst, "rb").read():
            shutil.copyfile(src, dst)
            changed += 1
            print(f"[deploy] synced {name}/SKILL.md")
    if os.path.isdir(SKILLS_DIR):
        for d in sorted(os.listdir(SKILLS_DIR)):
            if d not in sources and os.path.isdir(os.path.join(SKILLS_DIR, d)):
                print(f"[warning] orphan copy .agents/skills/{d}/ (master gone; deletion belongs to human)")
    if not changed:
        print("[deploy] all in sync")
    return True


def do_ls(plugins):
    for pid in sorted(plugins):
        deps = ", ".join(plugins[pid].get("depends") or []) or "—"
        cmds = ", ".join(plugins[pid].get("commands") or []) or "—"
        tier = "member" if plugins[pid].get("inject_tier") == "member" else "full"
        size = len(str(plugins[pid].get("inject") or "").encode("utf-8"))
        print(f"  {pid:<10} {plugins[pid].get('version', '?'):<6} {tier:<6} {size:>5} B  deps {deps}; commands {cmds}")
    print(f"{len(plugins)} plugins (.owfa/plugins/; injection order = dependency topo + alphabetical; inject budget {INJECT_BUDGET} B)")
    # usage routing table: plugin -> landing commands (own + source-side routes + command pulls)
    import wikilib

    consumes_map = {}
    for name in sorted(os.listdir(COMMANDS_DIR)):
        path = os.path.join(COMMANDS_DIR, name, "SKILL.md")
        if not os.path.exists(path):
            continue
        c = wikilib.parse_frontmatter(open(path, encoding="utf-8").read()).get("consumes")
        if c is None:
            continue
        consumes_map[name] = c if isinstance(c, list) else _owner_list(c)
    rows = []
    for pid in sorted(plugins):
        if not (plugins[pid].get("usage") or []):
            continue
        targets = list(dict.fromkeys(
            list(plugins[pid].get("commands") or [])
            + list(plugins[pid].get("usage_routes") or [])
            + [c for c, lst in consumes_map.items() if pid in lst]))
        rows.append(f"  {pid:<12} -> {', '.join(targets) if targets else '(no targets — contract documentation surface)'}")
    if rows:
        print("usage routing (plugin → commands):")
        print("\n".join(rows))


def parse_pkg(path):
    """Parse PKG.yaml's minimal shape (scalars / flow lists / block dict-lists / one nested mapping of lists); raises ValueError."""
    data, target, item = {}, None, None

    def flow_list(s):
        s = s.strip()
        if not (s.startswith("[") and s.endswith("]")):
            raise ValueError(f"expected flow list, got: {s!r}")
        inner = s[1:-1].strip()
        return [strip_quotes(x.strip()) for x in inner.split(",")] if inner else []

    for raw in open(path, encoding="utf-8").read().splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if indent == 0:
            m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
            if not m:
                raise ValueError(f"unparsable line: {raw!r}")
            key, val = m.group(1), m.group(2)
            if val == "":
                data[key] = None
            elif val.startswith("["):
                data[key] = flow_list(val)
            else:
                data[key] = strip_quotes(val)
            target, item = key, None
        elif indent == 2 and line.startswith("- "):
            if target is None:
                raise ValueError(f"list item before any key: {raw!r}")
            body = line[2:]
            if data.get(target) is None:
                data[target] = []
            if re.match(r"^[A-Za-z_][\w-]*:\s*\S", body) and ":" in body:
                k, v = body.split(":", 1)
                data[target].append({k.strip(): strip_quotes(v.strip())})
                item = data[target][-1]
            else:
                data[target].append(strip_quotes(body))
                item = None
        elif indent == 2:
            m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
            if not m or target is None:
                raise ValueError(f"unparsable line: {raw!r}")
            if data.get(target) is None:
                data[target] = {}
            k, v = m.group(1), m.group(2)
            data[target][k] = flow_list(v) if v.startswith("[") else (strip_quotes(v) if v else "")
            item = None
        elif indent == 4 and item is not None:
            m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
            if not m:
                raise ValueError(f"unparsable line: {raw!r}")
            item[m.group(1)] = strip_quotes(m.group(2))
        else:
            raise ValueError(f"unparsable line: {raw!r}")
    return data


def load_packages(errors):
    """Read domains/*/PKG.yaml package declarations (D1); returns {pkg_id: pkg}."""
    pkgs = {}
    domains_dir = os.path.join(PLUGINS_DIR, "domains")
    if not os.path.isdir(domains_dir):
        return pkgs
    for name in sorted(os.listdir(domains_dir)):
        ppath = os.path.join(domains_dir, name, "PKG.yaml")
        if not os.path.exists(ppath):
            continue
        try:
            pkgs[name] = parse_pkg(ppath)
            if pkgs[name].get("id") and pkgs[name]["id"] != name:
                errors.append(f"[error] domains/{name}/PKG.yaml: id ({pkgs[name]['id']}) != directory name")
        except ValueError as e:
            errors.append(f"[error] domains/{name}/PKG.yaml: {e}")
    return pkgs


def framework_version():
    """Framework version anchor (.owfa/VERSION, 'X.Y' — #20 D2); None when absent."""
    vpath = os.path.join(ROOT, ".owfa", "VERSION")
    if not os.path.exists(vpath):
        return None
    m = re.fullmatch(r"\s*(\d+)\.(\d+)\s*", open(vpath, encoding="utf-8").read())
    return (int(m.group(1)), int(m.group(2))) if m else None


def validate_packages(plugins, pkgs, errors, warnings):
    """Package invariants (issue #20 定稿 D1/D2/D5): roster == family closure (authoring side),
    full presence (site side, v1 — subsets land with --without later), flat package graph,
    compat vs the .owfa/VERSION anchor."""
    seen_member = {}
    fw = framework_version()
    if fw is None:
        warnings.append(".owfa/VERSION missing — framework anchor absent, PKG compat unchecked")
    for pid, pkg in sorted(pkgs.items()):
        members = pkg.get("members")
        if not isinstance(members, list) or not members:
            errors.append(f"[error] PKG {pid}: members must be a non-empty list")
            continue
        for mem in members:
            if mem in seen_member:
                errors.append(f"[error] PKG {pid}: member {mem} also declared by PKG {seen_member[mem]} (one plugin one package)")
            seen_member[mem] = pid
        if pid not in members:
            errors.append(f"[error] PKG {pid}: family root {pid} must be a member (D5: roots are never prunable)")
        if all(m in plugins for m in members):  # full presence → authoring invariant (roster == closure); subsets exempt (site invariant above covers them)
            closure = {pid} | {p for p in plugins if reaches_plugin(plugins, p, pid)}
            for extra in sorted(set(members) - closure):
                errors.append(f"[error] PKG {pid}: member {extra} declared but outside the family closure (depends chain never reaches {pid})")
            for miss in sorted(closure - set(members)):
                errors.append(f"[error] PKG {pid}: {miss} is in the family closure but missing from members (roster drift)")
        absent = [mem for mem in members if mem not in plugins]
        if pid not in plugins:
            errors.append(f"[error] PKG {pid}: family root {pid} must be installed (D5: roots are never prunable)")
        elif absent:
            closed = all(dep not in members or dep in plugins
                         for mem in members if mem in plugins
                         for dep in (plugins[mem].get("depends") or []))
            if closed:
                warnings.append(f"PKG {pid}: subset install — pruned {', '.join(absent)} (D5 legal subset)")
            else:
                errors.append(f"[error] PKG {pid}: installed subset not dependency-closed (structural member pruned while dependents remain — see kernel plan <pkg> --without ...)")
        for dep in pkg.get("depends") or []:
            if dep != "framework":
                errors.append(f"[error] PKG {pid}: package dependency {dep} not allowed in v1 (flat graph — framework only)")
        if fw is not None:
            compat = str(pkg.get("compat") or "")
            m = re.fullmatch(r">=\s*(\d+)\.(\d+)", compat)
            if not m:
                warnings.append(f"PKG {pid}: compat ({compat!r}) not in '>= X.Y' form — unchecked (v1 supports only this form)")
            elif (int(m.group(1)), int(m.group(2))) > fw:
                errors.append(f"[error] PKG {pid}: compat {compat} exceeds framework version {'.'.join(map(str, fw))}")


def do_pkg_ls(pkgs, plugins):
    """Package inventory: PKG table + connectors + the implicit core remainder."""
    claimed = {m for pkg in pkgs.values() for m in (pkg.get("members") or [])}
    for pid, pkg in sorted(pkgs.items()):
        members = pkg.get("members") or []
        print(f"pkg {pid:<10} v{pkg.get('version','?'):<5} compat {str(pkg.get('compat','?')):<8} {len(members)} members: {', '.join(members)}")
        for c in pkg.get("connectors") or []:
            where = c.get("path") or ("external" if c.get("external") else "system" if c.get("system") else "?")
            print(f"{'':16}connector {c.get('name')} ({where})")
    core = sorted(p for p in plugins if p not in claimed)
    print(f"core (framework): {len(core)}: {', '.join(core)}")


def _residual_hits(pkg_id, pkg):
    """Anchor-surface reference scan -> hit list (the default teardown gate)."""
    tokens = [pkg_id] + [t for t in (pkg.get("members") or []) if t != pkg_id]
    anchors = [AGENTS_MD,
               os.path.join(ROOT, "wiki", "profile.md"),
               os.path.join(ROOT, "wiki", "language.md"),
               os.path.join(ROOT, "wiki", "calendar.md"),
               os.path.join(ROOT, "wiki", "todo.md")]
    crondir = os.path.join(ROOT, "wiki", "cron")
    if os.path.isdir(crondir):
        anchors += [os.path.join(crondir, f) for f in sorted(os.listdir(crondir)) if f.endswith(".md")]
    hits = []
    for path in anchors:
        if not os.path.exists(path):
            continue
        try:
            lines = open(path, encoding="utf-8").read().splitlines()
        except OSError:
            continue
        inside_inject = False
        for i, line in enumerate(lines, 1):
            if INJECT_START in line:
                inside_inject = True
            if INJECT_END in line:
                inside_inject = False
                continue
            if inside_inject:
                continue  # kernel-managed region — cleaned mechanically on uninstall
            for t in tokens:
                if re.search(rf"(?<![\w-]){re.escape(t)}(?![\w-])", line):
                    hits.append(f"{os.path.relpath(path, ROOT)}:{i}: references {t}: {line.strip()[:120]}")
                    break
    return hits


def do_residual(pkg_id, pkgs):
    """D6 residual scan: grep the semantic anchor surfaces for member references after/before uninstall."""
    if not pkg_id:
        print(__doc__)
        return 2
    pkg = pkgs.get(pkg_id)
    if pkg is None:
        print(f"[error] residual: no such package {pkg_id} (see: kernel pkg)")
        return 1
    hits = _residual_hits(pkg_id, pkg)
    for h in hits:
        print(f"[residual] {h}")
    if hits:
        print(f"[residual] {len(hits)} reference(s) on semantic anchor surfaces (handwritten AGENTS region / profile / language / calendar / todo / cron) — semantic cleanup before/after uninstall, per PKG uninstall.bridges")
    else:
        print("[residual] clean — no member references on semantic anchor surfaces")
    return 0


# ---------- process round: install / uninstall / list-remote / upgrade (issue #20 流程轮) ----------

INDEX_FILENAME = "INDEX.yaml"
INDEX_REMOTE = "https://raw.githubusercontent.com/owfadev/registry/master/INDEX.yaml"
FW_VERSION_REMOTE = "https://raw.githubusercontent.com/owfadev/owfa/master/.owfa/VERSION"


def load_index(errors, quiet=False):
    """Resolve the package index: local ROOT/INDEX.yaml first, then a short-TTL cache, else remote (cached on success; stale cache as fallback)."""
    import urllib.request
    import time
    raw, src = None, None
    local = os.path.join(ROOT, INDEX_FILENAME)
    cache = os.path.join(ROOT, ".owfa", "registry-cache.yaml")
    if os.path.exists(local):
        raw, src = open(local, encoding="utf-8").read(), local
    else:
        fetched = False
        if os.path.exists(cache) and time.time() - os.path.getmtime(cache) < 600:
            raw, src = open(cache, encoding="utf-8").read(), cache + " (TTL fresh)"
            fetched = True
        if not fetched:
            try:
                raw = urllib.request.urlopen(INDEX_REMOTE, timeout=15).read().decode("utf-8")
                src = INDEX_REMOTE
                try:
                    open(cache, "w", encoding="utf-8").write(raw)
                except OSError:
                    pass
            except Exception as e:
                if os.path.exists(cache):  # a stale index beats no index
                    raw, src = open(cache, encoding="utf-8").read(), cache + " (stale fallback)"
                elif not quiet:
                    errors.append(f"[error] index unavailable: {e}")
                    return {}, src
    index = {}
    for line in raw.splitlines():
        m = re.match(r"^\s{2}([\w-]+):\s*\{(.+)\}\s*$", line)
        if not m:
            continue
        entry = {kv.group(1): strip_quotes(kv.group(2).strip()) for kv in re.finditer(r"(\w+):\s*([^,}]+)", m.group(2))}
        if entry:
            index[m.group(1)] = entry
    return index, src


def _clone_package(entry, pkg, tag, errors):
    """git clone the package repo (git is the declared prerequisite); returns the clone dir or None."""
    import subprocess
    import tempfile
    url = entry.get("repo")
    if not url:
        errors.append(f"[error] index entry {pkg} has no repo")
        return None
    tmp = tempfile.mkdtemp(prefix="vw-pkg-")
    ref = tag or (f"{pkg}-v{entry.get('version')}" if entry.get("version") else None)
    cmd = ["git", "clone", "--quiet", "--depth", "1"] + (["--branch", ref] if ref else []) + [url, tmp]
    r = subprocess.run(cmd,
                       capture_output=True, text=True)
    if r.returncode != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        errors.append(f"[error] clone {url}@{ref} failed: {(r.stderr or '').strip()[:200]}")
        return None
    return tmp


def converge(label):
    """Post-change convergence: reload, validate, run every mechanical projection."""
    plugins, errors = load_plugins()
    pkgs = load_packages(errors)
    warns = []
    validate(plugins, errors, warnings=warns)
    if not errors:
        validate_bindings(plugins, errors)
        validate_bridges(plugins, errors)
        validate_packages(plugins, pkgs, errors, warns)
    for w in warns:
        print(f"[warning] {w}")
    for e in errors:
        print(e)
    if errors:
        print(f"[{label}] validation failed ({len(errors)} errors) — fix before continuing")
        return False
    print(f"[{label}] validate: {len(plugins)} plugins green")
    for project in (do_inject, do_check_inject, do_cmd_inject, do_registry):
        if not project(plugins):
            print(f"[{label}] projection failed ({project.__name__}) — state may be partial")
            return False
    if not do_deploy():
        print(f"[{label}] deployment failed — state may be partial")
        return False
    return True


def _preflight_install(src, ignore):
    """Validate the prospective manifest graph before writing installed package state.

    Stage only masters using the same copy filter as install, including --without.
    Binding/bridge/package checks still run after commands and connectors land.
    This is a preflight, not a transaction or a replacement for convergence.
    """
    import tempfile

    plugins, errors = load_plugins()
    warns = []
    try:
        with tempfile.TemporaryDirectory(prefix="vw-preflight-") as stage:
            shutil.copytree(src, os.path.join(stage, "package"), ignore=ignore)
            incoming, load_errors = load_plugins(stage)
            errors.extend(load_errors)
            for name, manifest in incoming.items():
                if name in plugins:
                    errors.append(f"[error] {name}/: duplicate plugin id (already installed)")
                else:
                    plugins[name] = manifest
            if not errors:
                validate(plugins, errors, warnings=warns)
    except (OSError, ValueError) as e:
        errors.append(f"[error] install preflight: {e}")
    for w in warns:
        print(f"[warning] {w}")
    for e in errors:
        print(e)
    if errors:
        print("[install] preflight failed — package files and projections were not changed")
        return False
    return True


def do_install(spec, args, prev_version=None):
    """Install a package from the index (or --path <dir> for a local/unregistered one): masters + connectors + commands, then converge."""
    pkg, _, tag = spec.partition("@") if spec else ("", "", "")
    path = None
    if "--path" in args:
        i = args.index("--path")
        path = args[i + 1] if i + 1 < len(args) else None
    without = []
    if "--without" in args:
        i = args.index("--without")
        without = [x for x in args[i + 1].split(",") if x] if i + 1 < len(args) else []
    if not pkg and not path:
        print(__doc__)
        return 2
    direct = pkg.startswith(("https://", "git@")) or ("/" in pkg and not path)
    # framework repo guard: library posture — the sandbox (test-repo) is the install target
    if os.path.isdir(os.path.join(ROOT, "test-repo")) and not os.path.exists(AGENTS_MD):
        print("[error] framework repo is library posture — install into an instance (e.g. cd test-repo)")
        return 1
    errors = []
    if path:
        src = path
        if not os.path.exists(os.path.join(src, "PKG.yaml")):
            print(f"[error] {src}/PKG.yaml not found (not a package directory)")
            return 1
    elif direct:
        # unindexed repository: reachable by convention, trust unknown — the index PR is the review gate (#20 / #12)
        if "--yes" not in args:
            print(f"[error] direct install of {pkg!r} (not in the index) requires --yes — trust: unknown; the registry PR is how a package earns reviewed trust")
            return 1
        url = pkg if pkg.startswith(("https://", "git@")) else f"https://github.com/{pkg}.git"
        entry = {"repo": url}
        src = _clone_package(entry, pkg, tag or None, errors)
        for e in errors:
            print(e)
        if src is None:
            return 1
        print(f"[install] trust: unknown (unindexed direct install)")
    else:
        index, _src = load_index(errors)
        if pkg not in index:
            print(f"[error] package {pkg} not in the index ({_src}) — third-party packages register via an index PR (#20 生态四问)")
            for e in errors:
                print(e)
            return 1
        entry = index[pkg]
        if entry.get("trust", "") not in ("framework-bundled", "reviewed-3rd-party") and "--yes" not in args:
            print(f"[error] package {pkg} trust level {entry.get('trust')!r} is not auto-installable — explicit --yes required (#12 安全面)")
            return 1
        src = _clone_package(entry, pkg, tag, errors)
        for e in errors:
            print(e)
        if src is None:
            return 1
    try:
        pkgm = parse_pkg(os.path.join(src, "PKG.yaml"))
    except ValueError as e:
        print(f"[error] PKG.yaml: {e}")
        return 1
    pid = str(pkgm.get("id") or pkg or os.path.basename(path))
    if not path and not direct and pid != pkg:
        print(f"[error] index says {pkg}, PKG.yaml says {pid} (index ↔ package mismatch — refuse)")
        return 1
    fw = framework_version()
    if fw is not None:
        m = re.fullmatch(r">=\s*(\d+)\.(\d+)", str(pkgm.get("compat") or ""))
        if m and (int(m.group(1)), int(m.group(2))) > fw:
            print(f"[error] package compat {pkgm.get('compat')} exceeds framework {'.'.join(map(str, fw))}")
            return 1
    if not path and not direct:
        idx_members = set(str(entry.get("members", "")).split("/")) - {""}
        pkg_members = set(pkgm.get("members") or [])
        if idx_members and idx_members != pkg_members:
            print(f"[error] index members {sorted(idx_members)} != PKG.yaml members {sorted(pkg_members)} (index <-> package drift — refuse)")
            return 1
        idx_ver = str(entry.get("version") or "").strip()
        if idx_ver and idx_ver != str(pkgm.get("version")).strip():
            print(f"[error] index version v{idx_ver} != PKG.yaml version v{pkgm.get('version')} (release metadata drift — the tag would install but never reconcile with `pkg`/`upgrade`; refuse)")
            return 1
    members_all = [str(m) for m in (pkgm.get("members") or [])]
    pruned = set()
    if without:
        bad = [w for w in without if w not in members_all]
        if bad:
            print(f"[error] --without {', '.join(bad)}: not members of {pid}")
            return 1
        if pid in without:
            print(f"[error] --without {pid}: the family root is never prunable (D5)")
            return 1
        depends_in = {}
        for m in members_all:
            try:
                deps = parse_manifest(os.path.join(src, m, "PLUGIN.yaml")).get("depends") or []
            except ValueError:
                deps = []
            depends_in[m] = [d for d in deps if d in members_all]
        pruned = set(without)
        changed = True
        while changed:
            changed = False
            for m in members_all:
                if m not in pruned and m != pid and set(depends_in[m]) & pruned:
                    pruned.add(m)
                    changed = True
        if pid in pruned or not [m for m in members_all if m not in pruned]:
            print(f"[error] --without cascade prunes the whole package (root or all members)")
            return 1
        print(f"[install] subset: final members {', '.join(m for m in members_all if m not in pruned)}; pruned {', '.join(sorted(pruned))}")
    dst = os.path.join(PLUGINS_DIR, "domains", pid)
    if os.path.exists(dst):
        print(f"[error] {pid} already installed — uninstall first (kernel uninstall {pid} --yes)")
        return 1
    ignore = shutil.ignore_patterns(".git", ".meta", ".owfa*", "connectors", "command", "README.md",
                                   "__pycache__", "migrations", *sorted(pruned))
    if not _preflight_install(src, ignore):
        if not path:
            shutil.rmtree(src, ignore_errors=True)
        return 1
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copytree(src, dst, ignore=ignore)
    copied_conn, copied_cmd = [], []
    csrc = os.path.join(src, "connectors")
    if os.path.isdir(csrc):
        for d in sorted(os.listdir(csrc)):
            dd = os.path.join(CONNECTORS_DIR, d)
            if os.path.exists(dd):
                print(f"[warning] connector {d} already present — kept existing")
                continue
            os.makedirs(CONNECTORS_DIR, exist_ok=True)
            shutil.copytree(os.path.join(csrc, d), dd, ignore=shutil.ignore_patterns("__pycache__", ".venv", "*.egg-info"))
            copied_conn.append(d)
    msrc = os.path.join(src, "command")
    if os.path.isdir(msrc):
        import wikilib
        for d in sorted(os.listdir(msrc)):
            fm_path = os.path.join(msrc, d, "SKILL.md")
            if os.path.exists(fm_path):
                owners = _owner_list(wikilib.parse_frontmatter(open(fm_path, encoding="utf-8").read()).get("owner"))
                if owners and owners[0] in pruned:
                    continue  # command of a pruned member rides out with it
            dd = os.path.join(COMMANDS_DIR, d)
            if os.path.exists(dd):
                print(f"[warning] command {d} already present — kept existing")
                continue
            shutil.copytree(os.path.join(msrc, d), dd, ignore=shutil.ignore_patterns("__pycache__"))
            copied_cmd.append(d)
    led0 = _load_ledger()
    if pid in led0 and led0[pid].get("kind") == "teardown":
        del led0[pid]  # reinstall: the teardown premise vanished with the package's return
        _save_ledger(led0)
        _banner_set(led0)
        _journal("sweep", f"{pid} teardown swept by reinstall")
        print(f"[sweep] {pid}: pending teardown swept (reinstall — premise vanished)")
    staged = _stage_migrations(os.path.join(src, "migrations"), pid, prev_version, pkgm.get("version"))
    os.makedirs(os.path.join(MIGRATIONS_DIR, pid), exist_ok=True)
    try:
        shutil.copyfile(os.path.join(src, "PKG.yaml"), os.path.join(MIGRATIONS_DIR, pid, "PKG.yaml"))  # dormant roster copy — residue-reference for self-healing
    except OSError:
        pass
    tsrc = os.path.join(src, "migrations")
    if os.path.isdir(tsrc):  # dormant teardown declaration rides along silently until an uninstall consumes it
        for f in ("teardown.md", "teardown.py"):
            if os.path.exists(os.path.join(tsrc, f)):
                shutil.copyfile(os.path.join(tsrc, f), os.path.join(MIGRATIONS_DIR, pid, f))
    if not path:
        shutil.rmtree(src, ignore_errors=True)
    print(f"[install] {pid}: masters -> .owfa/plugins/domains/{pid}/"
          + (f"; connectors: {', '.join(copied_conn)}" if copied_conn else "")
          + (f"; commands: {', '.join(copied_cmd)}" if copied_cmd else ""))
    _journal("install", f"{pid} v{pkgm.get('version')}" + (f" subset(-{','.join(sorted(pruned))})" if pruned else "") + (f" staged={','.join(staged)}" if staged else ""))
    converged = converge("install")
    if staged:
        print(f"[pending] semantic migration staged for {pid}: {', '.join(staged)} — kernel migrate {pid}; validate stays red until cleared")
    if not converged:
        print("[error] install incomplete — files may remain; run kernel validate before retrying")
        return 1
    return 0


def do_uninstall(pkg, args):
    """D6 uninstall: mechanical four-clear + convergence; data zones and credentials never touched."""
    if not pkg:
        print(__doc__)
        return 2
    if "--yes" not in args:
        print("[error] uninstall needs --yes (removes package masters + projections; data zones stay — #20 D6)")
        return 1
    pkg_dir = os.path.join(PLUGINS_DIR, "domains", pkg)
    if not os.path.exists(pkg_dir):
        print(f"[error] {pkg} not installed")
        return 1
    try:
        pkgm = parse_pkg(os.path.join(pkg_dir, "PKG.yaml"))
    except ValueError as e:
        print(f"[warning] PKG.yaml unreadable ({e}) — proceeding with mechanical removal")
        pkgm = {}
    members = set(pkgm.get("members") or [pkg])
    import wikilib
    removed_cmd = []
    if os.path.isdir(COMMANDS_DIR):
        for d in sorted(os.listdir(COMMANDS_DIR)):
            fm_path = os.path.join(COMMANDS_DIR, d, "SKILL.md")
            if not os.path.exists(fm_path):
                continue
            owners = _owner_list(wikilib.parse_frontmatter(open(fm_path, encoding="utf-8").read()).get("owner"))
            if owners and owners[0] in members:
                shutil.rmtree(os.path.join(COMMANDS_DIR, d))
                sk = os.path.join(SKILLS_DIR, d)
                if os.path.isdir(sk):
                    shutil.rmtree(sk)
                removed_cmd.append(d)
    removed_conn = []
    for c in pkgm.get("connectors") or []:
        name = c.get("name")
        if not name:
            continue
        cd = os.path.join(CONNECTORS_DIR, name)
        if os.path.isdir(cd):
            shutil.rmtree(cd)
            removed_conn.append(name)
        sk = os.path.join(SKILLS_DIR, name)
        if os.path.isdir(sk) and not os.path.exists(os.path.join(COMMANDS_DIR, name)):
            shutil.rmtree(sk)
    # teardown (x->0): dormant declaration staged before removal — semantic cleanup debt gets its warning
    tmd = os.path.join(MIGRATIONS_DIR, pkg, "teardown.md")
    if os.path.exists(tmd):
        led = _load_ledger()
        led[pkg] = {"kind": "teardown", "from": str(pkgm.get("version", "?")), "to": "0", "items": ["teardown"]}
        _save_ledger(led)
        _banner_set(led)
        try:
            shutil.copyfile(os.path.join(pkg_dir, "PKG.yaml"), os.path.join(MIGRATIONS_DIR, pkg, "PKG.yaml"))
        except OSError:
            pass
        _journal("warn+", f"{pkg} teardown staged (x->0)")
        print(f"[pending] {pkg}: teardown staged (x->0) — semantic deletion commands outstanding; kernel migrate {pkg}")
    shutil.rmtree(pkg_dir)
    # migrate-kind state sweeps with the package; teardown-kind survives (it is ABOUT the absence)
    led = _load_ledger()
    if pkg in led and led[pkg].get("kind", "migrate") == "migrate":
        del led[pkg]
        _save_ledger(led)
        _banner_set(led)
        shutil.rmtree(os.path.join(MIGRATIONS_DIR, pkg), ignore_errors=True)
        _journal("sweep", f"{pkg} migration state cleared by uninstall")
        print(f"[uninstall] {pkg}: pending migration state swept (ledger/staging/banner)")
    print(f"[uninstall] {pkg}: masters removed"
          + (f"; commands: {', '.join(removed_cmd)}" if removed_cmd else "")
          + (f"; connectors: {', '.join(removed_conn)}" if removed_conn else ""))
    _journal("uninstall", f"{pkg} v{pkgm.get('version', '?')}")
    converge("uninstall")
    do_residual(pkg, {pkg: pkgm})
    un = pkgm.get("uninstall") or {}
    if un.get("retains"):
        print(f"[uninstall] retains (never touched): {', '.join(un['retains'])}")
    if un.get("credentials"):
        print(f"[uninstall] credentials stay on this machine — remove manually if desired: {', '.join(un['credentials'])}")
    if un.get("processes"):
        print(f"[uninstall] stop long-running executors if any: {', '.join(un['processes'])}")
    for d in (os.path.join(PLUGINS_DIR, "domains"), CONNECTORS_DIR):
        if os.path.isdir(d) and not os.listdir(d):
            os.rmdir(d)  # empty containers leave no residue
    return 0


def do_list_remote():
    """Index table with installed marks — GitHub is the marketplace page, this is the agent surface."""
    errors = []
    index, src = load_index(errors)
    installed = load_packages([])
    print(f"index: {src}")
    for name, e in sorted(index.items()):
        mark = "installed" if name in installed else "available"
        print(f"  {name:<10} v{e.get('version', '?'):<5} compat {e.get('compat', '?'):<8} [{mark}] {e.get('summary', '')}")
        mem = str(e.get("members", "")).replace("/", ", ")
        print(f"  {'':<12}members: {mem if mem else '?'}")
        print(f"  {'':<12}{e.get('repo', '')}  trust: {e.get('trust', '?')}")
    for e in errors:
        print(e)
    return 0 if index else 1


def _upgrade_action(pkg, args):
    """Mechanical reinstall + update report + migration chain staging (issue #20 + migration design)."""
    import contextlib
    import io
    pkg_dir = os.path.join(PLUGINS_DIR, "domains", pkg)
    if not os.path.exists(pkg_dir):
        print(f"[error] {pkg} not installed")
        return 1
    old_pkgm = parse_pkg(os.path.join(pkg_dir, "PKG.yaml"))
    old_ver = str(old_pkgm.get("version", "0"))
    old_members = {}
    for m in old_pkgm.get("members") or []:
        mp = os.path.join(pkg_dir, str(m), "PLUGIN.yaml")
        if os.path.exists(mp):
            try:
                old_members[str(m)] = str(parse_manifest(mp).get("version", "?"))
            except ValueError:
                old_members[str(m)] = "?"
    path = None
    if "--path" in args:
        i = args.index("--path")
        path = args[i + 1] if i + 1 < len(args) else None
    errors = []
    if path:
        src = path
        if not os.path.exists(os.path.join(src, "PKG.yaml")):
            print(f"[error] {src}/PKG.yaml not found")
            return 1
    else:
        index, _src = load_index(errors)
        if pkg not in index:
            print(f"[error] {pkg} not in the index — use --path for local/dev upgrades")
            return 1
        entry = index[pkg]
        src = _clone_package(entry, pkg, None, errors)
        for e in errors:
            print(e)
        if src is None:
            return 1
    new_pkgm = parse_pkg(os.path.join(src, "PKG.yaml"))
    new_ver = str(new_pkgm.get("version", old_ver))
    if new_ver == old_ver:
        print(f"[upgrade] {pkg}: already at v{old_ver} (index/local agree) — nothing to do")
        if not path:
            shutil.rmtree(src, ignore_errors=True)
        return 0
    fw = framework_version()
    if fw is not None:
        m = re.fullmatch(r">=\s*(\d+)\.(\d+)", str(new_pkgm.get("compat") or ""))
        if m and (int(m.group(1)), int(m.group(2))) > fw:
            print(f"[error] upgrade needs framework {'.'.join(map(str, (int(m.group(1)), int(m.group(2)))))} first — run `npx owfa upgrade` (npm channel), or sync the template trees and rerun kernel all")
            return 1
    # quiet mechanical reinstall (uninstall -> install-from-src with prev_version)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ok1 = do_uninstall(pkg, ["--yes"])
        ok2 = do_install(pkg + ("" if path else ""), (["--path", path] if path else []), prev_version=old_ver) if ok1 == 0 else 1
    if ok2 != 0:
        print(buf.getvalue())
        print("[error] reinstall failed — state may be partial, rerun kernel validate")
        return 1
    # report: member version deltas + changelog excerpts
    new_members = {}
    for m in new_pkgm.get("members") or []:
        mp = os.path.join(PLUGINS_DIR, "domains", pkg, str(m), "PLUGIN.yaml")
        if os.path.exists(mp):
            try:
                new_members[str(m)] = str(parse_manifest(mp).get("version", "?"))
            except ValueError:
                new_members[str(m)] = "?"
    changed = {m: (old_members.get(m, "new"), new_members.get(m, "new")) for m in new_members if old_members.get(m, "new") != new_members.get(m, "new")}
    print(f"[upgrade] {pkg} v{old_ver} -> v{new_ver} — {len(changed)} member change(s); semantic migrations: {', '.join(_load_ledger().get(pkg, {}).get('items', [])) or 'none'}")
    for m, (a, b) in sorted(changed.items()):
        print(f"[upgrade]   {m} {a} -> {b}")
        if a != "new":
            for line in _changelog_delta(os.path.join(PLUGINS_DIR, "domains", pkg, m, "PLUGIN.md"), a, b)[:4]:
                print(f"[upgrade]     {line}")
    _journal("upgrade", f"{pkg} {old_ver}->{new_ver} changed={len(changed)}")
    if _load_ledger().get(pkg):
        print(f"[pending] {pkg}: semantic migration staged — kernel migrate {pkg}; validate stays red until cleared")
    return 0


def do_upgrade(pkg, args=None):
    """Reconciliation report (packages vs index, framework vs template remote); `upgrade <pkg> --yes` performs the mechanical reinstall + stages migrations (per #20 逐包不级联)."""
    args = args or []
    if pkg and "--yes" in args:
        return _upgrade_action(pkg, args)
    errors = []
    index, src = load_index(errors)
    installed = load_packages([])
    fw = framework_version()
    fw_note = ""
    try:
        import urllib.request
        rfw = urllib.request.urlopen(FW_VERSION_REMOTE, timeout=10).read().decode("utf-8").strip()
        m = re.fullmatch(r"(\d+)\.(\d+)", rfw)
        if m:
            rt = (int(m.group(1)), int(m.group(2)))
            if fw and rt > fw:
                fw_note = f" — remote v{rfw} available (run `npx owfa upgrade`, or manual sync: template diff → selective copy → kernel all, see CONTRIBUTING)"
            elif fw:
                fw_note = " — up to date with the template"
    except Exception:
        fw_note = " — remote check unavailable"
    print(f"framework {'.'.join(map(str, fw)) if fw else '?'}{fw_note} — index: {src}")
    rows = 0
    for name, local in sorted(installed.items()):
        lv = str(local.get("version", "?"))
        e = index.get(name)
        if not e:
            print(f"  {name:<10} local v{lv} — not in the index (instance-local package, channel C)")
        else:
            rv = e.get("version", "?")
            state = "up to date" if lv == rv else f"v{lv} -> v{rv}: kernel upgrade {name} --yes"
            print(f"  {name:<10} local v{lv}  remote v{rv} — {state}")
        rows += 1
    if pkg and pkg not in installed:
        print(f"  {pkg:<10} not installed")
    if not rows:
        print("  (no packages installed)")
    for e in errors:
        print(e)
    return 0


def _vt(x):
    return tuple(int(i) for i in str(x).split("."))


def _journal(op, detail):
    import datetime
    line = f"{datetime.datetime.now().isoformat(timespec='seconds')} {op} {detail}"
    try:
        old = open(JOURNAL, encoding="utf-8").read().splitlines() if os.path.exists(JOURNAL) else []
    except OSError:
        old = []
    old.append(line)
    open(JOURNAL, "w", encoding="utf-8").write("\n".join(old[-500:]) + "\n")


def _load_ledger():
    import json as _json
    if not os.path.exists(LEDGER):
        return {}
    try:
        return _json.load(open(LEDGER, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_ledger(led):
    import json as _json
    os.makedirs(MIGRATIONS_DIR, exist_ok=True)
    _json.dump(led, open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def _banner_set(entries):
    """Tri-face visibility, agent side: a kernel-managed block inside the AGENTS injection region — every session sees it until cleared."""
    if not os.path.exists(AGENTS_MD):
        return
    text = open(AGENTS_MD, encoding="utf-8").read()
    text = re.sub(r"<!-- pending-migrations -->.*?<!-- /pending-migrations -->\n*", "", text, flags=re.S)
    if entries:
        lines = "; ".join(f"{k} {v.get('from', '?')}->{v.get('to', '?')}" for k, v in sorted(entries.items()))
        block = (f"<!-- pending-migrations -->\n> ⚠ PENDING SEMANTIC MIGRATIONS: {lines} — "
                 f"territory may be mid-shape; complete via `kernel migrate <pkg> --clear`; validate stays red until cleared.\n<!-- /pending-migrations -->\n\n")
        m = re.search(re.escape(INJECT_START) + r"\n", text)
        if m:
            text = text[:m.end()] + "\n" + block + text[m.end():]
    open(AGENTS_MD, "w", encoding="utf-8").write(text)


def _stage_migrations(migsrc, pid, prev_version, new_version):
    """Stage declarations into the kernel zone + register the ledger + AGENTS banner. Package dirs never carry migrations (use-and-delete)."""
    if not os.path.isdir(migsrc):
        return []
    os.makedirs(os.path.join(MIGRATIONS_DIR, pid), exist_ok=True)
    staged = []
    if prev_version is None:
        cands = [("init", "init.md")] if os.path.exists(os.path.join(migsrc, "init.md")) else []
    else:
        cands = []
        for f in sorted(os.listdir(migsrc)):
            m = re.fullmatch(r"(\d+\.\d+)-to-(\d+\.\d+)\.md", f)
            if m and _vt(m.group(1)) >= _vt(prev_version):
                cands.append((f[:-3], f))
    for label, f in cands:
        shutil.copyfile(os.path.join(migsrc, f), os.path.join(MIGRATIONS_DIR, pid, f))
        pyp = os.path.join(migsrc, f[:-3] + ".py")
        if os.path.exists(pyp):
            shutil.copyfile(pyp, os.path.join(MIGRATIONS_DIR, pid, f[:-3] + ".py"))
        staged.append(label)
    if staged:
        led = _load_ledger()
        pkgd = os.path.join(PLUGINS_DIR, "domains", pid)
        present = [str(m) for m in ((parse_pkg(os.path.join(pkgd, "PKG.yaml")).get("members")) if os.path.exists(os.path.join(pkgd, "PKG.yaml")) else []) if os.path.isdir(os.path.join(pkgd, str(m)))]
        led[pid] = {"from": str(prev_version or "0"), "to": str(new_version), "items": staged, "members": present}
        _save_ledger(led)
        _banner_set(led)
        _journal("warn+", f"{pid} {prev_version or '0'}->{new_version} items={','.join(staged)}")
    return staged


def _ast_gate(path):
    """Verify-script gate: stdlib-adjacent, read-only, defines verify(ctx). Catches casual abuse; malice is the registry review's job."""
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except SyntaxError as e:
        return [f"syntax error: {e}"]
    issues = []
    banned = {"subprocess", "shutil", "socket", "urllib", "urllib.request", "requests", "http", "ftplib", "telnetlib", "pickle"}
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name.split(".")[0] in banned:
                    issues.append(f"banned import: {a.name}")
        elif isinstance(n, ast.ImportFrom):
            if (n.module or "").split(".")[0] in banned:
                issues.append(f"banned import: {n.module}")
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "open":
            mode = n.args[1].value if len(n.args) > 1 and isinstance(n.args[1], ast.Constant) else "r"
            if any(c in str(mode) for c in "wa+"):
                issues.append(f"open(..., {mode!r}) — verify is read-only")
    if not any(isinstance(n, ast.FunctionDef) and n.name == "verify" for n in tree.body):
        issues.append("verify(ctx) not defined")
    return issues


def _run_verify(py_path):
    """Execute a staged verify(ctx) in-process; returns (issues, gate_problems)."""
    sys.dont_write_bytecode = True  # staged code is use-and-delete; leave no __pycache__ behind
    gate = _ast_gate(py_path)
    if gate:
        return None, gate
    import wikilib
    spec = importlib.util.spec_from_file_location("vw_verify", py_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    pkg = os.path.basename(os.path.dirname(os.path.abspath(py_path)))
    pkg_dir = os.path.join(PLUGINS_DIR, "domains", pkg)
    installed = []
    if os.path.isdir(pkg_dir):
        try:
            pm = parse_pkg(os.path.join(pkg_dir, "PKG.yaml"))
            installed = [str(m) for m in (pm.get("members") or []) if os.path.isdir(os.path.join(pkg_dir, str(m)))]
        except ValueError:
            installed = []
    ctx = types.SimpleNamespace(root=ROOT, pages=list(wikilib.walk_pages(ROOT)), installed=installed)  # subset matching: verifies address the installed subset, never the full roster
    try:
        return mod.verify(ctx) or [], []
    except Exception as e:
        return None, [f"verify() raised: {e}"]


def _changelog_delta(md_path, old_v, new_v):
    try:
        sec = open(md_path, encoding="utf-8").read().split("## Changelog", 1)[1]
    except (OSError, IndexError):
        return []
    out = []
    for line in sec.splitlines():
        m = re.match(r"-\s+(\d+(?:\.\d+)?)\s*[\s(]", line.strip())
        if m and _vt(old_v) < _vt(m.group(1)) <= _vt(new_v):
            out.append(line.strip()[:160])
    return out


def do_migrate(pkg, args):
    """Migration status / declaration printing / gated clear. The exit is always open: migrate works while warned."""
    led = _load_ledger()
    if not pkg:
        if not led:
            print("[migrate] no pending semantic migrations")
            return 0
        for k, v in sorted(led.items()):
            print(f"[migrate] {k} {v.get('from')}->{v.get('to')} pending: {', '.join(v.get('items', []))}")
        return 0
    ent = led.get(pkg)
    if ent is None:
        print(f"[migrate] {pkg}: nothing pending")
        return 0
    pdir = os.path.join(MIGRATIONS_DIR, pkg)
    if "--clear" not in args:
        print(f"[migrate] {pkg} {ent.get('from')}->{ent.get('to')} pending: {', '.join(ent.get('items', []))}")
        for f in sorted(os.listdir(pdir)) if os.path.isdir(pdir) else []:
            if f.endswith(".md"):
                print(f"[migrate] --- {f} ---")
                print(open(os.path.join(pdir, f), encoding="utf-8").read().rstrip())
                pyf = os.path.join(pdir, f[:-3] + ".py")
                if os.path.exists(pyf):
                    issues, gate = _run_verify(pyf)
                    if gate:
                        print(f"[migrate] verify gate: {gate}")
                    elif issues:
                        print(f"[migrate] verify: {len(issues)} issue(s): " + " | ".join(str(i)[:100] for i in issues[:5]))
                    else:
                        print("[migrate] verify: clean — ready to clear (--clear)")
                elif ent.get("kind") == "teardown":
                    pk = os.path.join(pdir, "PKG.yaml")  # default gate: show what the residual scan still sees
                    pkgm2 = parse_pkg(pk) if os.path.exists(pk) else {"members": [pkg]}
                    for h in _residual_hits(pkg, pkgm2)[:8]:
                        print(f"[migrate] residual: {h}")
                    if not _residual_hits(pkg, pkgm2):
                        print("[migrate] residual gate: clean — ready to clear (--clear)")
        return 0
    # --clear: verify-gated (explicit assertion only via --force when no script)
    cleared_all = True
    for f in sorted(os.listdir(pdir)) if os.path.isdir(pdir) else []:
        if not f.endswith(".py"):
            continue
        issues, gate = _run_verify(os.path.join(pdir, f))
        if gate:
            print(f"[error] verify gate refused {f}: {gate}")
            return 1
        errs = [i for i in issues if not (isinstance(i, (tuple, list)) and i[0] == "warning")]
        if errs:
            print(f"[error] {f}: migration incomplete — {len(errs)} issue(s): " + " | ".join(str(i)[:100] for i in errs[:5]))
            return 1
        if issues:
            print(f"[warning] {f}: warnings (non-blocking): " + " | ".join(str(i)[:100] for i in issues[:5]))
    has_py = any(f.endswith(".py") for f in os.listdir(pdir)) if os.path.isdir(pdir) else False
    if not has_py:
        if ent.get("kind") == "teardown":
            pk = os.path.join(pdir, "PKG.yaml")
            pkgm2 = parse_pkg(pk) if os.path.exists(pk) else {"members": [pkg]}
            hits = _residual_hits(pkg, pkgm2)
            if hits:
                print(f"[error] teardown incomplete — residual references on anchor surfaces: {hits[:5]}")
                return 1
        elif "--force" not in args:
            print(f"[error] no verify script staged for {pkg} — clear needs --force (explicit assertion) or author-provided verify")
            return 1
    if ent.get("kind") == "teardown":
        shutil.rmtree(pdir, ignore_errors=True)
    else:
        for item in ent.get("items", []):  # delete the pending items only — dormant teardown files survive for a future uninstall
            for ext in (".md", ".py"):
                try:
                    os.remove(os.path.join(pdir, item + ext))
                except OSError:
                    pass
    del led[pkg]
    _save_ledger(led)
    _banner_set(led)
    _journal("clear", f"{pkg} {ent.get('from')}->{ent.get('to')} verify-clean")
    print(f"[migrate] {pkg}: warning cleared, staged files deleted (use-and-delete); validate unblessed — permanent invariants belong in scripts/check.py (judgment split rule)")
    return 0


def do_plan(spec, args):
    """One-shot disclosure plan (consent-wizard data source): trust, package disclosure, baseline/optional members, connectors, suggested command. Never interactive."""
    import json as _json
    pkg, _, tag = spec.partition("@") if spec else ("", "", "")
    if not pkg:
        print(__doc__)
        return 2
    errors = []
    index, _src = load_index(errors, quiet=True)
    entry = index.get(pkg)
    direct = entry is None
    if direct:
        if not ("/" in pkg or pkg.startswith(("https://", "git@"))):
            print(f"[error] package {pkg} not in the index (registry)")
            for e in errors:
                print(e)
            return 1
        url = pkg if pkg.startswith(("https://", "git@")) else f"https://github.com/{pkg}.git"
        entry = {"repo": url, "trust": "unknown (unindexed direct)", "version": ""}
    src = _clone_package(entry, pkg, tag or None, errors)
    for e in errors:
        print(e)
    if src is None:
        return 1
    try:
        pkgm = parse_pkg(os.path.join(src, "PKG.yaml"))
    except ValueError as e:
        print(f"[error] PKG.yaml: {e}")
        shutil.rmtree(src, ignore_errors=True)
        return 1
    pid = str(pkgm.get("id") or pkg)
    members = [str(m) for m in (pkgm.get("members") or [])]
    menu = pkgm.get("menu") or {}
    depends_in = {}
    for m in members:
        try:
            deps = parse_manifest(os.path.join(src, m, "PLUGIN.yaml")).get("depends") or []
        except ValueError:
            deps = []
        depends_in[m] = [d for d in deps if d in members]

    def closure_of(m):
        out, stack = set(), [m]
        while stack:
            x = stack.pop()
            for d in depends_in.get(x, []):
                if d not in out:
                    out.add(d)
                    stack.append(d)
        return out

    optional = [m for m in members if m != pid]
    plan = {
        "package": pid,
        "version": pkgm.get("version"),
        "compat": pkgm.get("compat"),
        "trust": entry.get("trust", "?"),
        "disclosure": pkgm.get("disclosure") or "(no package disclosure declared)",
        "baseline": [{"id": pid, "summary": menu.get(pid, "")}],
        "optional": [{"id": m, "summary": menu.get(m, ""), "pulls": sorted(closure_of(m) - {pid})} for m in optional],
        "connectors": [{"name": c.get("name"), "kind": ("external" if c.get("external") else "system" if c.get("system") else "in-repo")}
                       for c in (pkgm.get("connectors") or [])],
        "suggested_command": f"kernel install {pid}" + (" --yes" if direct else ""),
    }
    # subset preview when --without given
    if "--without" in args:
        i = args.index("--without")
        wl = [x for x in args[i + 1].split(",") if x] if i + 1 < len(args) else []
        pruned = set(wl)
        changed = True
        while changed:
            changed = False
            for m in members:
                if m not in pruned and m != pid and set(depends_in[m]) & pruned:
                    pruned.add(m)
                    changed = True
        plan["subset_preview"] = {"final": [m for m in members if m not in pruned], "pruned": sorted(pruned)}
        plan["suggested_command"] += f" --without {','.join(wl)}"
    shutil.rmtree(src, ignore_errors=True)
    if "--json" in args:
        print(_json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    print(f"[plan] {pid} v{plan['version']} (compat {plan['compat']}) — trust: {plan['trust']}")
    print(f"[plan] disclosure: {plan['disclosure']}")
    print(f"[plan] baseline (always installed): {pid}" + (f" — {menu.get(pid, '')}" if menu.get(pid) else ""))
    for o in plan["optional"]:
        pulls = f" — pulls: {', '.join(o['pulls'])}" if o["pulls"] else ""
        print(f"[plan]   optional: {o['id']}" + (f" — {o['summary']}" if o["summary"] else "") + pulls)
    if plan["connectors"]:
        print("[plan] connectors (ride the package): " + ", ".join(f"{c['name']} ({c['kind']})" for c in plan["connectors"]))
    if "subset_preview" in plan:
        sp = plan["subset_preview"]
        print(f"[plan] subset preview: final {', '.join(sp['final'])}; pruned {', '.join(sp['pruned'])}")
    print(f"[plan] suggested: {plan['suggested_command']}")
    return 0


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "plan":
        return do_plan(sys.argv[2] if len(sys.argv) > 2 else "", sys.argv[3:])
    if cmd == "install":
        return do_install(sys.argv[2] if len(sys.argv) > 2 else "", sys.argv[3:])
    if cmd == "uninstall":
        return do_uninstall(sys.argv[2] if len(sys.argv) > 2 else None, sys.argv[3:])
    if cmd == "list-remote":
        return do_list_remote()
    if cmd == "migrate":
        return do_migrate(sys.argv[2] if len(sys.argv) > 2 else None, sys.argv[3:])
    if cmd == "upgrade":
        return do_upgrade(sys.argv[2] if len(sys.argv) > 2 else None, sys.argv[3:])
    _led = _load_ledger()
    _orphans = []
    if os.path.isdir(MIGRATIONS_DIR):
        for d in sorted(os.listdir(MIGRATIONS_DIR)):
            if d == "pending.json" or not os.path.isdir(os.path.join(MIGRATIONS_DIR, d)):
                continue
            if not os.path.exists(os.path.join(PLUGINS_DIR, "domains", d)) and _led.get(d, {}).get("kind") != "teardown":
                _orphans.append(d)  # staged dormant PKG marks presence; absent package + no teardown = orphan residue
    for k in _orphans:  # self-healing: migrate-kind entries die with the package; residue gets mechanically swept too
        _led.pop(k, None)
        _pkg_dir = os.path.join(MIGRATIONS_DIR, k)
        try:
            _pm = parse_pkg(os.path.join(_pkg_dir, "PKG.yaml")) if os.path.isdir(_pkg_dir) else None
        except ValueError:
            _pm = None
        if _pm:
            import wikilib as _wl
            _members = set(str(m) for m in (_pm.get("members") or []))
            if os.path.isdir(COMMANDS_DIR):
                for d in sorted(os.listdir(COMMANDS_DIR)):
                    _fm = os.path.join(COMMANDS_DIR, d, "SKILL.md")
                    if os.path.exists(_fm):
                        _own = _owner_list(_wl.parse_frontmatter(open(_fm, encoding="utf-8").read()).get("owner"))
                        if _own and _own[0] in _members:
                            shutil.rmtree(os.path.join(COMMANDS_DIR, d))
                            _sk = os.path.join(SKILLS_DIR, d)
                            os.path.isdir(_sk) and shutil.rmtree(_sk)
            for c in _pm.get("connectors") or []:
                _cd = os.path.join(CONNECTORS_DIR, str(c.get("name")))
                if os.path.isdir(_cd):
                    shutil.rmtree(_cd)
                _sk = os.path.join(SKILLS_DIR, str(c.get("name")))
                if os.path.isdir(_sk):
                    shutil.rmtree(_sk)
        shutil.rmtree(_pkg_dir, ignore_errors=True)
        _journal("sweep", f"{k} orphaned package state auto-swept (package absent, residue cleaned)")
    if _orphans:
        _save_ledger(_led)
        _banner_set(_led)
        print(f"[sweep] orphaned migration state removed: {', '.join(_orphans)} (package no longer installed)")
    if _led and cmd:
        _ps = "; ".join(f"{k} {v.get('from', '?')}->{v.get('to', '?')}" for k, v in sorted(_led.items()))
        print(f"[pending] SEMANTIC MIGRATIONS OUTSTANDING: {_ps} — kernel migrate <pkg>; validate stays red until cleared")
    plugins, errors = load_plugins()
    pkgs = load_packages(errors)
    if cmd == "pkg":
        if errors:
            for e in errors:
                print(e)
            return 1
        do_pkg_ls(pkgs, plugins)
        return 0
    if cmd == "residual":
        return do_residual(sys.argv[2] if len(sys.argv) > 2 else None, pkgs)
    if cmd == "ls":
        do_ls(plugins)
        if errors:
            print(f"[warning] {len(errors)} manifest load errors — run validate for details")
        return 0
    if cmd == "audit":
        for e in errors:
            print(e)
        return do_audit(plugins, sys.argv[2] if len(sys.argv) > 2 else None)
    if cmd not in ("validate", "inject", "registry", "deploy", "all"):
        print(__doc__)
        return 2
    scope = None
    if len(sys.argv) > 3 and sys.argv[2] == "--scope":
        scope = sys.argv[3]
        if scope not in pkgs:
            print(f"[error] --scope {scope}: no such package (see: kernel pkg)")
            return 1
        members = set(pkgs[scope].get("members") or [])
        plugins = {p: m for p, m in plugins.items() if p in members}
    warns = []
    validate(plugins, errors, scope=scope, warnings=warns)
    if scope:
        print(f"[scope] bindings/bridges/package checks skipped — single-package mode over {scope} (full-graph disciplines run where the full graph lives)")
    else:
        validate_bindings(plugins, errors)
        validate_bridges(plugins, errors)
        validate_packages(plugins, pkgs, errors, warns)
    for k, v in sorted(_led.items()):
        errors.append(f"[error] pending semantic migration {k} {v.get('from', '?')}->{v.get('to', '?')} — kernel migrate {k} --clear; mechanical blessing withheld (tri-face warning)")
    for w in warns:
        print(f"[warning] {w}")
    for e in errors:
        print(e)
    if errors:
        print(f"[result] validation failed ({len(errors)} errors) — mechanical actions blocked")
        return 1
    label = f"package {scope}" if scope else f"all {len(plugins)} plugins"
    print(f"[validate] {label} passed (fields / id match / deps exist / acyclic / command bindings / usage routes / bridges)")
    if cmd in ("inject", "all"):
        if not do_inject(plugins):
            return 1
        if not do_check_inject(plugins):
            return 1
        if not do_cmd_inject(plugins):
            return 1
    if cmd in ("registry", "all"):
        if not do_registry(plugins):
            return 1
    if cmd in ("deploy", "all"):
        if not do_deploy():
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
