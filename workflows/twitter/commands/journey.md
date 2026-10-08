---
description: Log a build-in-public journey entry (what was built, what broke, decisions) with tweet candidates
argument-hint: [what happened — leave empty to summarize this session]
---

# /journey — document the build

Input: $ARGUMENTS

## 1. Load context
1. Read `taste-engine.config.json`. Resolve `{engine}`, `{twitter}`, `{overmind}`, `x_char_limit`.
2. Read the 2–3 most recent entries in `{twitter}/journey/` for continuity, so you don't re-explain earlier context.
3. Gather raw material:
   - the current conversation (what was actually done this session)
   - the input text, if given
   - `git log --oneline -15` in the engine repo, if the owner has one (ask for the path once and suggest adding it to config as `paths.repo`)
   - the newest entries in `{overmind}/wiki/log/` if `{overmind}` is set

## 2. Write the entry
Create it with `python "{engine}/scripts/new_curation.py" journey "<short title>"`, then fill in every section:
- **What I built**: concrete artifacts, commands and files. Show, don't hype.
- **What broke / surprised me**: honest. This is the part people actually read.
- **The decision (and why)**: one real trade-off you made.
- **Proof**: commit hashes, file paths, screenshots, links.
- **Tweet candidates**: 1–3 standalone tweets (`### Tweet N` format, each ≤ `x_char_limit`) plus, if there's enough substance, a note that it could become a thread via `/draft`.

**Privacy filter:** never include health, sleep, burnout, finance, relationship or company-confidential details (for example, anything from `{overmind}/wiki/profile/`), even if they're in the session. Rewrite to the public-safe version or leave it out.

## 3. Validate
Run `python "{engine}/scripts/thread_validator.py" "<entry path>" --limit <x_char_limit>` and fix anything over the limit.

## 4. Report
The entry path, the strongest tweet candidate in full, and: "Run `/draft <entry>` to turn it into a thread, or copy the candidate as-is."
