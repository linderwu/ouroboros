---
name: repo-structurer
description: "Transform a project repo into a 4-layer structured format: raw/, graphify/, wiki/, spec/"
---

# Repo Structurer

Transform any project repo into a structured 4-layer format:

```
repo/
  raw/           # immutable original code (Trivium: evidence layer)
  graphify/      # function-level knowledge graph (Trivium: how layer)
  wiki/          # Why layer — design intent, decisions, experience
  spec/          # openspec format (Trivium: what layer)
```

## Layer Philosophy (Trivium)

This skill produces four orthogonal layers. Each has a clear role and clear boundaries:

| Layer | Question | Source | Editable |
|-------|----------|--------|----------|
| **raw/** | "What is the original evidence?" | Cloned repo, logs, references | No — append-only |
| **graphify/** | "How does the code connect?" | `/graphify` scan | Re-generated on rebuild |
| **wiki/** | "Why is it designed this way?" | Human/agent curation via PR | Yes — via PR review |
| **spec/** | "What does the system do?" | openspec format | Yes — with code |

**Boundaries:**
- Wiki does NOT hold OpenSpec (spec is the "what", lives in `spec/`)
- Wiki does NOT hold call graph (graphify owns function relationships)
- Wiki does NOT replace git history (git tracks who changed what; wiki tracks why)
- Wiki content is NOT auto-generated as final knowledge — it goes through PR review

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

**Phase 1 — Evidence Preservation:**
1. Accept path
2. Create directory structure
3. Copy ALL code to `raw/` (immutable snapshot)

**Phase 2 — Function Relationship Mapping:**
4. Scan each function's functionality with graphify → build relationship network in `graphify/`
5. Agent reads graph output → understands major functional blocks → proposes entities/concepts

**Phase 3 — Knowledge Curation (Wiki):**
6. Draft wiki/ pages from graph insights (entities, concepts, patterns, comparisons)
7. Generate spec/ from code + graph analysis
8. Create index.md and SCHEMA.md for the wiki
9. Open PR for human review (NEVER auto-merge — wiki is curated knowledge)

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

### Step 3 - Copy original code to raw/

Preserve directory structure. Exclude common build artifacts.

```bash
cd "$PATH"
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

**Wiki is the Why layer.** It is NOT auto-generated as final knowledge — it goes through PR review before merge.

The wiki directory follows this structure:

```
wiki/
  raw/           # Evidence layer — original sources (meeting notes, external docs, logs, incident records)
  entities/      # Actors layer — services, modules, systems, external deps
  concepts/      # Decisions layer — design choices, tradeoffs, the Why
  patterns/      # Experience layer — runtime-learned knowledge (known issues, debug clues, workarounds)
  comparisons/   # Comparison layer — different options/tools/architectures
  index.md       # Entry point — list of important pages
  SCHEMA.md      # Format spec — frontmatter, tags, wikilinks, page structure
```

**Drafting rules:**

1. **wiki/raw/** — Evidence layer (immutable, append-only)
   - Original sources: meeting notes, external references, logs, test results, incident records
   - Never modify old evidence. Add new files only.
   - Filename convention: `YYYY-MM-DD-source-type.md`

2. **wiki/entities/** — Actors layer
   - Each page documents ONE entity (service, module, system, external dependency)
   - Content: responsibility boundaries, history, known issues, related decisions
   - Filename: `[entity-name].md` (e.g. `auth-service.md`)
   - Cross-link to related concepts and patterns via `[[wikilinks]]`

3. **wiki/concepts/** — Decision layer (the most valuable)
   - Each page documents ONE design decision or technical choice
   - Content: what was chosen, alternatives, why, consequences, evidence
   - Old decisions are NOT deleted. If superseded, mark with `status: superseded` in frontmatter
   - Filename: `[decision-name].md` (e.g. `use-postgres-over-mongo.md`)
   - Cross-link to evidence in `raw/`, related entities, and patterns

4. **wiki/patterns/** — Experience layer
   - Runtime-learned knowledge
   - Content: known issues, debug clues, performance observations, workaround backgrounds, incident lessons
   - Filename: `[pattern-name].md` (e.g. `ocr-timeout-300to500ms.md`)
   - Updated whenever a new runtime issue is discovered

5. **wiki/comparisons/** — Comparison layer
   - Compare different options, tools, architectures, or technical routes
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
- Add `[[wikilinks]]` between related pages
- Update `index.md` after adding pages

**Every wiki page MUST follow the frontmatter schema in SCHEMA.md.** Use templates in `references/`.

### Step 6 - Generate spec/ (openspec format — What layer)

Create specification documents in openspec format. Spec is the "what" layer; it follows code.

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

# SCHEMA.md defines the wiki format
cat > "$PATH/wiki/SCHEMA.md" << 'EOF'
# Wiki SCHEMA

## Frontmatter (required on every page)
- title: string
- type: entity | concept | pattern | comparison | raw
- tags: [string]
- status: active | superseded | deprecated (for concepts)
- created: YYYY-MM-DD
- updated: YYYY-MM-DD

## Wikilinks
Use [[page-name]] to link between wiki pages.

## Filenames
- entities/: [entity-name].md
- concepts/: [decision-name].md
- patterns/: [pattern-name].md
- comparisons/: [topic-a]-vs-[topic-b].md
- raw/: YYYY-MM-DD-source-type.md

## Content Sections
- ## Summary — one paragraph
- ## Context — background and motivation
- ## Decision — what was chosen (for concepts)
- ## Consequences — tradeoffs and follow-ups
- ## References — [[wikilinks]] and external sources
EOF
```

### Step 8 - Open PR for human review (REQUIRED for wiki content)

**Wiki content MUST go through PR review before merge.** This is a curation workflow, not an auto-publish.

```bash
cd "$PATH"
git add .
git commit -m "Draft wiki pages from graphify analysis"
git checkout -b wiki/initial-curation
git push -u origin wiki/initial-curation
# Open PR via gh CLI or GitHub UI
```

The user (RD Agent / human) reviews and merges. After merge, the Wiki Search Service re-indexes.

## Output summary

After completing, report:
```
Repo structured at: $PATH

raw/          — original code preserved (immutable)
graphify/     — function-level knowledge graph
wiki/         — Why layer (curated, PR-reviewed)
  raw/        —   evidence (append-only)
  entities/   —   services, modules, external deps
  concepts/   —   design decisions, tradeoffs
  patterns/   —   runtime-learned knowledge
  comparisons/ —  option/architecture comparisons
  index.md    —   entry point
  SCHEMA.md   —   format spec
spec/         — openspec-format specifications (What layer)
```

## CI Checks (recommended for the wiki repo)

When this wiki is hosted as a git repo, set up these CI checks:

- **raw/ immutability**: `raw/` only allows new files; old evidence must not be modified
- **index completeness**: Important pages must appear in `index.md`
- **frontmatter validation**: Every page has valid metadata
- **wikilink integrity**: All `[[wikilinks]]` point to existing pages

## Read Workflow

Wiki is read by:
- **RD Agent** — queries Wiki Search Service for design intent ("why")
- **Chatbot RAG** — uses wiki content to answer end users

Read-only access: semantic search via embeddings + `[[wikilinks]]` traversal. The service returns raw markdown without summarization or rewriting.

## Constraints

- **Step 4 (/graphify) is MANDATORY — do not skip or replace with manual extraction**
- **Wiki content MUST go through PR review — never auto-merge**
- Do NOT modify anything in `raw/` (code evidence) or `wiki/raw/` (curated evidence) after creation
- `wiki/concepts/` entries are NEVER deleted; supersede them with `status: superseded`
- `wiki/` and `spec/` are editable; keep them in sync with code changes
- If graphify fails on large repos, run on subdirectories first
- Use Traditional Chinese for wiki content unless source is clearly English