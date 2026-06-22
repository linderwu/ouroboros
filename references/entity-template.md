---
title: [Entity Name]
type: entity
tags: [service, backend, frontend, external-dep, ...]
repo: repos/<repo-name>           # which repo this entity lives in
source_path: path/to/file         # primary source location within the repo
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# [Entity Name]

> An entity is an **actor** in the system — a service, module, external dep, or component.
> Its source of truth is in `repos/<repo-name>/source_path`, NOT here.

## Summary
One-paragraph description of what this entity is and its role.

## Responsibility Boundaries
- What this entity owns
- What it explicitly does NOT do

## Source
- **Repository**: `repos/<repo-name>/`
- **Primary path**: `path/to/main/file`
- **Spec**: [[spec-<module-name>]] (OpenSpec entry)

## Procedural Position
Where this entity sits in the runtime flow:
- `[[entity-upstream]]` → **this** → `[[entity-downstream]]`
- Triggered by: `[[pattern-x]]`, `[[pattern-y]]`
- Invokes: `[[entity-z]]` (cross-repo: `[[repos/backend/entity-z]]`)

## History
- YYYY-MM-DD: Initial implementation (cite evidence: [[raw/YYYY-MM-DD-pm-spec]])
- YYYY-MM-DD: Refactored for ... (cite evidence: [[raw/YYYY-MM-DD-meeting-notes]])

## Known Issues
- [[pattern-name-1]] — related runtime issue
- [[pattern-name-2]] — debug clue

## Related Decisions
- [[concept-decision-name]] — design choice that shaped this entity

## References
- [[raw/source-file]] — supporting evidence (cite `raw/` directly, never `wiki/raw/`)
- External: <https://example.com>
