---
name: repo-structurer
description: "Transform a project repo into a 4-layer structured format: raw/, graphify/, wiki/, spec/"
---

# Repo Structurer

Transform any project repo into a structured 4-layer format:

```
repo/
  raw/           # immutable original code
  graphify/      # function-level knowledge graph (via graphify)
  wiki/          # concepts, procedures, decisions
  spec/          # openspec-format specifications
```

## Trigger

Use when asked to "structure a repo", "transform to 4-layer format", "prepare repo for knowledge management", or similar.

## Workflow

### Step 1 - Accept path

If no path given, ask for it. Confirm it exists.

```bash
ls -la "$PATH" 2>/dev/null || echo "PATH_NOT_FOUND"
```

If `PATH_NOT_FOUND`, stop and ask for a valid path.

### Step 2 - Create directory structure

```bash
mkdir -p "$PATH/raw" "$PATH/graphify" "$PATH/wiki" "$PATH/spec"
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

### Step 4 - Run /graphify on raw/ (REQUIRED — do not skip)

**This step is mandatory.** The `graphify/` layer is the core of this format; it MUST be generated.

1. First ensure graphify is installed:
```bash
pip install graphifyy --quiet --break-system-packages 2>&1 | tail -3
```

2. Then invoke the graphify skill from the raw/ directory:
```bash
cd "$PATH/raw"
/graphify . --output-dir "$PATH/graphify" --mode deep 2>&1 | tail -10
```

This MUST produce these files in `graphify/`:
- `graph.html` — interactive visualization
- `graph.json` — raw graph data (function-level nodes with call/import edges)
- `GRAPH_REPORT.md` — community detection, god nodes, surprising connections

If graphify fails, do NOT proceed to Step 5. Stop and report the error. The wiki and spec layers depend on graph.json for identifying hub functions and cross-module edges.

### Step 5 - Extract wiki/ content (concepts + procedures)

Read key source files to extract:
- **concepts/** — what each module/file does (from comments, function names, docstrings)
- **procedures/** — how processes flow (from function calls, data flow)
- **decisions/** — why design choices were made (from comments, naming conventions)

```bash
# List top-level source files
find "$PATH/raw" -maxdepth 3 -type f \( -name "*.py" -o -name "*.ts" -o -name "*.js" -o -name "*.go" -o -name "*.rs" -o -name "*.java" \) | head -20
```

For each meaningful module, create a wiki page:
- `wiki/concepts/[module-name].md`
- `wiki/procedures/[process-name].md`

Use graphify output (`graph.json`) to identify:
- High-degree nodes (hub functions)
- Communities (grouped functionality)
- Cross-module edges (interfaces between components)

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
wiki/         — extracted concepts + procedures
spec/         — openspec-format specifications
```

## Constraints

- **Step 4 (/graphify) is MANDATORY — do not skip or replace with manual extraction**
- Do NOT modify anything in `raw/` after copying
- `wiki/` and `spec/` are editable; keep them in sync with code changes
- If graphify fails on large repos, run on subdirectories first
- Use Traditional Chinese for wiki content unless source is clearly English
