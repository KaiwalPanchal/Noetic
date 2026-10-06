---
description: Stage a validated draft as copy-paste text, then log it once the owner has posted it manually
argument-hint: <draft path or name> [posted <tweet-url>]
---

# /ship — draft → ready → archive

Arguments: $ARGUMENTS

**Hard rule: never post anything anywhere.** This engine does not touch X/Twitter. The owner posts by hand.

## 1. Load context
Read `taste-engine.config.json`. Resolve `{engine}`, `{twitter}`, `{overmind}`, `x_char_limit`.
Find the draft: Glob in `{engine}/03-pipeline/02-drafts/` and `{twitter}/drafts/`.

## 2. Stage (no URL given)
1. Run `python "{engine}/scripts/thread_validator.py" "<draft>" --limit <x_char_limit>`. If it fails, stop and show the failures.
2. Build the ready file:
   - Engine drafts go to `{engine}/03-pipeline/03-ready-to-post/<slug>.md`
   - Journey drafts go to `{twitter}/ready/<slug>.md`

   The ready file contains: frontmatter (`status: ready`, `source-draft: [[...]]`), then each tweet as plain text in its own fenced ```text block (easy copy-paste, no markdown artifacts), numbered `1/`, `2/` and so on, only if the draft used numbering.
3. Leave the draft where it is, but set its frontmatter `status: shipped` so `/curate` and `/draft` skip it.
4. Tell the owner: "Ready at <path>. Post it by hand, then run `/ship <slug> posted <url>`."

## 3. Log (URL given: `posted <url>`)
1. Move the ready file to `{engine}/03-pipeline/04-archive/<date>-<slug>.md` (engine posts) or keep it in `{twitter}/ready/` and mark it `status: posted` (journey posts). Add `url:` and `posted:` to the frontmatter, plus empty sections for **Metrics (48h)**, **Top replies** and **New edge learned**.
2. Append a row to `{twitter}/posted.md`: `| date | [title](url) | type (thread/journey) | interest | learnings: _pending_ |`
3. If `{overmind}` is set:
   - Append a dated bullet to the current month's log `{overmind}/wiki/log/YYYY-MM.md` (create the month heading if needed).
   - If this post completes an active quest's pass criteria (check `{overmind}/wiki/quests/`), **say so and propose** the XP-LEDGER row. Write it only after the owner confirms, because XP is awarded on verified completion only.
4. Remind the owner to fill in metrics in 48h.
