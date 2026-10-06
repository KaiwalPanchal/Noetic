"""Knowledge layer: the vault is the database (12-factor #5).

- config.py   where things live (taste-engine.config.json)
- context.py  what a model is allowed to see: budgeted, privacy-filtered context
- notes.py    how results become notes: frontmatter, renderers, status changes

Future knowledge pipelines (indexing, organizing, auto-linking, a disposable
semantic index in .taste-engine/cache/) belong here. Markdown stays the source
of truth; any index must be rebuildable from the .md files.
"""
