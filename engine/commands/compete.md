---
description: Perform deep competitor and market intelligence research for a business idea or product wedge
argument-hint: <idea-slug or target-topic>
---

# /compete — idea/wedge → competitor intelligence → research report

Target: $ARGUMENTS

## 1. Load context
1. Read `taste-engine.config.json`. Resolve `{engine}`, `{frameworks}`, and vault root.
2. If `ideas/$ARGUMENTS/idea.md` exists in the vault, read its Core Problem, Target Audience, and Hypotheses.
3. Skim `{engine}/interests.md` and related stances in `{engine}/01-taste-graph/` to identify relevant mental models.

## 2. Search for ground truth & competitors
- Run parallel search queries targeting primary practitioner sources:
  - Discussions: Reddit (r/SaaS, r/smallbusiness, domain subreddits), Hacker News, Twitter/X.
  - Reviews & Complaints: G2, Trustpilot, Capterra, GitHub Issues.
  - Actual products: Direct competitor landing pages, documentation, and pricing tables.
- Strictly ignore SEO listicles, generic marketing copy, and AI-generated overviews.
- Clip key reference pages using the Clipper tool (`clip_url` / WebFetch).

## 3. Excavate the graveyard
- Uncover failed predecessors and shuttered startups in this space:
  - Search queries like `"<problem/domain> shutdown"`, `"<product> postmortem"`, `"why <company> failed"`.
  - Identify root causes of death: customer acquisition cost (CAC) explosion, user apathy, lack of budget authority, regulatory or compliance barriers.

## 4. Extract what works vs what fails
- Document verified willingness to pay (actual price points customers pay).
- Identify sticky workflows that users refuse to replace.
- Highlight false demand traps (features users say they want in interviews, but abandon in practice).

## 5. Formulate wedge & differentiation
- Define counter-positioning against the market incumbents.
- Specify the low-friction entry wedge.
- Articulate the novel mechanism that enables this product to win.

## 6. Write notes
- If working within an idea workspace (`ideas/<slug>/`), update or create `ideas/<slug>/research.md`.
- Create signal notes in `{engine}/02-signals/web/` for high-value competitor mechanisms and teardowns.
- Output the structured synthesis with verdict (`Strong Signal`, `Mixed Signal`, or `Negative Signal`).
