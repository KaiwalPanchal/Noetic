<!-- taste-engine:start -->
## Taste Engine

This vault runs the open-source Taste Engine. Paths are configured in `taste-engine.config.json`.

- **Interests** (what to curate for): `{{engine}}/interests.md`
- **Taste graph** (stances, negative filters, exemplars): `{{engine}}/01-taste-graph/`
- **Frameworks** (thinking extracted from sources, vault-wide): `{{frameworks}}/`. Build briefs go in `{{frameworks}}/briefs/`
- **Content pipeline**: `{{engine}}/03-pipeline/` (00-inbox → 01-curation → 02-drafts → 03-ready-to-post → 04-archive)
- **Build-in-public journey**: `{{twitter}}/` (journey/, drafts/, ready/, posted.md)
- **Commands**: `/ingest` `/apply` `/curate` `/research` `/draft` `/ship` `/journey`
- **Python pipeline (multi-agent)**: `python "{{engine}}/scripts/pipeline.py" list`. The same jobs as the commands, as fixed steps routed to claude / codex / agy. Outputs are `status: pending_review`; approve with `pipeline.py approve <file>`. Architecture: orchestration · knowledge · tools · actions in `{{engine}}/scripts/taste_engine/`.
- **Scripts**: `{{engine}}/scripts/new_curation.py` (scaffolder), `{{engine}}/scripts/thread_validator.py` (exits 1 if a tweet is over the limit)

Rules:
- **When running a Taste Engine command, the command file is the harness. Follow it exactly.** Do its steps in order. Use only the scripts, templates, folders and tools it names. Don't add steps, files, features or your own methodology, and don't widen or narrow its scope. If something it needs is missing or ambiguous, stop and say what's missing instead of improvising. (Pipeline agents get the same contract: `{{engine}}/prompts/_contract.md`.)
- **Never post to X/Twitter or any external service.** The owner posts by hand.
- AI-written notes use the `author: ai-agent` frontmatter + NOTE callout (`new_curation.py` produces it).
- The machine drafts; the owner supplies the final taste. Don't mark anything `curated` on the owner's behalf.
- Ship over meta-structure: don't reorganize the graph when a draft is waiting to be published.
<!-- taste-engine:end -->
