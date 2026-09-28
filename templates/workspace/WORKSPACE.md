# {{WORKSPACE_NAME}} Workspace

## Purpose

{{ONE_PARAGRAPH_SYSTEM_OR_PRODUCT_PURPOSE}}

## Repositories

### {{REPOSITORY_ID}}

- Path: `{{RELATIVE_PATH}}`
- Purpose: {{SHORT_PURPOSE}}
- Profile: `{{PROFILE_NAME}}`
- Owns: {{OWNED_CAPABILITIES_OR_DATA}}
- Contract: `{{CONTRACT_OR_DOC_PATH_IF_ANY}}`

<!-- Repeat only for repositories that belong to this workspace. -->

## Relationships

```text
{{CALLER}} -> {{DEPENDENCY}} : {{CONTRACT_OR_REASON}}
```

## Shared operational flow

{{ONLY_THE_MINIMUM_CROSS_REPOSITORY_FLOW_NEEDED_FOR_ROUTING}}

## Cross-repository rule

Do not inspect another repository unless the current task changes or depends on its contract, rollout, data, or runtime behavior. Load the target repository's own `AGENTS.md` before reading its internals.

## Workspace decisions

- Cross-repository ADRs: `docs/adr/`
- Shared contracts: `{{SHARED_CONTRACT_LOCATION_OR_NONE}}`

Keep this file roughly 500–1,500 tokens. Link to details instead of duplicating repository architecture.
