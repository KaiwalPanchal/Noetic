# OverMind wiki (template)

A generic starting point for a personal operating wiki. Copy it into your vault with
`python install.py --vault <vault> --with-wiki` (existing files are never overwritten).

Layout

- `OVERMIND.md`: the constitution and current state. Agents read it at session start.
- `wiki/profile/`: who you are and how you want agents to work with you. **Private by design.**
- `wiki/competencies/`: skills you are building, with a level and evidence.
- `wiki/goals/`: outcomes you declared, each with a deadline and a measure.
- `wiki/projects/`: the project registry. See `_template.md` for the frontmatter.
- `wiki/quests/`: bounded units of work, plus `XP-LEDGER.md`.
- `wiki/log/`: dated log, one file per month (`YYYY-MM.md`).

## The profile folder is private by design

`wiki/profile/` holds personal context (preferences, constraints, history). Agents may read
it to tailor their work, but it must never be quoted in anything meant for publishing:
posts, READMEs, commits, public notes. Keep it out of any public repo or sync target.

Everything in this template is placeholder text. Replace it with your own.
