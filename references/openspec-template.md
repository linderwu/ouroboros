# OpenSpec Template Reference

## Per-Module Spec: `spec/[module]/SPEC.md`

```markdown
# [Module Name]

## Summary
One-paragraph description of what this module does and why it exists.

## Functionality

### Core Features
- **Feature 1**: ...
- **Feature 2**: ...

### Inputs
- `input_1`: description, type, source
- `input_2`: description, type, source

### Outputs
- `output_1`: description, type, destination
- `output_2`: description, type, destination

### Side Effects
- Any mutations, I/O, network calls, or state changes

## Interface

```[language]
// function signatures, API endpoints, class definitions
```

## Data Flow
How data moves through this module (input → transformation → output).

## Dependencies
- **Internal**: [other modules this depends on]
- **External**: [libraries, services, infrastructure]

## Edge Cases
- Case 1: expected behavior
- Case 2: expected behavior

## Error Handling
How errors are detected, logged, and propagated.

## Testing Notes
Key test scenarios or testing approach (not actual tests — those go in code).
```

## System Overview Spec: `spec/SPEC.md`

```markdown
# [Project Name] — System Specification

## Overview
High-level description of the system, its purpose, and scope.

## Architecture
[Key components and how they interact]

## Data Model
[Core entities and their relationships]

## API Surface
[Public endpoints and their purpose]

## Configuration
[Environment variables, feature flags, key settings]

## Deployment
[How the system is deployed, infrastructure requirements]

## Security Considerations
[Auth, authorization, data classification, sensitive handling]
```
