---
description: Curate content ideas from the vault only (no web), filtered by interests and taste
argument-hint: [optional topic or interest to focus on]
---

# /curate — vault → curation packages

Focus: $ARGUMENTS (if empty, use the highest-weight interests that have the fewest recent posts)

## 1. Load context
1. Read `taste-engine.config.json`. Resolve `{engine}`, `{frameworks}`, `{twitter}`.
2. Read `{engine}/interests.md`, every file in `{engine}/01-taste-graph/` (stances, negative filters, exemplars) and `{engine}/playbooks/editorial-lenses.md` if present.
3. Read `{engine}/03-pipeline/04-archive/` and `{twitter}/posted.md` so you don't repeat what's already shipped.

## 2. Gather (vault only, no web)
Search across the **whole vault**, not just the engine folder. Older notes (books, journals, thoughts) are where unexpected cross-pollination comes from. Use Grep on interest keywords, and read `{engine}/02-signals/`, `{engine}/03-pipeline/00-inbox/` and `{frameworks}/`.
Skip private areas: anything under `{overmind}/wiki/profile/`, journals, and finance/personal folders, unless the owner explicitly includes them.

## 3. Select (taste)
Pick **1–3** ideas. Each must:
- link to at least one interest
- make a non-obvious claim (contrarian, cross-domain, or backed by hands-on experience)
- pass every negative filter

Prefer intersections: two unrelated vault notes that combine into one sharp idea.

## 4. Write
For each idea, write a curation package to `{engine}/03-pipeline/01-curation/curation-<NNN>-<slug>.md`. Use the same structure as `/apply content`: Core Thesis, 3 Hook Angles, Key Talking Points, and Linked notes (cite every source note with `[[wikilinks]]`).

## 5. Report
A table with columns: package · interest · why it's non-obvious · source notes. Then a list of 2–3 ideas you *rejected* and which filter killed them, so the taste stays visible.
