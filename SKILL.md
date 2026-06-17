---
name: ouroboros
description: "Transform a project repo into Trivium-aligned 4-layer structure: raw/ (What=Code), graphify/ (How bridge), wiki/ (Why), spec/ (How 施工藍圖)"
---

# Repo Structurer (Trivium v2.3)

Transform any project repo into a Trivium-aligned structure where each layer answers one specific question:

```
repo/
  raw/           # Code — the ONLY What (the finished product)
  graphify/      # How family member: bridge between Wiki (Why) and Code (What)
  wiki/          # Why layer (Git-native, curated via PR)
    raw/         #   證據
    entities/    #   對象
    concepts/    #   為什麼這樣設計
    patterns/    #   How family member: 操作知識 (runtime experience)
    comparisons/ #   對比分析
    index.md
    SCHEMA.md
  spec/          # OpenSpec — How family member: 施工藍圖 (construction blueprint)
```

## Trivium Philosophy

**Trivium** = 中世紀三藝 (Grammar / Logic / Rhetoric). Three knowledge paths converge on the same object.

| Trivium | Trivium System | Question | Layer in this skill |
|---------|----------------|----------|---------------------|
| 文法（rules） | OpenSpec | 「現在規則是什麼？」 | `spec/` |
| 邏輯（how） | Graphify | 「實際上怎麼跑？」 | `graphify/` |
| 修辭（why） | Wiki | 「為什麼這樣設計？」 | `wiki/` |
| (Code) | (Code) | 「成品是什麼？」 | `raw/` |

**Critical correction (v2.3):** How is **a family**, not a single tool.

```
Why (concepts/)              → Design tradeoffs
─────────────────────────────────────────────────
How OpenSpec                 → 施工藍圖 (construction blueprint)
    patterns/                → 操作知識 (runtime experience)
    [[wikilinks]]            → 結構關係 (manual/intentional links)
    Graphify                 → 橋 (Why ↔ What, automatic/exploratory)
─────────────────────────────────────────────────
What Code                    → The only finished product
```

**Boundaries (each layer does NOT do):**
- Wiki does NOT hold OpenSpec (follows repo git)
- Wiki does NOT hold call graph (Graphify owns it)
- Wiki does NOT replace git history (git tracks who changed what; wiki tracks why)
- Graphify does NOT modify Wiki pages (read-only, may pollute curated knowledge)
- OpenSpec does NOT cross repo (single-repo contract layer)

## Question Routing

Before drafting content, classify the question:

- 「為什麼這樣設計？」 / 「設計理由」 → **Wiki Search Service** (`wiki/`)
- 「誰依賴誰」 / 「trace」 / 「call graph」 → **Graphify MCP** (`graphify/`)
- 「現在規則是什麼」 / 「API schema」 / 「合約」 → **CI API / OpenSpec** (`spec/`)
- 「這是 bug 還是故意的」 → Graphify MCP → CI API → Wiki Search (順序不可顛倒)
- 「改了會影響誰」 → Graphify MCP (`find_dependents`)
- 「當初為什麼這樣寫」 → Wiki Search Service

## Workflow Order

**Development: Why → How → What → Update reverse**

1. 先看 Wiki（跨 repo 架構限制）
2. 再跑 Graphify（影響範圍）
3. 最後讀 OpenSpec（既有合約）
4. 更新順序：OpenSpec 先 → Code → Graphify 驗收 → Wiki 補（僅跨 repo 決策）

**Debugging: How → What → Why**

1. Graphify query（定位）
2. OpenSpec 對照（規格 vs 實際）
3. Wiki Search（設計理由歸因）

## Graphify

**Graphify** (package: `graphifyy`, double-y) — https://github.com/safishamsi/graphify

Turns any codebase into a queryable knowledge graph. Run `/graphify .` and get:
- `graph.html` — interactive node graph
- `graph.json` — function-level nodes + call/import edges
- `GRAPH_REPORT.md` — community detection, hub functions, cross-module insights

**Shared Workspace (跨 repo):** `/opt/graphify-workspace/`
```
repos/           # All repos master (read-only clone)
  frontend/
  backend/
  shared-types/
graphify-out/    # Cross-repo merged graph (NOT inside any single repo)
  graph.json
  graph.html
  GRAPH_REPORT.md
```

The graphify layer in this skill is the **per-repo slice**. For cross-repo queries, use Graphify MCP.

## Trigger

Use when asked to "structure a repo", "transform to 4-layer format", "Trivium-fy a repo", "prepare repo for knowledge management", or similar.

## Execution Order (Strict — Do Not Reorder)

**Phase 1 — Evidence Preservation (What):**
1. Accept path
2. Create directory structure
3. Copy ALL code to `raw/` (immutable snapshot)

**Phase 2 — How Bridge (Graphify):**
4. Scan function-level relationships with `/graphify` → build relationship network in `graphify/`
5. Agent reads graph output → proposes candidate entities and concepts for the wiki

**Phase 3 — Knowledge Curation (Why Wiki + How 施工藍圖 Spec):**
6. Draft `wiki/` pages (entities, concepts, patterns, comparisons) — curation, not auto-publish
7. Generate `spec/` (OpenSpec construction blueprint per module)
8. Create `wiki/index.md` and `wiki/SCHEMA.md`
9. Open Git PR for human review (NEVER auto-merge — wiki is curated knowledge)

## Workflow

### Step 1 - Accept path

If no path given, ask for it. Confirm it exists.

```bash
ls -la "$PATH" 2>/dev/null || echo "PATH_NOT_FOUND"
```

If `PATH_NOT_FOUND`, stop and ask for a valid path.

### Step 2 - Create directory structure

```bash
mkdir -p \
  "$PATH/raw" \
  "$PATH/graphify" \
  "$PATH/wiki/raw" \
  "$PATH/wiki/entities" \
  "$PATH/wiki/concepts" \
  "$PATH/wiki/patterns" \
  "$PATH/wiki/comparisons" \
  "$PATH/spec"
echo "Directories created"
```

### Step 3 - Copy original code to raw/ (What layer)

Code is the only finished product. This is the **immutable What** layer.

```bash
cd "$PATH"
rsync -av --exclude='node_modules' --exclude='.git' --exclude='dist' --exclude='build' --exclude='__pycache__' --exclude='.venv' --exclude='target' --exclude='.next' --exclude='*.pyc' --exclude='*.class' --exclude='*.o' ./ "$PATH/raw/" 2>/dev/null || cp -r . "$PATH/raw/"
echo "raw/ done"
```

### Step 4 - Scan function-level relationships with /graphify (REQUIRED — How bridge)

**Graphify is one of the four How family members** — the automatic/exploratory bridge between Wiki (Why) and Code (What).

1. Install graphify (official package: `graphifyy`, double-y on PyPI):

   **Recommended — uv (fastest, isolates environment):**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh 2>&1 | tail -3
   uv tool install graphifyy 2>&1 | tail -5
   ```

   **Alternative — pipx:**
   ```bash
   pipx install graphifyy 2>&1 | tail -5
   ```

   **Alternative — pip:**
   ```bash
   pip install graphifyy --break-system-packages 2>&1 | tail -5
   ```

2. Register the OpenClaw skill:
   ```bash
   graphify install --platform claw 2>&1 | tail -5
   ```

3. Run /graphify from the raw/ directory — this scans every function's calls, imports, and data flow:
   ```bash
   cd "$PATH/raw"
   /graphify . --output-dir "$PATH/graphify" --mode deep 2>&1 | tail -10
   ```

   **Requirements:** Python 3.10+, uv or pipx recommended.

This step MUST produce:
- `graph.json` — every function as a node; edges = calls, imports, data flow
- `graph.html` — interactive visualization
- `GRAPH_REPORT.md` — community clusters, hub functions, cross-module edges

**The wiki and spec layers are derived from graph.json.** If graphify fails, stop and report the error — do not skip this step.

### Step 4.5 — Agent reads graphify output to understand the codebase

**Critical: The agent must read and understand graphify's output before drafting wiki content.**

After /graphify completes, the agent MUST:
1. Read `graphify/GRAPH_REPORT.md` — understand community clusters, hub functions, and insights
2. Read `graphify/graph.json` — understand the full function-level relationship network
3. Identify major functional blocks (communities of functions that work together)
4. Propose candidate entities (services/modules) and concepts (design decisions) for the wiki

### Step 5 - Draft wiki/ content (Why layer — curation, not generation)

**Wiki is the Why layer of Trivium.** The wiki directory follows this structure:

```
wiki/
  raw/           # Evidence (不可變、追加) — 原始輸入：PM 目標、外部參考、log、事故記錄
  entities/      # Actors layer — 跨 repo 服務、模組、系統、外部依賴
  concepts/      # Why layer (寫 code 前) — 設計決策、技術選型、架構取捨
  patterns/      # How family member (寫 code 後) — runtime experience: known issue、debug 線索、workaround
  comparisons/   # Why 的對比 — 多方比較（為什麼選 A 而非 B）
  index.md       # Entry point — 列出重要頁面與分類
  SCHEMA.md      # Format spec — frontmatter、tags、wikilinks、頁面結構
```

**Drafting rules (each layer serves a distinct purpose):**

1. **wiki/raw/** — Evidence layer (immutable, append-only)
   - 原始來源：會議紀錄、外部參考、log、測試結果、事故記錄
   - **Never modify old evidence. Add new files only.**
   - Filename convention: `YYYY-MM-DD-source-type.md`
   - Frontmatter required: `source`, `date`, `created`

2. **wiki/entities/** — Actors layer
   - Each page documents ONE entity (service, module, system, external dependency)
   - Content: 職責邊界、歷史演進、已知問題、相關決策
   - Filename: `[entity-name].md` (e.g. `auth-service.md`)
   - Cross-link to related concepts and patterns via `[[wikilinks]]`

3. **wiki/concepts/** — Why layer (the most valuable)
   - Each page documents ONE design decision or technical choice
   - Content: 為什麼選 X、考慮過哪些替代方案、最終決定、取捨理由
   - **Old decisions are NOT deleted.** If superseded, mark with `status: superseded` in frontmatter and link to the new decision
   - Filename: `[decision-name].md` (e.g. `use-postgres-over-mongo.md`)
   - Cross-link to evidence in `raw/`, related entities, and patterns

4. **wiki/patterns/** — How family member (runtime experience)
   - 系統上線後才浮現的知識：known issue、debug 線索、效能觀察、workaround 背景、incident lessons
   - **Source is runtime, not design-time.** Concepts explain "why this road looks like this"; patterns explain "how to walk it / what pitfalls exist"
   - Filename: `[pattern-name].md` (e.g. `jwt-expiry-edge-bug.md`, `connection-pool-exhaustion.md`)
   - Same format as concepts/ (Markdown + YAML frontmatter + `[[wikilinks]]`)
   - Trigger to add: after debugging a known issue, after on-call incident post-mortem, after observing a performance pattern
   - Cross-link to related entities and concepts

5. **wiki/comparisons/** — Why comparison layer
   - Compare different options, tools, architectures
   - Filename: `[topic-a]-vs-[topic-b].md` (e.g. `postgres-vs-mongo.md`)

6. **wiki/index.md** — Entry point
   - List important pages by category
   - Enables human and agent navigation
   - Must be kept up-to-date as new pages are added

7. **wiki/SCHEMA.md** — Format specification
   - Define frontmatter schema, tag taxonomy, wikilink conventions, page structure

**Drafting flow:**
- Use `graph.json` communities to identify candidate entities
- Use the call graph and cross-module edges to identify decision boundaries
- For each candidate entity, draft an `entities/` page
- For each major design choice encountered, draft a `concepts/` page
- For known runtime issues discovered during code analysis, draft `patterns/` pages
- For decision alternatives, draft `comparisons/` pages
- Add `[[wikilinks]]` between related pages
- Update `index.md` after adding pages

**Every wiki page MUST follow the frontmatter schema in SCHEMA.md.** Use templates in `references/`.

**Every wiki page goes through PR review. NEVER auto-merge.**

### Step 6 - Generate spec/ (OpenSpec — How 施工藍圖)

**OpenSpec is a How family member (施工藍圖, construction blueprint)**, NOT the What layer. Code is the only What. OpenSpec lives in this repo's `spec/` directory, follows the repo's git history, and is verified by CI against the actual code.

```
spec/
  SPEC.md           # system overview
  [module]/
    SPEC.md         # per-module construction blueprint
```

Each SPEC.md uses this template:
```markdown
# [Module Name]

## Summary
One-paragraph description of what this module does.

## Construction Blueprint
- **Inputs**: ...
- **Outputs**: ...
- **Side effects**: ...
- **API contract**: ...

## Interface
```[language]
[function signatures / API endpoints]
```

## Data Flow
[How data moves through this module]

## Edge Cases
- ...
```

**OpenSpec lives in repo, not in wiki.** This is a hard boundary — see Trivium Decision 2.

### Step 7 - Create index and schema files

```bash
cat > "$PATH/wiki/index.md" << 'EOF'
# Wiki Index

## Entities
EOF
ls "$PATH/wiki/entities/" >> "$PATH/wiki/index.md"

cat >> "$PATH/wiki/index.md" << 'EOF'

## Concepts
EOF
ls "$PATH/wiki/concepts/" >> "$PATH/wiki/index.md"

cat >> "$PATH/wiki/index.md" << 'EOF'

## Patterns
EOF
ls "$PATH/wiki/patterns/" >> "$PATH/wiki/index.md"

cat >> "$PATH/wiki/index.md" << 'EOF'

## Comparisons
EOF
ls "$PATH/wiki/comparisons/" >> "$PATH/wiki/index.md"

# SCHEMA.md defines the wiki format
cat > "$PATH/wiki/SCHEMA.md" << 'EOF'
# Wiki SCHEMA

## Frontmatter (required on every page)
- title: string
- type: entity | concept | pattern | comparison | raw
- tags: [string]
- status: active | superseded | deprecated (for concepts only)
- created: YYYY-MM-DD
- updated: YYYY-MM-DD

## Wikilinks
Use [[page-name]] to link between wiki pages.

## Filenames
- raw/: YYYY-MM-DD-source-type.md
- entities/: [entity-name].md
- concepts/: [decision-name].md
- patterns/: [pattern-name].md
- comparisons/: [topic-a]-vs-[topic-b].md

## Content Sections
- ## Summary — one paragraph
- ## Context — background and motivation (for concepts)
- ## Decision — what was chosen (for concepts)
- ## Consequences — tradeoffs and follow-ups
- ## Symptom — what you see (for patterns)
- ## Root Cause — why it happens (for patterns)
- ## Workaround — how to mitigate (for patterns)
- ## References — [[wikilinks]] and external sources
EOF
```

### Step 8 - Open Git PR for human review (REQUIRED for wiki content)

**Wiki content MUST go through PR review before merge.** This is a curation workflow, not an auto-publish.

```bash
cd "$PATH"
git add .
git commit -m "Draft Trivium-aligned wiki + spec from graphify analysis"
git checkout -b wiki/initial-curation
git push -u origin wiki/initial-curation
# Open PR via gh CLI or GitHub UI
```

The user (RD Agent / human) reviews and merges. After merge, the **Wiki Search Service** re-indexes.

**Why Git PR (not auto-merge or Wiki MCP):**
- Human review gate preserves the "Why" layer's judgment quality
- Git history becomes the audit trail (no separate log.md needed)
- File conflicts → agent git merge
- Design conflicts → PR review queue surfaces contradictions
- Agent doesn't need to learn MCP write syntax

## Output summary

After completing, report:
```
Repo structured at: $PATH

raw/          — Code (the only What)
graphify/     — How bridge (function-level knowledge graph)
wiki/         — Why layer (curated, Git PR reviewed)
  raw/        —   evidence (append-only)
  entities/   —   services, modules, external deps
  concepts/   —   design decisions, tradeoffs
  patterns/   —   How family: runtime experience
  comparisons/ —  option/architecture comparisons
  index.md    —   entry point
  SCHEMA.md   —   format spec
spec/         — OpenSpec How family: construction blueprint (per module)
```

## CI Checks (recommended for the wiki repo)

When this wiki is hosted as a git repo, set up these CI checks:

- **raw/ immutability**: `raw/` only allows new files; old evidence must not be modified
- **index completeness**: Important pages must appear in `index.md`
- **frontmatter validation**: Every page has valid metadata
- **wikilink integrity**: All `[[wikilinks]]` point to existing pages
- **patterns/ separation**: Patterns cite runtime evidence (incident, log, bug report) — patterns without [[wikilinks]] to evidence should be flagged

## Read Workflow (Trivium v2)

After the wiki is merged, the **Wiki Search Service** (read-only) provides access:

```
RD Agent       → Wiki Search Service (查 Why) + Graphify MCP (查 How) + CI API (查 What)
Chatbot RAG    → Wiki Search Service (語意搜尋, 不摘要)
End User       → Chatbot RAG (uses Wiki Search Service content)
```

**Wiki Search Service API contract:**
- Semantic search + `[[wikilinks]]` traversal + relevance ranking
- Returns full original markdown (no summarization, no rewriting)
- Index rebuilt on git merge to main

## Cross-Repo Integration

For multi-repo projects, follow the Trivium cross-repo design:

```
/opt/graphify-workspace/
├── repos/           # All repos master (read-only clone)
│   ├── frontend/
│   ├── backend/
│   └── shared-types/
└── graphify-out/    # Cross-repo merged graph
    ├── graph.json
    ├── graph.html
    └── GRAPH_REPORT.md
```

The shared wiki repo (separate git repo) holds cross-repo `concepts/` and `patterns/`. Per-repo wiki subdirectories can be merged into the shared wiki repo.

## Constraints

- **Step 4 (/graphify) is MANDATORY — do not skip or replace with manual extraction**
- **Wiki content MUST go through PR review — never auto-merge**
- Do NOT modify anything in `raw/` (code) or `wiki/raw/` (evidence) after creation
- `wiki/concepts/` entries are NEVER deleted; supersede them with `status: superseded`
- OpenSpec lives in repo, not in wiki (this is a hard Trivium boundary)
- Graphify output is read-only — never modify Wiki pages from Graphify output
- If graphify fails on large repos, run on subdirectories first
- Use Traditional Chinese for wiki content unless source is clearly English