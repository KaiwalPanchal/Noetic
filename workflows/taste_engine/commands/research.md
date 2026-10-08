---
description: Research a topic on the web, filter it through taste, and save signals plus a curation package
argument-hint: <topic or question>
---

# /research — web → filtered signals → curation

Topic: $ARGUMENTS

## 1. Load context
1. Read `taste-engine.config.json`. Resolve `{engine}`, `{frameworks}`.
2. Read `{engine}/interests.md` and `{engine}/01-taste-graph/negative-filters/*`. Also skim the stances and exemplars so you know what the owner already believes.

## 2. Search for ground truth, not SEO
- Run several web searches in parallel. Prefer primary sources: papers, repos, changelogs, engineering blogs, postmortems, and practitioner threads/Reddit/HN.
- Avoid listicles, "top 10" posts, vendor marketing and AI-generated summaries.
- Fetch the 3–6 most promising results and read them properly.

## 3. Filter
For every source, decide **keep** or **reject**:
- Reject if it trips a negative filter, has no mechanism (all claims, no how), or just restates something already in the vault.
- Keep if it has a concrete mechanism, data, a failure story, or a claim that contradicts or sharpens an existing stance.

## 4. Write
- For each kept source, create a signal note: `python "{engine}/scripts/new_curation.py" signal "<title>" --type <paper|repo|postmortem|web>`, then fill in the mechanism, the taste judgment, genealogy, linked interests and the tweet angle.
- Write **one** curation package that synthesizes the kept signals: `{engine}/03-pipeline/01-curation/curation-<NNN>-<slug>.md`.
- If a source contradicts an existing stance, flag it in the report. Don't silently edit the stance.

## 5. Report
- Kept sources (title, URL, one line each on why)
- **Rejected sources, each with the reason it failed the filter**
- The curation package path and its strongest hook
