---
title: [Pattern Name]
type: pattern
tags: [runtime-issue, performance, debug-clue, work-around, ...]
trigger: incident | post-mortem | perf-observation | on-call
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# [Pattern Name]

> A pattern is a **runtime experience** — what you see, why it happens, how to work around it.

## Summary
The runtime observation in one sentence.

## Symptom
What you see when this pattern triggers (log lines, error messages, behavior).

## Root Cause
Why this happens (cite code path or config).
- **Source**: `repos/<repo-name>/path/to/file:LINE`
- **Why**: explanation

## Workaround
How to mitigate or work around this issue.

## Detection
How to identify this pattern in logs or metrics.

## Related Entities
- [[entity-name]] — entity affected
- (cross-repo) `[[repos/<other-repo>/entity-name]]`

## Related Decisions
- [[concept-decision-name]] — design decision that influenced this

## References
- [[raw/incident-record]] — incident that first surfaced this (cite `raw/` directly, never `wiki/raw/`)
- Internal logs: ...
- External: <https://example.com>
