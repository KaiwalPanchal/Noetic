---
description: Apply a framework to produce an action — a content package, a coding build brief, or a project decision
argument-hint: <framework-slug> <content|code|project> [target: url, topic, or project name]
---

# /apply — framework → action

Arguments: $ARGUMENTS
(The first word is the framework slug, the second is the mode, and the rest is the target.)

## 1. Load context
1. Read `taste-engine.config.json`. Resolve `{engine}`, `{frameworks}`, `{overmind}`.
2. Read `{frameworks}/<framework-slug>.md`. If it's missing, list close matches and stop. Suggest `/ingest` instead.
3. Read `{engine}/interests.md` and `{engine}/01-taste-graph/negative-filters/*`.

## 2. Mode: `content`
Build a curation package in `{engine}/03-pipeline/01-curation/curation-<NNN>-<slug>.md`. NNN is the next free number.
- **Core Thesis**: the framework applied to the target topic, as a non-obvious claim.
- **3 Hook Angles**: contrarian, story, and practitioner. Use `{engine}/playbooks/twitter-hook-frameworks.md` if it exists.
- **Key Talking Points**: 4–6, each tied to a specific Principle or Mental Move from the framework.
- **Linked**: framework, stances, interests.
Run every angle through the negative filters. Drop or rewrite anything that reads as generic slop.

## 3. Mode: `code` — the "steal like an artist" build brief
The target is one or more reference URLs: awwwards, dribbble, a portfolio, or any site the owner admires.
1. Fetch each reference. Use WebFetch for content and structure. If browser tools are available, also inspect layout, typography, color and motion, and take screenshots.
2. **Deconstruct element by element.** For each notable element (hero, nav, grid, card, transition, cursor effect, scroll behavior, and so on), record:
   - what it is and where it appears
   - the likely implementation (CSS grid/flex, GSAP/ScrollTrigger, Framer Motion, WebGL, View Transitions, and so on)
   - why it works (the taste judgment, not just a description)
3. **Steal vs. transform.** Following the framework, decide per element: steal the *mechanism*, transform the *expression*. Never copy brand assets, copy text, logos or images. Credit every source.
4. Write `{frameworks}/briefs/<date>-<slug>-build-brief.md` using `{engine}/templates/build-brief.md`. A coding agent must be able to start from this file alone: stack suggestion, element specs, acceptance criteria and credits.

## 4. Mode: `project`
The target is a project or decision.
1. If `{overmind}` is set, read the relevant note in `{overmind}/wiki/projects/` or `goals/`.
2. Run the framework's Mental Moves against the situation. Example: hats/haircuts/tattoos means classifying how reversible the decision is.
3. **Propose** the decision or next-action text and the exact note it would go in. **Don't write it until the owner confirms.**

## 5. Close the loop
Append a line to the framework's **Applications Log**: `- YYYY-MM-DD · <mode> · [[link to output]]`.
Reply with the output path and a 3-line summary.
