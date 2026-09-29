# Current work

Status: AIRS v0.4.0 implementation complete; no active task.

The CLI supports file-scoped reviews of prior runs, bounded Antigravity streaming review, an environment doctor, and preview-first history pruning/scrubbing. `README.ko.md` documents the same daily workflow in Korean.

Validation: unit tests, Python compilation, whitespace checks, offline doctor, and a one-file Antigravity review passed. The large application repository was not reviewed again because the prior attempt consumed substantial context before timing out.

Next action: collect labeled real-world runs to evaluate routing quality. Diff-aware review of deleted files and automatic Codex model capability discovery remain open.
