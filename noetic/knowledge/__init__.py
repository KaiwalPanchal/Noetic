"""Knowledge layer: the vault is the database (12-factor #5).

- config.py   where things live (noetic.config.json)
- context.py  what a model is allowed to see: budgeted, privacy-filtered context
- notes.py    how results become notes: frontmatter, renderers, status changes
- migrate.py  vault naming migration (.taste-engine -> .noetic)
- liminal.py  optional Liminal graph memory HTTP sidecar client
- recall.py   unified memory recall with sidecar and vault-grep fallback

Future knowledge pipelines (indexing, organizing, auto-linking, a disposable
semantic index in .noetic/cache/) belong here. Markdown stays the source
of truth; any index must be rebuildable from the .md files.
"""
