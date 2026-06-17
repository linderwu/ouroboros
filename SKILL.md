---
name: repo-structurer
description: "Transform a project repo into a 4-layer structured format: raw/, graphify/, wiki/, spec/"
---

# Repo Structurer

Transform any project repo into a structured 4-layer + sublayer format:

```
repo/
  raw/           # immutable original code
  graphify/      # function-level knowledge graph (via graphify)
  wiki/
    concepts/    # what each module does (design-time)
    procedures/  # how data flows through function chains
    decisions/   # why design choices were made
    patterns/    # runtime-learned: known issues, debug clues, workarounds
    reference/   # 外部參考資料：API 文件、第三方文檔、引用來源
  spec/          # openspec-format specifications
```

## Graphify

**Graphify** (package: `graphifyy`, double-y) — https://github.com/safishamsi/graphify

Turns any codebase into a queryable knowledge graph. Run `/graphify .` and get:
- `graph.html` — interactive node graph
- `graph.json` — function-level nodes + call/import edges
- `GRAPH_REPORT.md` — community detection, hub functions, cross-module insights

This skill uses graphify to scan every function's calls, imports, and data flow, then builds the `graphify/` layer as the foundation for wiki extraction.

## Trigger

Use when asked to "structure a repo", "transform to 4-layer format", "prepare repo for knowledge management", or similar.

## Execution Order (Strict — Do Not Reorder)

**Phase 1 — Code Preservation:**
1. Accept path
2. Create directory structure
3. Copy ALL code to `raw/` (immutable snapshot)

**Phase 2 — Function Relationship Mapping:**
4. Scan each function's functionality with graphify → build relationship network in `graphify/`
5. Agent reads graph output → understands major functional blocks → writes concept descriptions

**Phase 3 — Knowledge Extraction:**
6. Extract wiki/ content from graphify insights (concepts, procedures, decisions)
7. Generate spec/ from code + graph analysis
8. Create index files
9. Establish patterns/ for runtime-learned knowledge (known issues, debug clues)

## Workflow

### Step 1 - Accept path

If no path given, ask for it. Confirm it exists.

```bash
ls -la "$PATH" 2>/dev/null || echo "PATH_NOT_FOUND"
```

If `PATH_NOT_FOUND`, stop and ask for a valid path.

### Step 2 - Create directory structure

```bash
mkdir -p "$PATH/raw" "$PATH/graphify" "$PATH/wiki/concepts" "$PATH/wiki/procedures" "$PATH/wiki/decisions" "$PATH/wiki/patterns" "$PATH/wiki/reference" "$PATH/spec"
echo "Directories created"
```

### Step 3 - Copy original code to raw/

Preserve directory structure. Exclude common build artifacts.

```bash
cd "$PATH"
FIND_EXCLUDE="-path '*/node_modules' -o -path '*/.git' -o -path '*/dist' -o -path '*/build' -o -path '*/__pycache__' -o -path '*/.venv' -o -path '*/target' -o -path '*/.next'"
rsync -av --exclude='node_modules' --exclude='.git' --exclude='dist' --exclude='build' --exclude='__pycache__' --exclude='.venv' --exclude='target' --exclude='.next' --exclude='*.pyc' --exclude='*.class' --exclude='*.o' ./ "$PATH/raw/" 2>/dev/null || cp -r . "$PATH/raw/"
echo "raw/ done"
```

### Step 4 - Scan function-level relationships with /graphify (REQUIRED — do not skip)

**Phase 2 — Function relationship mapping.** This step scans every function and builds a relationship network.

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

   If pip install puts graphify outside PATH, add `~/.local/bin` to PATH or use `python3 -m graphify`.

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

**Critical: The agent must read and understand graphify's output before writing wiki content.**

After /graphify completes, the agent MUST:
1. Read `graphify/GRAPH_REPORT.md` — understand community clusters, hub functions, and insights
2. Read `graphify/graph.json` — understand the full function-level relationship network
3. Identify major functional blocks (communities of functions that work together)
4. Write concept descriptions for each large functional block in the codebase

**Concept descriptions** are plain-language summaries of what a functional area does, not just file-level summaries. Use the graph to understand which functions cluster together and why.

### Step 5 - Extract wiki/ content from graphify insights

**Derived from Phase 2's graph.json.** Use the function relationship network to extract concepts and procedures.

For each meaningful module, create:
- `wiki/concepts/[module-name].md` — what each function/module does
- `wiki/procedures/[process-name].md` — how data flows through function chains
- `wiki/decisions/[decision-name].md` — why design choices were made
- `wiki/patterns/[issue-name].md` — runtime-learned: known issues, debug clues, workarounds
- `wiki/reference/[external-resource].md` — external references: API docs, third-party docs, citations

**Filename convention:** `[noun-phrase].md` — use descriptive nouns, not verbs. Example filenames:
- `concepts/auth-service.md` — not `Authentication.md`
- `procedures/order-checkout-flow.md` — not `Checkout.md`
- `decisions/timeout-500ms.md` — not `TimeoutDecision.md`
- `patterns/ocr-timeout-300to500.md` — not `KnownIssue1.md`
- `reference/supabase-postgres-spec.md` — not `Doc.md`

Base wiki pages on graphify's graph.json:
- Hub functions (high-degree nodes) → core concepts
- Community clusters → module-level procedures
- Cross-module edges → interfaces and shared data flows

### Step 6 - Generate spec/ (openspec format)

Create specification documents in openspec format:

```
spec/
  SPEC.md           # overview of the system
  [module]/
    SPEC.md         # per-module specification
```

Each SPEC.md uses this template:
```markdown
# [Module Name]

## Summary
One-paragraph description of what this module does.

## Functionality
- **What it does**: ...
- **Inputs**: ...
- **Outputs**: ...
- **Side effects**: ...

## Interface
```[language]
[function signatures / API endpoints]
```

## Data Flow
[How data moves through this module]

## Edge Cases
- ...
```

### Step 7 - Create index files

For each directory, create an `INDEX.md` that links to all contents.

```bash
# Graphify index
ls "$PATH/graphify/" > /tmp/gfiles
# Wiki index
ls "$PATH/wiki/" > /tmp/wfiles
# Spec index
ls "$PATH/spec/" > /tmp/sfiles
```

## Output summary

After completing, report:
```
Repo structured at: $PATH

raw/          — original code preserved (immutable)
graphify/     — function-level knowledge graph
  graph.html        — interactive visualization
  graph.json        — raw graph data
  GRAPH_REPORT.md   — community detection + insights
wiki/
  concepts/    — what each module does
  procedures/  — how data flows through function chains
  decisions/   — why design choices were made
  patterns/    — runtime-learned: known issues, debug clues, workarounds
  reference/   — external references: API docs, third-party docs, citations
spec/         — openspec-format specifications
```

## Constraints

- **Step 4 (/graphify) is MANDATORY — do not skip or replace with manual extraction**
- Do NOT modify anything in `raw/` after copying
- `wiki/` and `spec/` are editable; keep them in sync with code changes
- `wiki/decisions/` and `wiki/patterns/` should be updated whenever a decision is made or a runtime issue is discovered
- If graphify fails on large repos, run on subdirectories first
- Use Traditional Chinese for wiki content unless source is clearly English
