---
name: ouroboros
description: "Ouroboros — Transform project repo(s) into Trivium-aligned multi-repo structure: raw/ (evidence), repos/ (code), graphify/ (bridge), wiki/ (decisions + procedural architecture), spec/ (blueprint)"
---

# Ouroboros (Trivium v2.8)

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

## Execution Modes

Ouroboros 支援三種執行模式：

| 模式 | 適用 | 順序嚴格度 |
|------|------|-----------|
| **waterfall** | 大型專案（>20 檔案） | 嚴格 |
| **iterative** | 中小型專案（default） | 靈活 |
| **incremental** | 現有專案添加 wiki | 自由 entry point |

**使用方式：**
```bash
export OUROBOROS_MODE=iterative  # waterfall | iterative | incremental
```

**在 iterative 模式下，允許任意 Phase 之間來回跳轉。**

## Phase Execution Order

### Phase 0 — Size Assessment

**核心原則：LLM 本身就擅長理解小型程式碼的關聯性。工具是「增強」而非「取代」。**

0.1 Accept target path (or workspace root for multi-repo)
0.2 Identify scope: single repo vs multi-repo
0.3 Inventory existing evidence in `raw/` — DO NOT mutate (single canonical evidence layer)
0.4 **評估專案大小** — 決定使用哪些工具

```bash
# 計算重要程式碼檔案數量
FILE_COUNT=$(find "$PATH/repos" -type f \
  \( -name "*.py" -o -name "*.ts" -o -name "*.js" \
     -o -name "*.cpp" -o -name "*.h" -o -name "*.java" \
     -o -name "*.go" -o -name "*.rs" \
  \) 2>/dev/null | wc -l)

if [ "$FILE_COUNT" -lt 5 ]; then
  echo "size: SMALL"
  echo "tools: wiki_only"
elif [ "$FILE_COUNT" -lt 20 ]; then
  echo "size: MEDIUM"
  echo "tools: graphify_key_modules"
else
  echo "size: LARGE"
  echo "tools: codebase_memory_mcp_plus_graphify"
fi
```

### Size-Based Tool Selection

| 等級 | 標準 | 工具策略 | 理由 |
|------|------|---------|------|
| **S** | < 5 檔案 | LLM 自己理解 + wiki | 工具啟動成本 > LLM 自己理解的成本 |
| **M** | 5-20 檔案 | graphify 關鍵模組 | 局部關聯已足夠，不需要全域圖 |
| **L** | > 20 檔案 | codebase-memory-mcp + graphify | 超出 LLM 上下文，需要工具輔助 |

**Tool Selection Matrix:**

| 大小 | wiki | graphify | codebase-memory-mcp | spec |
|------|------|----------|---------------------|------|
| S    | ✅    | ❌       | ❌                  | ⚠️   |
| M    | ✅    | ⚠️關鍵模組 | ❌                  | ✅    |
| L    | ✅    | ✅       | ✅                  | ✅    |

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

**根據 Phase 0.4 評估結果，選擇性執行：**

#### SMALL: 跳過 graphify/mcp
LLM 本身就擅長理解小型程式碼的關聯性。直接進入 Phase 4。
理由：工具的啟動成本 > LLM 自己理解的成本

#### MEDIUM: graphify 關鍵模組
只對以下模組執行 graphify：
- 被多個模組依賴的（hub functions）
- 跨 repo 的介面
- 外部依賴密集的模組
理由：不需要全域圖，局部關聯已足夠

3.1 Install graphify: `uv tool install graphifyy`
3.2 For **關鍵模組** in `repos/`, run:
   ```
   cd repos/<repo-name> && graphify . --output-dir ../../graphify/<repo-name>/ --mode deep
   ```
3.3 Agent reads `graphify/GRAPH_REPORT.md` + `graph.json` for key modules only
3.4 Proposes wiki entity/concept/pattern candidates

#### LARGE: codebase-memory-mcp + 完整 graphify

**3.1 安裝 codebase-memory-mcp:**
```bash
curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash
```

**3.2 索引所有 repos:**
```bash
codebase-memory-mcp index_repository --repo-path "$PATH/repos/repo-a"
codebase-memory-mcp index_repository --repo-path "$PATH/repos/repo-b"
# ... all repos
```

**3.3 graphify cross-repo merge:**
```bash
graphify merge "$PATH/graphify/" --output "$PATH/graphify-out/" --mode deep
```

**3.4 Agent reads codebase-memory-mcp graph + graphify output:**
- `codebase-memory-mcp get_architecture` — 程式碼概覽
- `codebase-memory-mcp trace_path` — 關鍵函數的 call chain
- `codebase-memory-mcp query_graph` — Cypher 查詢
- `graphify/GRAPH_REPORT.md` — cross-repo 關係

**3.5 Proposes wiki entity/concept/pattern candidates**

**注意：** 對於小/中專案，跳過此階段直接進入 Phase 4。

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
  - Conditional: `{{if condition}} [[page-a]] {{else}} [[page-b]] {{endif}}`
  - Concurrency: `{{concurrent}} [[task-1]] | [[task-2]] {{/concurrent}}`
  - Loop: `{{repeat 3}} [[retry-task]] {{/repeat}}`
  - Cross-repo: `[[repos/frontend/entity]] ↔ [[repos/backend/entity]]`
- All pages: PR review before merge. NEVER auto-merge.

**Frontmatter schema** (see `ouroboros/references/frontmatter_schema.json`):
```yaml
title: string
type: entity | concept | pattern | comparison | procedure | raw
tags: [string]
status: active | superseded | archived | draft | deprecated  # all types have lifecycle
created: YYYY-MM-DD
updated: YYYY-MM-DD
```

**Content sections** (by type):
- entity: Summary, Responsibility Boundaries, History, Known Issues, Related Decisions, References
- concept: Summary, Context, Decision, Alternatives Considered, Consequences, References
- pattern: Summary, Symptom, Root Cause, Workaround, Detection, Related, References
- comparison: Summary, Dimensions, When to Choose A/B, Our Context, References
- procedure: Summary, Prerequisite, Steps, Expected Result, Error Handling, Related
- raw: Source, Date, Content (preserved as-is), Tags, Referenced By

**Lifecycle rules**:
- All types support `status: active | superseded | archived | draft | deprecated`
- `superseded` — 被新版本取代，但保留參考
- `archived` — 過時但有歷史價值
- `deprecated` — 不再建議使用

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

- **Phase 3 (/graphify or codebase-memory-mcp) is MANDATORY for MEDIUM and LARGE — do not skip**
- **For SMALL projects: skip Phase 3, LLM directly understands code relations**
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
- **v2.5: Size-based tool selection — LLM擅長理解小型程式碼，工具增強大型專案。Phase 0 新增大小評估，Phase 3 條件化（SMALL跳過、M只能graphify、L標配codebase-memory-mcp）。**
- **v2.6: Entropy Management + Enforcement Hooks — 新增熵管理、去重偵測、wikilinks完整性檢查、程式化CI鉤子。**
- **v2.7: Design Adjustments — 新增 Execution Modes（iterative/waterfall/incremental）、擴展型別系統（procedure/deprecated/lifecycle）、流程表達增強（分支/並發/迴圈）。**
- **v2.8: Working Memory Integration — 新增三層記憶架構（Knowledge Base / Session Memory / Working Memory）、Progress Tracker、Audit Log。**

---

## Phase 1.5: Entropy Management (熵管理)

### 問題診斷

Ouroboros 只設計了「怎麼把知識寫進去」，幾乎沒設計「怎麼讓它不爛」。跑過幾個月會被自己的熗壓垮。

### 解決方案：staleness_rules.yaml

```yaml
# ouroboros/references/staleness_rules.yaml
staleness_rules:
  entity:
    warning_threshold_days: 14
    archive_threshold_days: 30
  
  concept:
    warning_threshold_days: 30
    archive_threshold_days: 60
  
  pattern:
    warning_threshold_days: 60
    archive_threshold_days: 120
```

### 自動歸檔腳本

```bash
# 掃描並報告過時頁面（dry-run）
python3 ouroboros/scripts/auto_archive_hook.py

# 實際執行歸檔
python3 ouroboros/scripts/auto_archive_hook.py --execute
```

### 去重偵測

```bash
# 偵測近義重複頁面
python3 ouroboros/scripts/deduplication_hook.py
```

---

## Phase 2.5: Enforcement Hooks (強制力)

### 問題診斷

 Ouroboros 全靠自然語言語氣（MUST/NEVER），沒有任何 hook、CI、schema validator 在程式層擋。

### Wikilinks 完整性檢查

```bash
# 檢查所有 [[wikilinks]] 是否指向存在的頁面
python3 ouroboros/scripts/wikilinks_integrity_hook.py
```

**會阻擋 merge 如果有斷鏈存在。**

### 程式化 CI 鉤子

建議的 Git hook 設定：

```yaml
# ouroboros_ci.yaml（建議的 CI 設定）
hooks:
  pre-commit:
    - validate_frontmatter_schema
    - check_wikilinks_integrity
    - scan_staleness
  
  pre-merge:
    - deduplication_check
    - entity_concept_type_validation
    - link_integrity_report
```

### Frontmatter Schema 驗證

```json
// ouroboros/references/frontmatter_schema.json
{
  "required": ["title", "type", "updated"],
  "properties": {
    "type": {"enum": ["entity", "concept", "pattern", "comparison", "procedure"]},
    "status": {"enum": ["active", "superseded", "archived", "draft", "deprecated"]},
    "updated": {"type": "string", "format": "date"}
  }
}
```

---

## Phase 6: Working Memory Integration (工作記憶)

### 問題診斷

Ouroboros 只做「codebase 知識庫」，缺少 agent 工作記憶層：
- 沒有 progress 追蹤
- 沒有操作踩坑記錄
- 沒有 baseline/測試記錄
- 沒有 shared/private 可見範圍分級

### 解決方案：三層記憶架構

```
┌─────────────────────────────────────────────────┐
│  Ouroboros Knowledge Base（長期知識）            │
│  - wiki/ — PR-reviewed, curated                 │
│  - 回答「為什麼這樣設計」                        │
└─────────────────────────────────────────────────┘
                      ↑
┌─────────────────────────────────────────────────┐
│  Session Memory（當前任務）                      │
│  - memory/YYYY-MM-DD.md                         │
│  - 回答「現在在處理什麼」                        │
└─────────────────────────────────────────────────┘
                      ↑
┌─────────────────────────────────────────────────┐
│  Working Memory（當下操作）                      │
│  - HEARTBEAT.md, task_queue.json                │
│  - 回答「我現在在做什麼」                        │
└─────────────────────────────────────────────────┘
```

### Progress Tracker

```bash
# 開始 Phase
python3 ouroboros/scripts/progress_tracker.py start "phase_1"

# 完成 Phase
python3 ouroboros/scripts/progress_tracker.py complete "phase_1"

# 記錄決策
python3 ouroboros/scripts/progress_tracker.py decision \
  --decision "採用 iterative mode" \
  --reason "中小型專案不需要嚴格順序"

# 查看進度
python3 ouroboros/scripts/progress_tracker.py status

# 查看審計日誌
python3 ouroboros/scripts/progress_tracker.py audit --limit 20
```

### Session Memory Hook

```bash
# 記錄 entry
python3 ouroboros/scripts/session_memory_hook.py --entry "完成 Phase 1" --category "Ouroboros"

# 記錄決策
python3 ouroboros/scripts/session_memory_hook.py --decision "採用某方案" --reason "因為..."
