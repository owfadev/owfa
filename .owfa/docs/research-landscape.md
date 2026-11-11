# Comparable Products and Paradigms Survey: Getting Information In and Out

> Development-side research archive (2026-09-16, distilled from four parallel web-research tracks: official docs / papers / HN·Reddit communities): the market benchmarking basis for vault-wiki (inspired by llm-wiki). Not a runtime artifact of any instance. Unified four-question frame: **how information composition (ingestion) works, how information retrieval (output) works, success points and attractions, problems and flaws**.

## 1. Lineage origins: llm-wiki and OKF

### 1.1 Karpathy's "LLM Wiki" gist (2026-04-04)

- **What it is**: a GitHub Gist published by Karpathy (a pure idea file, no code, designed to be pasted directly to any agent). Core claim: RAG (including NotebookLM, ChatGPT file uploads) "rediscovers knowledge from scratch" on every question, with no compounding; the alternative is letting an LLM incrementally build and maintain a persistent markdown wiki—"knowledge is compiled once and then kept current, not re-derived on every query", i.e. the opposition of **distill-at-write vs. retrieve-at-query**. Humans abandon wiki maintenance because the burden grows faster than the value, while an LLM does not tire and never forgets to update cross-references. Intellectually traceable to Bush's 1945 Memex.
- **Structure**: three layers—raw sources (human-curated, immutable, LLM read-only) → the wiki (LLM full-authority generation and maintenance) → the schema (CLAUDE.md/AGENTS.md conventions); three operations Ingest/Query/Lint; two special files index.md and log.md. (The gist is deliberately abstract; the folk "raw/wiki/output three-folder" account is second-hand embellishment.)
- **Success points**: measured token gains are dramatic (an r/ClaudeAI case of 47,450 → 360 tokens, plus a 71.5× case); pure files, zero dependencies, Obsidian-compatible; knowledge compounding.
- **Flaws**: initial compilation and ongoing maintenance are themselves token-hungry (2000 md files will blow the rate limit, per a skeptical r/ObsidianMD thread); errors and hallucinations from the distillation stage solidify into the wiki; the barrier is high for ordinary users.
- **Derivative implementations**: nvk/llm-wiki (1.3k★, command set + AGENTS.md, self-described as inspired by Karpathy), nashsu/llm_wiki (19.6k★, Tauri desktop app + knowledge graph), the awesome-llm-wiki list, etc. autoresearch (karpathy's official repo, ~96k★) is ML-training automation, unrelated to wikis, but the community often conflates the derived "loop research-archive" pattern with it in circulation.

### 1.2 Google OKF—Open Knowledge Format (2026-06-13)

- **What it is (verified)**: the Google Cloud official blog post "How the Open Knowledge Format can improve data sharing" + the spec repository (GoogleCloudPlatform/knowledge-catalog/okf/SPEC.md, started at v0.1, now v0.2). Self-positioned: **formalizing the llm-wiki pattern into a portable, interoperable open format**; the blog text cites Karpathy, acknowledging the intellectual origin.
- **Contract**: "Just markdown + Just files + Just YAML frontmatter"; one file per concept, **the file path is the identity**; the only required field is `type`, with title/description/resource/tags/timestamp conventional; reserved file names index.md and log.md; markdown links woven into a relationship graph. Three principles: minimally opinionated / producer-consumer independence / **format, not platform** (no binding to cloud, database, model, or agent framework).
- **Ingestion**: the reference implementation's enrichment agent walks BigQuery datasets drafting a concept doc per table, with a second LLM pass adding citations/schema/join paths. **Retrieval**: static single-file HTML graph visualization (no backend).
- **Reception**: positive but exploratory—vs-RAG/GraphRAG comparisons, enterprise agent-knowledge-layer discussions, developers building their own supersets, r/LLMDevs debates over applicability boundaries. Note the acronym collision with the Open Knowledge **Foundation** (CKAN, government open-data portals; a very distant lineage).
- **Convergence with this project's `01-okf.md`** (independent distillation on both sides, same Karpathy lineage):

| Contract point | Google OKF | This project's 01-okf.md v0.2 |
|---|---|---|
| `type` required, value set decided instance-side | ✓ | ✓ (closed via registry) |
| Reserved names index.md / log.md | ✓ | ✓ (+ exemption duties) |
| One concept one file, path as identity | ✓ | ✓ (wikilink full name = path) |
| Minimal YAML, complex structures not accepted | ✓ | ✓ (top-level scalars / block lists / one-level block mappings) |
| Producer-consumer decoupling | producer-consumer independence | SASU-L zero priors |
| Trust and provenance | **none** | **trust four fields + unified actor format + trust-level derivation** (a differentiated strength) |

### 1.3 kepano/obsidian-skills (2026-01)

The official agent skills repository from Obsidian CEO kepano, following the Agent Skills open specification (agentskills.io), now about 48.4k★. Six skills today: obsidian-markdown / obsidian-bases / json-canvas / obsidian-cli / defuddle / knap (the last added later; the five skills recorded in internal archives lack it). Pure-files philosophy: agents read and write Markdown/Bases/JSON Canvas directly. Flaw: community testing of obsidian-cli 1.12 found 13 silent failures (22.8% of 57 scenarios exiting 0 yet returning empty/wrong data), spawning third-party remediation skills.

### 1.4 Nearby references

- **DeepWiki** (Cognition): freely AI-generates conversable documentation for any public GitHub repository; controversies: generating without maintainer consent + questioned accuracy.
- **OKFN/CKAN**: a dataset publication and discovery system aimed at government/institutional open data; distant lineage from agent personal knowledge bases.

## 2. AI-native knowledge-base products (consumer PKM)

| Product | Ingestion (composition) | Retrieval (search) |
|---|---|---|
| NotebookLM | sources uploaded per notebook (PDF/Docs/URL/audio-video), near-zero processing at write | source-grounded RAG with inline citation markers; Audio Overview podcast-style summaries |
| Notion AI | the workspace is the corpus + connectors syncing Slack/Jira/Drive | cross-page + connector-data Q&A with source links |
| Mem | quick capture, AI auto-tagging and association, zero manual organization | Smart Search semantic retrieval + Related Notes auto-surfacing |
| Reflect | daily notes + web clipping + voice transcription; AI auto-adds entity backlinks | backlink-network browsing + full-text search + built-in AI chat |
| Tana | meeting transcription / AI capture; supertags give nodes a schema, processing fields at write | live searches as dynamic aggregate views + Ask AI |
| Reor | points at an md directory, local chunking + embeddings stored in LanceDB at write | local semantic search + related notes + local-LLM RAG, fully offline |
| Khoj | syncs markdown/PDF into an index (embedded at write), open-source self-hosted | natural-language search + sourced Q&A, backend can plug into Ollama |
| Obsidian plugins | Smart Connections embeds everything locally with continuous increments | sidebar live related notes + semantic search; Copilot Vault QA with citations |
| MyMind | one-click save, AI auto-tagging + summarization, zero organization | smart search (keyword + semantic) |

**Success points**: NotebookLM's grounding + traceable citations are seen as the anti-hallucination benchmark, and Audio Overview was the breakout catalyst (third-party aggregate tallies claim over 30 million users; second-hand figures, for reference only); Notion leans on existing users with zero migration cost; Mem's search reputation and $23.5M funding; Reor's Show HN 411 points plus kepano's public endorsement that "plain markdown files beat databases"; Khoj/Obsidian plugins feed on the "data never leaves the machine + reuse your existing vault" selling points.

**Flaws** (documented per product): NotebookLM still has fake citations / mismatched quotes, poor PDF table recognition, serious inaccuracy past roughly 500k characters, and a long-lamented source-count cap; Notion's results depend heavily on workspace organization quality, questions against databases often fail retrieval, and paywall changes sparked discontent; Mem bled users to long-standing bugs before 2.0, and the cost of automatic organization is that the classification logic is not your own; Tana has a steep learning curve; Reor's author concedes "RAG is fairly naive" and the local 7B model is a hard ceiling; Khoj has a high deployment barrier, and its "self-hosted" marketing clashes with its OpenAI dependency; Obsidian plugins' Vault QA requires full embedding first, and semantic association is poor in multilingual vaults; MyMind's inaccurate auto-tags make things harder to find again.

**Spectrum summary**: on one end, **heavy processing at write** (Mem/Reflect/MyMind auto-tagging; Reor/Smart Connections embedding at write); on the other, **near-zero processing, computed at query** (NotebookLM/Notion/Tana live search). Processing at write buys retrieval speed but solidifies errors—inaccurate auto-tags are the common failure point; processing at query keeps the original text pure but is costly and slow. "RAG Q&A with clickable citations" has become a standard selling point, while "fake citations" remain every vendor's shared crack in trust.

## 3. Agent memory systems

### 3.1 Product level

- **ChatGPT Memory**: saved memories (entries written by the bio tool and injected into the system prompt) + reference chat history (per Embrace The Red's hands-on analysis: it does not retrieve historical conversations but is a continuously aggregated longitudinal profile—preference inferences, topic summaries, the raw text of roughly the last 40 user messages, device/intent metadata—injected wholesale, pure write-time processing). Successes: zero-config on by default, deletable item by item; flaws: the profile area is unauditable and uneditable by the user, capacity is small (Plus fills up quickly), the profile can be contaminated by conversation injection, and it is unavailable in Europe over GDPR concerns.
- **Claude (Projects / memory tool / the 2026-08 unified memory)**: on the product side, chat and Cowork share memory, partitioned per Project, on by default. On the API side, the memory tool is **client-side file-based memory**: six commands operate on a `/memories` directory, Claude autonomously decides what to record, the system prompt enforces "look at the memory directory before doing anything", and it persists to disk continuously under the assumption that "the context may be reset at any moment". Files are memory—a minimal mental model; flaws: the application side must implement its own handler and guardrails, with no built-in deduplication/conflict resolution.

### 3.2 Framework level (star counts as of 2026-09)

- **Mem0 (65.4k★)**: two-stage extract-consolidate—on `add()` an LLM extracts fact-level memories, and a decision engine issues ADD/UPDATE/DELETE/NOOP against old memories (OSS v3 has simplified to ADD-only; corrections require explicit update/delete). Retrieval fuses four signals (vector + keyword + entity boost + temporal intent). Official numbers: LoCoMo 92.5, tokens about 1/3–1/4 of full context. Flaws: extraction is lossy and non-deterministic, details are lost at "factualization"; HN critics say it "only stores and retrieves, learns no patterns".
- **Zep / Graphiti (30.9k★)**: incrementally builds a **temporal knowledge graph**, bitemporal—facts carry valid/invalid time windows, outdated facts are "invalidated rather than deleted", episodes retained permanently for provenance. Retrieval is hybrid (embeddings + BM25 + graph traversal) with graph-distance reranking, supporting "current truth / any historical point-in-time" queries. Flaw: multiple LLM calls per episode make ingestion latency and cost high.
- **Letta (formerly MemGPT, 24.8k★)**: OS-style layering—context as RAM, external storage as disk; memories are named blocks that the agent self-edits via tool calls; sleep-time compute reflects in the background during idle periods and rewrites shared memory blocks. Key experiment: **Letta Filesystem merely stores conversation history in files and scored 74.0% on LoCoMo, beating most dedicated memory stores**. Flaws: many abstraction layers, a steep learning curve, and self-editing can corrupt memory.
- **MemOS (11.4k★)**: the paper unifies three memory states via MemCube (plaintext / activated KV-cache / parameterized LoRA) + a Memory Scheduler for dispatching; the open-source landing is a multi-Cube knowledge base with traces/policies/world-models layering, while the three-state transitions mostly remain on paper. The greatest academic ambition, concept-heavy, lacking third-party validation.
- **Cognee (30.7k★)**: an ECL pipeline (Extract-Cognify-Load) into knowledge graph + embeddings, including session distillation and ontology-constrained deduplication; `recall` auto-routes hybrid graph/vector retrieval. The code knowledge graph is the differentiator; LLM graph extraction is the cost bottleneck—an independent evaluation rated extraction quality 2.97/5.
- **LangMem / LangGraph memory**: splits memory psychologically into semantic/episodic/procedural; the distinctive part is the procedural channel hot-updating the system prompt. Clear concepts and the broadest tutorial ecosystem; but it is more of an SDK—no graph, no temporality, schemas entirely user-designed.

### 3.3 Academic side

MemGPT (arXiv:2310.08560, the paradigm's origin); A-MEM (arXiv:2502.12110, Zettelkasten-style atomic cards with LLM-generated links/tags, where adding new memories triggers dynamic reorganization of the old memory network); HippoRAG 2 (ICML 2025, modeled on hippocampal indexing theory, builds a KG offline + completes multi-hop association with a single graph traversal at query time).

### 3.4 The LoCoMo benchmark dispute (a trust-crisis specimen)

The Mem0 paper reported Zep at 65.99% → Zep published "Lies, Damn Lies, & Statistics" alleging misconfiguration, self-reporting 84% → Mem0's CTO counter-sued (denominator-exclusion manipulation, secretly altered prompts; across 10 reruns Zep got only 58.44%±0.20). **Third-party meta-analysis**: about 6.4% of LoCoMo questions have corrupted ground truth; the GPT-4o-mini judge pass rate is 62.81%; **the full-context baseline of about 73% overtakes most dedicated memory stores**; the same system scores anywhere from 38%–92% depending on who does the evaluating. Net conclusion: static memory leaderboards are basically untrustworthy; evaluation must be self-built and carry full-context/grep baselines—external corroboration of this project's ruling to "validate by use, no matrix testing".

## 4. Multi-agent collaboration paradigms

**A four-way split of shared substrates**: message streams (AutoGen, OpenAI Agents SDK's items) · state/checkpoints (LangGraph, ADK) · vector memory stores (CrewAI) · **files and documents** (Anthropic appendix recommendation, Manus, Claude Code, MetaGPT). vault-wiki belongs to the files school.

**Four highlights**:

1. **Anthropic's multi-agent research system** (2025-06 blog): orchestrator-worker, with embedded scaling rules (1 subagent for simple facts / 10+ for complex research); context isolation—each subagent carries a clean context, and the lead receives only compressed results. **The official appendix explicitly recommends: subagent outputs are written to the filesystem, with only lightweight references passed back**—avoiding large outputs being copied layer upon layer through conversation history. Opus 4 lead + Sonnet 4 workers beat a single agent by 90.2%, with token usage explaining 80% of performance variance; costs: multi-agent runs about 15× tokens, vague instructions cause subagent collisions and duplicated work, non-determinism is hard to debug, and the company states outright that it does not fit tightly coupled tasks that need shared context.
2. **Claude Code**: memory fully file-based—layered CLAUDE.md (enterprise/project/user levels), skills as SKILL.md folders with on-demand progressive disclosure, subagents themselves being md definitions. A subagent's isolated context sees only task + constitution + git snapshot, with only the final summary flowing back. Official warning: a bloated constitution gets ignored (every line must pass the "would removing it break something?" test).
3. **Manus context engineering**: **the filesystem as the ultimate context**—unbounded, naturally persistent, directly operable by the agent; todo.md plans externalized and rewritten repeatedly, fighting lost-in-the-middle; append-only context with a stable prefix preserves KV-cache ($0.30 cached vs $3.00 uncached/MTok, 10×). Admitted flaws: long-context performance decay, and repeated traces leading the model to imitate old patterns.
4. **OpenAI Agents SDK**: a session is an items list; Session prepends before the run / appends after, and multiple agents can share a session and see each other; handoff by default **broadcasts the full history** (trimmable with a filter), and input_type passes only small metadata. Flaws: misplaced guardrail responsibilities, and token bloat over long chains requires building your own filters.

**Quick sketches**: AutoGen's group chat is shared memory—every message visible to all—with the official advice "single agent first, a team only when collaboration is truly needed"; CrewAI has the most explicit consolidation strategy (similarity >0.85 triggers LLM arbitration of keep/update/delete, ≥0.98 dedup, composite scoring semantic 0.5 / recency 0.3 / importance 0.2); LangGraph runs dual-track checkpointer (session snapshots) + Store (cross-thread shared KV), with accumulating checkpoints pushing latency up; MetaGPT (70.4k★) encodes SOPs, its shared memory being structured document artifacts flowing through (user stories → PRD → design → code), at the cost of process rigidity; MCP handles tool externalization (donated to the Linux Foundation, a de facto standard), complementary to the wiki's handling of shared memory between agents; Google A2A takes the **no shared memory** route (Agent Card discovery + task/artifact passing, protecting IP), while the same company's ADK keeps session state as a KV dictionary with long-term memory in a Memory Bank—default InMemory vanishes on restart, and storing the raw full history "may drown the model".

## 5. Side-by-side comparison

| Representative | Memory substrate | Ingestion (composition) | Retrieval (search) | Trust/provenance |
|---|---|---|---|---|
| llm-wiki (Karpathy) | md files | LLM distills at write, raw read-only | index + browsing | none (log.md records operations) |
| Google OKF | md + YAML | enrichment agent drafts + second pass | static graph visualization | timestamp by convention, no trust model |
| **vault-wiki** | **md + YAML** | **explicit command-discipline composition (map/save), raw=vault append-only** | **hot cache → index → grep → body, progressive disclosure** | **trust four fields + trust-level derivation** |
| NotebookLM | source files + chunks | near-zero processing at write | query-time RAG + citation markers | inline citations (occasionally fake) |
| Mem0 | SQL + vector + entities | LLM extraction + decision-engine consolidation | four-signal fusion | no temporal semantics |
| Zep/Graphiti | temporal knowledge graph | incremental entity-edge extraction + bitemporal | hybrid retrieval + graph reranking | bitemporal (strongest temporal provenance) |
| Letta | memory blocks + files | agent self-editing + idle-time reflection | core blocks resident + archival vectors | none |
| ChatGPT Memory | proprietary profile | aggregated and injected at write | no standalone retrieval layer | unauditable (weakest) |
| Anthropic multi-agent | message streams + files | orchestrator consolidates; writing to files and returning references recommended | context isolation + summary backflow | a dedicated citation-backfill agent |
| Manus | filesystem | append-only + externalized todo.md | full retention + KV-cache | reconstructable (URL/path pointers) |

## 6. Shared successes and shared flaws

**Successes**: ① compounding—"compile once, keep fresh" replacing "re-derive every time" (llm-wiki, Mem0's selective updates, Zep's invalidate-not-delete); ② verifiable citations as a trust selling point (NotebookLM's markers, Notion's links); ③ pure files + path as identity (OKF's format-not-platform, kepano's argument, the Letta Filesystem experiment, Claude's memory tool in the same direction); ④ progressive disclosure controlling tokens (index → body, skills, Audio Overview); ⑤ zero-config on-by-default lowering the mass-market barrier (ChatGPT Memory).

**Flaws**: ① extraction is lossy and non-deterministic (the common ailment of Mem0/Zep/Cognee, not reproducible); ② distilled errors solidify—hallucinations in a wiki have no natural correction loop (llm-wiki's biggest soft spot; check/lint is the lifeline); ③ fake citations and audit gaps (NotebookLM's mismatched quotes, ChatGPT's uneditable profile); ④ token costs (multi-agent 15×, wiki maintenance fees, full-embedding fees); ⑤ benchmark arms races detached from real use (the LoCoMo dispute, full-context baselines overtaking); ⑥ the loss of control from automatic organization and the philosophical critique that it "makes thinking passive" (Mem/MyMind).

## 7. Implications for vault-wiki

**Choices already externally validated**: the md pure-files foundation (OKF's three principles, kepano's argument, Letta Filesystem's 74.0%, Claude memory tool's file memory—four independent corroborations); path as identity ↔ the wikilink full-name convention; index.md/log.md reserved names already a lineage convention; the hot cache ≈ Manus's todo.md anti-drift + progressive disclosure; the trust four fields exactly fill the trust layer that both Google OKF and NotebookLM lack; the "validate by use" ruling and the LoCoMo trust crisis corroborate each other.

**Worth borrowing**: Anthropic's "outputs to the filesystem, lightweight references back" can be written explicitly into save/map usage; Zep's "invalidate rather than delete" is isomorphic to trust's stale_after/verified event lists and can strengthen the semantics of "mark stale knowledge, never delete"; Letta's sleep-time compute corresponds to this project's "idle-time log consolidation" (the existing requires-user-consent boundary unchanged); CrewAI's consolidation thresholds prove that save deduplication can be quantified, but mechanizing the numbers risks overfitting.

**Risk warnings**: distilled errors solidifying—check must keep its hard-constraint status; the token cost of wiki maintenance swelling with page count—hot ≤25 entries and index aggregation are the existing gates and need continued watching; **the OKF name collision** (Google Open Knowledge Format / Open Knowledge Foundation)—the full name of `01-okf.md` is undetermined, pending the owner's note; whether to align with Google OKF or explicitly differentiate is a decision point.

## 8. Sources (selected, grouped)

- **Lineage**: Karpathy LLM Wiki gist (gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) · Google OKF blog (cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing) · OKF spec (github.com/GoogleCloudPlatform/knowledge-catalog, okf/SPEC.md) · kepano/obsidian-skills (github.com/kepano/obsidian-skills) · nvk/llm-wiki (github.com/nvk/llm-wiki) · nashsu/llm_wiki (github.com/nashsu/llm_wiki) · token case (r/ClaudeAI 1sfdztg) · hype skepticism (r/ObsidianMD 1sx040s) · CLI silent failures (forum.obsidian.md/t/111169)
- **Knowledge-base products**: NotebookLM (blog.google Audio Overviews; r/notebooklm 1l2aosy) · Notion AI (workflowautomation.net review; r/Notion 1g7gx3h) · Mem (techcrunch 2022-11-10 funding) · Reflect (reflect.app/blog) · Tana (producthunt.com/products/tana) · Reor (news.ycombinator.com/item?id=39372159) · Khoj (github.com/khoj-ai/khoj) · Smart Connections (community.obsidian.md)
- **Agent memory**: Mem0 (docs.mem0.ai/core-concepts/how-it-works; arxiv 2504.19413) · Zep/Graphiti (github.com/getzep/graphiti) · Letta (letta.com/blog/sleep-time-compute; letta.com/research) · MemOS (arxiv 2505.22101; github.com/MemTensor/MemOS) · Cognee (github.com/topoteretes/cognee) · LangMem (langchain-ai.github.io/langmem) · ChatGPT Memory teardown (embracethered.com 2025 chatgpt-how-does-chat-history-memory-preferences-work) · Claude memory tool (platform.claude.com/docs) · the dispute (blog.getzep.com/lies-damn-lies-statistics; github.com/getzep/zep-papers/issues/5; essays.bloo-mind.ai/posts/2026-05-20-mem-eval)
- **Multi-agent**: Anthropic multi-agent system (anthropic.com/engineering/built-multi-agent-research-system) · Claude Code (code.claude.com/docs/en/best-practices; /sub-agents) · Manus (manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) · Agents SDK (openai.github.io/openai-agents-python) · AutoGen (microsoft.github.io/autogen) · CrewAI (docs.crewai.com/concepts/memory) · LangGraph (docs.langchain.com langgraph/persistence) · MetaGPT (github.com/FoundationAgents/MetaGPT; arxiv 2308.00352) · MCP (modelcontextprotocol.io) · A2A (a2a-protocol.org) · ADK (cloud.google.com/blog remember-this-agent-state-and-memory-with-adk)
