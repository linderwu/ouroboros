---
name: ouroboros
description: "Ouroboros — Transform project repo(s) into Trivium-aligned multi-repo structure: raw/ (evidence), repos/ (code), graphify/ (bridge), wiki/ (decisions + procedural architecture), spec/ (blueprint)"
---

# Ouroboros (Trivium v2.4)

Transform any project (single repo or multi-repo workspace) into a Trivium-aligned knowledge structure. Named for the snake that consumes itself to be reborn — every codebase becomes its own auditable knowledge graph.

## Trivium-aligned structure

```
workspace/
  raw/            # Evidence Layer (Grammar / What) — immutable, append-only
                   #   PM specs, meeting notes, discussion records, external refs
                   #   NOT code. Pure inputs and references.
  repos/          # Code Layer — actual source repositories
                   #   One or more code repos (single or multi-repo projects)
                   #   What runs in production; where edits happen
  graphify/       # Connection Bridge (Logic / How bridge)
                   #   Function-level graph + cross-entity relations
                   #   Bridges repos/ ↔ wiki/ ↔ spec/
                   #   Bridges multi-repo relationships
  wiki/           # Rhetoric Layer (Why + procedural architecture)
                   #   Curated, PR-reviewed. NOT auto-generated.
                   #   Wiki pages cite evidence via [[raw/YYYY-MM-DD-...]] wikilinks
                   #   There is NO wiki/raw/ — raw/ is the single evidence source.
    entities/     #   actors (services, modules, deps)
    concepts/     #   design decisions, tradeoffs
    patterns/     #   runtime experience, debug clues
    comparisons/  #   option comparisons
    index.md      #   entry point
    SCHEMA.md     #   format spec
  spec/           # OpenSpec (Logic / How construction blueprint)
                   #   Per-module contracts, API schemas, data flow
```

## Trivium Philosophy (updated)

| Layer          | Trivium    | Role                                        | Mutability         |
|----------------|------------|---------------------------------------------|--------------------|
| `raw/`         | Grammar    | **Sole** canonical evidence layer — original inputs (PM spec, meeting notes, external refs, logs) | Immutable, append-only |
| `repos/`       | —          | Actual code (production source of truth)    | Mutable (via git) |
| `graphify/`    | Logic      | Connection bridge — relations               | Read-only output    |
| `wiki/`        | Rhetoric   | Decisions + procedural architecture + links | Curated via PR      |
| `spec/`        | Logic      | Construction blueprint / contract           | Mutable (via PR)    |

**Canonical evidence rule**: `raw/` is the **single canonical evidence layer** in the system.
There is **no `wiki/raw/`**. Wiki pages that need to cite evidence use `[[raw/YYYY-MM-DD-source-type]]` wikilinks directly. There is exactly one place where evidence lives, exactly one place where it can be appended, and exactly one place where it can be read as the source of truth.

**Key shifts from prior version:**
- `raw/` is now **evidence layer**, not code. Real code lives in `repos/`.
- `wiki/raw/` was previously a parallel evidence layer; this is **removed in v2.4.1** to eliminate double-truth confusion.
- `wiki/` now also captures **procedural architecture** (how modules relate, call graph narratives, runbook-level descriptions) via wikilinks — but wiki is still not the source of truth for code or evidence.
- `graphify/` is explicitly the **connection bridge** — it links wiki entries, code, and specs across repos.
- `repos/` supports **multiple repositories** (frontend / backend / shared-types / etc).

## Question Routing

| You ask                              | Look in                                  |
|--------------------------------------|------------------------------------------|
| 為什麼這樣設計 / 當初決策是什麼       | `wiki/concepts/`                         |
| 這個 module 跟誰連動 / call graph     | `graphify/` + Graphify MCP (`find_dependents`) |
| API schema / 介面契約                | `spec/` (OpenSpec)                       |
| 程式碼在哪 / 怎麼改                  | `repos/<repo>/`                          |
| 證據來源 / 會議紀錄 / 外部參考       | `raw/`（唯一 evidence layer）            |
| 程序架構 / 模組關係 / 運作脈絡        | `wiki/` + `graphify/`                    |
| 改了會影響誰                          | `graphify/` MCP (`find_dependents`)      |
| 這是 bug 還是故意的                  | `graphify/` → `spec/` → `wiki/` (strict order) |
| 跨 repo 關係                          | `graphify-out/` (merged) + 各自 `graphify/` |
| 當初為什麼這樣寫                      | `wiki/` search                           |

## Workflow: Why → How → What → Update reverse

1. **Wiki** (cross-repo constraints, prior decisions)
2. **Graphify** (impact scope, dependency surface)
3. **OpenSpec** (existing contracts, schemas)
4. **Update**: OpenSpec → Code → Graphify → Wiki (cross-repo decisions only)

## Debugging: How → What → Why

1. **Graphify** query (locate the affected module across repos)
2. **OpenSpec** (compare spec vs reality)
3. **Wiki** search (reason attribution)

## Execution Order (strict — do not reorder)

### Phase 0 — Accept & Inventory

0.1 Accept target path (or workspace root for multi-repo)
0.2 Identify scope: single repo vs multi-repo
0.3 Inventory existing evidence in `raw/` — DO NOT mutate (single canonical evidence layer)

### Phase 1 — Evidence Preservation (raw/ as Evidence Layer)

1.1 Create `raw/` directory structure
1.2 Collect ALL evidence (NOT code) into `raw/`:
   - PM specs and requirements docs
   - Meeting notes, discussion records
   - External reference materials (URLs, papers, vendor docs)
   - Raw data dumps, test results, logs snapshots
   - Imported evidence from prior projects
1.3 **Append-only rule**: never overwrite, never rewrite, never delete.
   New evidence → new file with `YYYY-MM-DD-source-type.md` naming.

### Phase 2 — Code Inventory (repos/ as Code Layer)

2.1 Create `repos/<repo-name>/` for each code repository
2.2 Place actual source code here. This is where edits happen.
2.3 `repos/` is the source of truth for code. Git-tracked.
2.4 For multi-repo projects: each repo gets its own subdirectory.
   Shared libraries / types go in their own `repos/<shared>`.

### Phase 3 — Connection Bridge (graphify/ as How Layer)

3.1 Install graphify: `uv tool install graphifyy`
3.2 For each repo in `repos/`, run:
   ```
   cd repos/<repo-name> && graphify . --output-dir ../../graphify/<repo-name>/ --mode deep
   ```
3.3 For multi-repo: also generate merged `graphify-out/` at workspace root
   (cross-repo relationship view)
3.4 Agent reads `graphify/GRAPH_REPORT.md` + `graph.json` per repo
3.5 Proposes wiki entity/concept/pattern candidates

### Phase 4 — Knowledge Curation (wiki/ + spec/)

4.1 Draft `wiki/entities/` — one page per actor (service, module, external dep)
4.2 Draft `wiki/concepts/` — one page per design decision
4.3 Draft `wiki/patterns/` — runtime experience, debug clues
4.4 Draft `wiki/comparisons/` — A vs B tradeoffs
4.5 Use wikilinks to express **procedural architecture**:
   - Module flow: `[[entity-a]] → [[entity-b]] → [[entity-c]]`
   - Runbook: `[[pattern-x]] when [[symptom-y]]; see [[entity-z]]`
   - Cross-repo: `[[repos/frontend/entity]] interacts with [[repos/backend/entity]]`
4.6 Generate `spec/<module>/SPEC.md` (OpenSpec per module)
4.7 Create `wiki/index.md` + `wiki/SCHEMA.md`
4.8 **Open Git PR** for review. NEVER auto-merge.

### Phase 5 — Audit & Maintenance

5.1 Verify `raw/` integrity (append-only, no mutations)
5.2 Verify `repos/` matches production reality
5.3 Re-run graphify when code changes
5.4 Update wiki via PR, never direct push to main

---

## Step 1 - Accept path

```bash
ls -la "$PATH" 2>/dev/null || echo "PATH_NOT_FOUND"
```

Stop if `PATH_NOT_FOUND`. For multi-repo, `$PATH` is the workspace root.

## Step 2 - Create directory structure

```bash
mkdir -p \
  "$PATH/raw" \
  "$PATH/repos" \
  "$PATH/graphify" \
  "$PATH/wiki/entities" \
  "$PATH/wiki/concepts" \
  "$PATH/patterns" \
  "$PATH/wiki/comparisons" \
  "$PATH/spec"

# Multi-repo: pre-create repo dirs if known
mkdir -p "$PATH/repos/repo-a" "$PATH/repos/repo-b" "$PATH/repos/shared"
```

## Step 3 - Populate raw/ with evidence (NOT code)

```bash
# Copy PM specs, meeting notes, external refs into raw/
# Naming: YYYY-MM-DD-source-type.md
# Example:
cp ~/specs/2026-06-pm-spec.md "$PATH/raw/2026-06-22-pm-spec.md"
cp ~/meeting-notes/2026-06-21-team-sync.md "$PATH/raw/2026-06-21-team-sync.md"

# raw/ rules:
#  - immutable once written
#  - no rewrites, no overwrites
#  - new evidence → new file
```

## Step 3.5 - Populate repos/ with actual code

```bash
# Clone or copy real code repos into repos/
git clone https://github.com/org/repo-a.git "$PATH/repos/repo-a"
git clone https://github.com/org/repo-b.git "$PATH/repos/repo-b"
git clone https://github.com/org/shared-types.git "$PATH/repos/shared"

# OR copy existing local repo:
cp -r /path/to/existing/code "$PATH/repos/repo-a"
cd "$PATH/repos/repo-a" && git init && git add . && git commit -m "initial"

# repos/ rules:
#  - this is where code lives and is edited
#  - git-tracked per repo
#  - graphify reads from here, never writes here
```

## Step 4 - Run /graphify per repo (REQUIRED — How bridge)

```bash
# Per-repo graphify
cd "$PATH/repos/repo-a"
/graphify . --output-dir "$PATH/graphify/repo-a" --mode deep 2>&1 | tail -10

cd "$PATH/repos/repo-b"
/graphify . --output-dir "$PATH/graphify/repo-b" --mode deep 2>&1 | tail -10
```

**Must produce** per repo: `graph.json`, `graph.html`, `GRAPH_REPORT.md`

For multi-repo, also build cross-repo merged graph:
```bash
# After per-repo graphs exist:
graphify merge "$PATH/graphify/" --output "$PATH/graphify-out/" --mode deep
```

If graphify fails → stop and report error. Do not skip.

## Step 4.5 - Agent reads graphify output

Read `graphify/<repo>/GRAPH_REPORT.md` + `graph.json`:
- Identify community clusters (functional blocks)
- Identify hub functions (cross-module edges)
- Identify cross-repo dependencies (from merged graph)
- Propose candidate entities + concepts for wiki

## Step 5 - Draft wiki/ content (Why + procedural architecture)

```
wiki/
  raw/           # Evidence mirror — keep synchronized with /raw
  entities/      # ONE entity per page — services, modules, external deps
  concepts/      # ONE decision per page — why X, alternatives considered, tradeoffs
  patterns/      # Runtime experience — known issues, debug clues, workarounds
  comparisons/   # A vs B comparisons
  index.md       # Entry point — list important pages by category
  SCHEMA.md      # Format spec — frontmatter, wikilinks, page structure
```

**Wiki layer rules:**
- `wiki/entities/`: `[entity-name].md`. Cite repos via `[[repos/repo-a/path/to/file]]`. Cite evidence via `[[raw/YYYY-MM-DD-source-type]]` (single canonical evidence layer — there is no `wiki/raw/`).
- `wiki/concepts/`: `[decision-name].md`. Never delete — mark `status: superseded`.
- `wiki/patterns/`: `[pattern-name].md`. Trigger: post-incident, post-mortem, perf observation.
- `wiki/comparisons/`: `[topic-a]-vs-[topic-b].md`.
- **All pages**: YAML frontmatter + `[[wikilinks]]` between related pages. Evidence citations use `[[raw/YYYY-MM-DD-source-type]]` — never `[[wiki/raw/...]]` (the latter does not exist).
- **Procedural architecture** via wikilinks:
  - Flow: `[[entity-a]] -> [[entity-b]] -> [[entity-c]]`
  - Conditional: `if [[pattern-x]] then [[entity-y]]`
  - Cross-repo: `[[repos/frontend/entity]] ↔ [[repos/backend/entity]]`
- All pages: PR review before merge. NEVER auto-merge.

**Frontmatter schema** (see `wiki/SCHEMA.md`):
```yaml
title: string
type: entity | concept | pattern | comparison | raw
tags: [string]
status: active | superseded | deprecated  # concepts only
created: YYYY-MM-DD
updated: YYYY-MM-DD
```

**Content sections** (by type):
- entity: Summary, Responsibility Boundaries, History, Known Issues, Related Decisions, References
- concept: Summary, Context, Decision, Alternatives Considered, Consequences, References
- pattern: Summary, Symptom, Root Cause, Workaround, Detection, Related, References
- comparison: Summary, Dimensions, When to Choose A/B, Our Context, References
- raw: Source, Date, Content (preserved as-is), Tags, Referenced By

## Step 6 - Generate spec/ (OpenSpec — How 施工藍圖 / contract)

```
spec/
  SPEC.md           # system overview
  [module]/
    SPEC.md         # per-module blueprint
```

```markdown
# [Module Name]

## Summary
One-paragraph description.

## Construction Blueprint
- **Inputs**: ...
- **Outputs**: ...
- **Side effects**: ...
- **API contract**: ...
- **Source**: repos/<repo-name>/path/to/module

## Interface
```[language]
[function signatures / API endpoints]
```

## Data Flow

## Edge Cases
- ...
```

**OpenSpec lives in repo, not wiki.** Hard Trivium boundary.
**OpenSpec cites repos/ paths** — wiki may link to spec, but spec points to actual code in repos/.

## Step 7 - Create index + SCHEMA

```bash
cat > "$PATH/wiki/index.md" << 'EOF'
# Wiki Index

## Entities
EOF
ls "$PATH/wiki/entities/" | grep '\.md$' | sed 's/\.md$//' >> "$PATH/wiki/index.md"

cat >> "$PATH/wiki/index.md" << 'EOF'

## Concepts
EOF
ls "$PATH/wiki/concepts/" | grep '\.md$' | sed 's/\.md$//' >> "$PATH/wiki/index.md"

cat >> "$PATH/wiki/index.md" << 'EOF'

## Patterns
EOF
ls "$PATH/wiki/patterns/" | grep '\.md$' | sed 's/\.md$//' >> "$PATH/wiki/index.md"

cat >> "$PATH/wiki/index.md" << 'EOF'

## Cross-Repo Modules
EOF
ls "$PATH/repos/" >> "$PATH/wiki/index.md"
```

## Step 8 - Open Git PR (REQUIRED)

```bash
cd "$PATH"
git add .
git commit -m "Draft Trivium-aligned wiki + spec + repos inventory"
git checkout -b wiki/initial-curation
git push -u origin wiki/initial-curation
# Open PR via gh or GitHub UI
```

**Why Git PR**: human review gate preserves quality; git history = audit trail; design conflicts surface in PR review queue.

## Output Summary

```
workspace/
  raw/           — Evidence (append-only, NOT code) — single canonical evidence source
  repos/         — Actual code (one or more repos)
  graphify/      — Connection bridge (per-repo + cross-repo)
  wiki/          — Why + procedural architecture (PR-reviewed); cites raw/ via wikilinks
    entities/    —   services, modules, deps (cite repos paths)
    concepts/    —   design decisions
    patterns/    —   runtime experience
    comparisons/ —  option comparisons
    index.md
    SCHEMA.md
  spec/          — OpenSpec (How contract, per module — cites repos/)
```

## Read Workflow (Post-Merge)

```
RD Agent → Wiki Search (Why) + Graphify MCP (How) + repos/ (What via git)
Chatbot RAG → Wiki Search Service (semantic, no summarization)
End User → Chatbot RAG
```

## Multi-Repo Workspace

```
/opt/workspace/
├── raw/               # shared evidence (cross-repo PM specs, meeting notes) — single source of truth
├── repos/             # actual code, one dir per repo
│   ├── frontend/
│   ├── backend/
│   ├── shared-types/
│   └── infra/
├── graphify/          # per-repo graphs
│   ├── frontend/
│   ├── backend/
│   └── shared-types/
├── graphify-out/      # merged cross-repo graph (NOT in any single repo)
├── wiki/              # shared wiki (cross-repo concepts + patterns); cites raw/ via wikilinks
│   ├── entities/      # entity pages cite repos paths
│   ├── concepts/
│   ├── patterns/
│   └── comparisons/
└── spec/              # per-repo + cross-repo OpenSpec
```

**Wiki entries should explicitly link across repos** when describing architecture:
- `[[repos/frontend/src/auth]]` interacts with `[[repos/backend/src/auth-service]]`
- Cross-repo decisions live in shared `wiki/concepts/`

## Constraints

- **Step 4 (/graphify) is MANDATORY — do not skip**
- **Wiki content MUST go through PR review — never auto-merge**
- Do NOT modify `raw/` after creation (append-only; `raw/` is the single canonical evidence layer)
- Do NOT create `wiki/raw/` or any parallel evidence layer — wiki pages must cite `raw/` directly via wikilinks
- Do NOT put code in `raw/` — code belongs in `repos/`
- `repos/<repo>/` is the only place to edit code
- `wiki/concepts/`: never delete, mark superseded instead
- OpenSpec lives in repo, not wiki (hard boundary). OpenSpec cites `repos/` paths.
- Graphify output is read-only — never modify wiki from Graphify output, always via PR
- Use Traditional Chinese for wiki unless source is clearly English

## Versioning

- v2.0: Initial Trivium 4-layer
- v2.1: Wiki CURATED + wikilinks
- v2.2: OpenSpec separation from wiki
- v2.3: Git-native Knowledge Wiki + mandatory PR review
- **v2.4: Evidence Layer (raw), Code Layer (repos), Connection Bridge (graphify), Procedural Architecture in wiki, multi-repo support**
- **v2.4.1: Removed `wiki/raw/` entirely. `raw/` is the single canonical evidence source. Wiki pages cite `raw/` via `[[raw/...]]` wikilinks — no parallel evidence layer.**
