---
description: Turn a curation package or journey entry into a validated Twitter/X thread draft
argument-hint: <path or name of curation package / journey entry / existing draft>
---

# /draft — curation → thread

Input: $ARGUMENTS

## 1. Load context
1. Read `taste-engine.config.json`. Resolve `{engine}`, `{twitter}`, `x_char_limit`.
2. Read the input note. If it's a name rather than a path, Glob for it under `{engine}/03-pipeline/` and `{twitter}/`.
3. Read `{engine}/playbooks/thread-templates.md`, `twitter-hook-frameworks.md` and `editorial-lenses.md` if they exist, plus the negative filters.
4. Read 1–2 recent posts in `{engine}/03-pipeline/04-archive/` or `{twitter}/posted.md` to match the owner's voice.

## 2. Where it goes
- Curation package → `{engine}/03-pipeline/02-drafts/<slug>.md`
- Journey entry → `{twitter}/drafts/<slug>.md`
- Existing draft → edit it in place (a refinement pass)

## 3. Write
- Use `### Tweet N (label)` headers separated by `---`. The validator depends on this format.
- Tweet 1 is the hook: one sharp claim, no throat-clearing, no "🧵 A thread" filler unless it earns its place.
- One idea per tweet. Concrete over abstract: names, numbers, code, mechanisms.
- Credit sources by name or @handle (be nice, it's a small town).
- Last tweet: the takeaway plus a real question, or a link to the repo/artifact.
- Subtract. Cut every sentence that doesn't add new signal.
- Journey threads: first person, honest about what broke. Use specifics (time spent, what failed, what changed), never vague hustle-speak.

## 4. Validate (required)
Run: `python "{engine}/scripts/thread_validator.py" "<draft path>" --limit <x_char_limit>`
If it exits non-zero, fix the flagged tweets and re-run until it passes.

## 5. Report
The draft path, the validator result, and the hook tweet in full. Remind the owner that this is a **draft for their edit**: the machine drafts, the human supplies taste.
