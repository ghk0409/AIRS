# Current work

Status: AIRS v0.4.2 implementation complete; no active task.

The CLI supports file-scoped reviews of prior runs, bounded Antigravity streaming review, an environment doctor, and preview-first history pruning/scrubbing. v0.4.2 adds a Korean project adoption guide, routes primary agents to project docs, separates the project manifest from CLI settings, and raises the default Antigravity review timeout to 600 seconds.

Validation: 51 unit tests, Python compilation, whitespace checks, offline lockfile check, project-config smoke test, and live subscription CLI diagnostics passed. The large application repository is out of scope; its files were not changed.

Next action: collect labeled real-world runs to evaluate routing quality and refine retries/capability checks. A live Antigravity review of a 5–10 minute project task has not been repeated; the new timeout is verified through configuration and adapter tests.
