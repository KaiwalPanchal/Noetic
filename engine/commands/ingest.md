---
description: Ingest a source (book, URL, thread, notes) and extract a reusable thinking framework into the vault
argument-hint: <url | book title | path to notes | pasted text>
---

# /ingest — source → framework

Source to ingest: $ARGUMENTS

## 1. Load context
1. Read `taste-engine.config.json` at the vault root. Resolve `{engine}`, `{frameworks}`, `{twitter}`, `{overmind}` from `paths`, and `owner` / `agent`.
2. Read `{engine}/interests.md`. This is what the owner cares about. Every framework must link to at least one interest, or be flagged as off-interest.
3. Skim the filenames in `{frameworks}/` and `{engine}/01-taste-graph/`. If this framework (or a close cousin) already exists, **extend that note** instead of duplicating it.

## 2. Get the material
- URL → WebFetch it. Book title → check the vault for existing notes on it first (Grep the title), then use your own knowledge of the book, and say which parts came from where. Path → Read it. Pasted text → use it directly.
- If the source is thin or ambiguous, say so. Don't invent principles the author never stated.

## 3. Extract the *thinking*, not a summary
A framework is something you can **execute**. For each principle, ask: "What would I *do* differently on Monday because of this?" Write the answer as a verb-led procedure.

Fill `{engine}/templates/framework.md` exactly (all sections, in order):
- **Core Idea** — the whole framework in 1–2 sentences.
- **Principles** — numbered, in the author's terms, with a short quote or paraphrase.
- **Mental Moves / Procedures** — concrete steps. This is the important part.
- **When to Apply** — one line each for Content, Code, Projects/Decisions. Be specific. Example: "Code: before building any UI, collect 5 references and diff what they share."
- **Anti-Patterns** — how people misuse it.
- **Source Genealogy** — what the author stole from (Steal Like an Artist applies to the frameworks themselves).
- **Applications Log** — leave empty; `/apply` appends here.

Write it to `{frameworks}/<slug>.md` with the AI frontmatter from the template (author: ai-agent, agent from config, status: draft-for-review, the NOTE callout).

## 4. Side effects
- If the source is a paper, repo, postmortem or web article with standalone signal, also create a signal note: `python "{engine}/scripts/new_curation.py" signal "<title>" --type <paper|repo|postmortem|web>`, then fill it in.
- If it suggests a new interest, **propose** it (don't add it): show the line you'd add to `interests.md`.

## 5. Report
Reply with: the framework path, the 3 most actionable Mental Moves, and one suggested `/apply` command (e.g. `/apply <slug> code <reference-url>`).
