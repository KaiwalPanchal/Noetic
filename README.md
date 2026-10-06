# Taste Engine

**Turn what you read into how you work.**

**In plain words:** you give it a book, a website or a thread. It figures out *how that person thinks* and saves that as a reusable framework. Later you ask it to use that framework to write a post, plan a website ("build it like that site, but mine"), or think through a decision. It lives inside your notes app, it never posts anything for you, and your notes stay on your machine.

An open-source agent layer for your second brain (Obsidian or any markdown vault). You feed it sources: books, sites, threads, papers. It extracts the *thinking frameworks* inside them and then **applies** them. It can write content that sounds like you, produce build briefs for your coding agent, and help with project decisions.

You can drive it two ways:
- **Claude Code commands** (`/ingest`, `/draft`, …): interactive, inside your vault.
- **A Python pipeline** (`python pipeline.py ingest …`): fixed steps, where each step can go to a different AI. Claude writes, Codex builds code, Antigravity researches, and if one is down or out of quota the next takes over.

There's no server, database or SaaS. It's your notes, plain-text prompts, and a small Python framework with four layers (**orchestration · knowledge · tools · actions**) that you can extend with your own pipelines and tools. See [ARCHITECTURE.md](ARCHITECTURE.md).

> Content is infinite now. Taste (what you select, how you combine it, and what you reject) is what's scarce. This engine writes your taste down so an agent can use it.

## The loop

```
  sources ──/ingest──▶ frameworks/ ──/apply──▶ content package  ──/draft──▶ thread ──/ship──▶ you post it
 (books, sites,        (principles,         ├▶ code build brief ──▶ your coding agent
  threads, papers)      mental moves)        └▶ project decision ──▶ your project notes
        ▲
   interests.md + taste graph (stances · negative filters · exemplars) steer every step

  /curate   vault-only idea mining        /research  web research filtered by your taste
  /journey  build-in-public log of what you shipped, broke and decided
```

## Commands

| Command | What it does |
|---------|--------------|
| `/ingest <source>` | Book / URL / notes → a framework note: principles, **executable mental moves**, when to apply, anti-patterns, genealogy |
| `/apply <framework> content\|code\|project [target]` | Framework → curation package, **site-replication build brief**, or proposed decision |
| `/curate [topic]` | Mines your whole vault for non-obvious, on-interest ideas, and lists what it rejected |
| `/research <topic>` | Web research → filter → signal notes + a curation package, with rejected sources listed |
| `/draft <note>` | Curation package or journey entry → thread draft, checked against X's character limits |
| `/ship <draft> [posted <url>]` | Stages copy-paste text, then logs it after you post. **Never posts for you.** |
| `/journey [what happened]` | Build-in-public entry with tweet candidates and a privacy filter |

### Example: steal like an artist, for websites
```
/ingest Steal Like an Artist by Austin Kleon
/apply steal-like-an-artist code https://some-awwwards-site.com https://a-portfolio-you-love.dev
```
→ `frameworks/briefs/<date>-<slug>-build-brief.md`: an element-by-element breakdown (layout, type, motion, interaction), what to steal (the mechanism) vs. transform (the expression), acceptance criteria and credits. Hand it to your coding agent.

## Python pipeline (multi-agent)

```bash
cd <vault>
python <engine>/scripts/pipeline.py list                     # pipelines, agents, routing
python <engine>/scripts/pipeline.py doctor                   # which agent CLIs actually work
python <engine>/scripts/pipeline.py ingest "Make it stick.md"   # vault note, URL, or book title
python <engine>/scripts/pipeline.py curate "agent memory"
python <engine>/scripts/pipeline.py research "temporal knowledge graphs" --agent agy
python <engine>/scripts/pipeline.py draft "<curation note>"
python <engine>/scripts/pipeline.py journey "what I shipped today"
python <engine>/scripts/pipeline.py replicate steal-like-an-artist https://a.com https://b.com         --goal "portfolio hero" --build ../my-site            # brief → code on a new branch, never committed
python <engine>/scripts/pipeline.py approve "<file>"          # the human gate
python <engine>/scripts/pipeline.py status | resume <run-id>
```

How it behaves:
- **Python runs the flow.** Each AI gets one narrow job and must return JSON that matches a schema.
- **Code checks the output:** schema, tweet length, and whether research links actually resolve. A failure gets one retry with the exact errors; if the agent is down, out of quota, or not logged in, the next agent takes over.
- **Everything lands as `status: pending_review`.** Nothing is published, committed or posted automatically.
- **Runs are saved** in `<vault>/.taste-engine/runs/`. A failed run resumes from where it stopped.

Agent CLIs (install whichever you have): [Claude Code](https://claude.com/claude-code), [Codex CLI](https://github.com/openai/codex), Antigravity CLI (`agy`), Gemini CLI. Route steps in `taste-engine.config.json`.

## Install (5 minutes)

Requirements: [Claude Code](https://claude.com/claude-code) and Python 3.10+.

```bash
git clone <this repo> taste-engine && cd taste-engine
python install.py --vault "/path/to/your/vault" --owner "Your Name"
```

Then:
1. Edit `<vault>/taste-engine/interests.md` with 3–7 topics you want to be known for.
2. Add a few stances and negative filters (`new_curation.py stance "..."`), or let `/ingest` and `/research` suggest them.
3. Open the vault in Claude Code and run `/ingest` on a book you love.

Re-running `install.py` updates commands, scripts, prompts, schemas and templates. It **never touches your notes** or your config choices.

### Options
| Flag | Default | |
|------|---------|--|
| `--engine-dir` | `taste-engine` | Folder for the taste graph + pipeline |
| `--frameworks-dir` | `frameworks` | Vault-wide frameworks (usable by all projects) |
| `--twitter-dir` | `Twitter` | Build-in-public journey |
| `--overmind-dir` | none | Optional: a goals/quests/log wiki. `/ship` and `/journey` will log there |
| `--x-char-limit` | `280` | Raise it if you have X Premium |

## What gets created in your vault

```
<vault>/
├── CLAUDE.md                       # a marked block telling Claude how the engine works
├── taste-engine.config.json
├── .claude/commands/*.md           # the 7 commands
├── .taste-engine/runs/             # pipeline run logs (resume from here)
├── frameworks/  (+ briefs/ sources/)  # extracted thinking, vault-wide
├── Twitter/  journey/ drafts/ ready/ posted.md
└── taste-engine/
    ├── interests.md
    ├── 01-taste-graph/  stances/ negative-filters/ exemplars/
    ├── 02-signals/      papers/ repos/ postmortems/ web/
    ├── 03-pipeline/     00-inbox/ 01-curation/ 02-drafts/ 03-ready-to-post/ 04-archive/
    ├── playbooks/  templates/  prompts/  schemas/
    └── scripts/   pipeline.py · new_curation.py · thread_validator.py
                   taste_engine/  orchestration/ knowledge/ tools/ actions/ pipelines/
```

## Scripts
```bash
python <engine>/scripts/new_curation.py framework "Deep Work" --source "Cal Newport"
python <engine>/scripts/new_curation.py signal "Some repo" --type repo
python <engine>/scripts/new_curation.py journey "Shipped v0.1"
python <engine>/scripts/thread_validator.py <draft.md>      # exits 1 if any tweet is too long
```

## Principles the engine holds itself to
- **The machine drafts, you decide.** Nothing auto-posts. Taste can't be outsourced.
- **Frameworks must be executable.** A summary isn't a framework; the mental moves are what count.
- **Steal from many, credit all.** Every brief and post names its sources.
- **Ship over structure.** Reorganizing your graph doesn't count as output.

See [`examples/`](examples/) for a sample framework (Steal Like an Artist, in the full schema).

## Contributing
Issues and PRs are welcome, especially new command modes for `/apply`, playbooks and framework examples.
If you contribute from your own vault, enable the privacy hook so personal notes never leak:
```bash
git config core.hooksPath .githooks
echo "your-private-project-name" >> .private-strings   # gitignored deny-list
```

## License
MIT
