# OverMind

**Turn what you read into how you work.**

**In plain words:** You give it a book, a website, a research paper, or a thread. It extracts *how that author thinks* and stores it as a reusable, executable framework. Later, you ask it to apply that framework to write high-signal content, produce a site-replication build brief for your coding agent ("build it like that site, but mine"), or think through a complex architectural decision. It lives inside your notes app, never posts anything automatically, and keeps your data strictly on your local machine.

An open-source agent harness and taste engine for your second brain (Obsidian or any markdown vault).

OverMind structures your work into **modular, composable blocks**:
- **Projects:** Active goals, build briefs, roadmaps, and journey logs.
- **Knowledge Base:** Your markdown vault, taste graph, stances, negative filters, and frameworks.
- **Tools:** Model adapters, scrapers, schema checkers, link verifiers, and validators.
- **Actions:** Human-approval gates, sandboxed git branches, and manual post stagers.

> **The Agent's Role:** The AI agent is not a rigid black box that traps your data — it is strictly an **orchestrator** that wires these blocks together in whatever sequence you need. OverMind can also be exposed as an **MCP (Model Context Protocol)** server to any coding agent (Claude Code, Cursor, Antigravity, Codex).

---

## Architecture: Composable Blocks & MCP

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            CODING AGENTS (CLIENTS)                           │
│        Claude Code   ·   Cursor   ·   Antigravity   ·   Codex   ·   CLI      │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                              MCP Protocol / CLI
                                       │
┌──────────────────────────────────────▼───────────────────────────────────────┐
│                              AGENT ORCHESTRATOR                              │
│         Wires blocks together · Manages flow · Enforces schemas & gates       │
└───────────┬────────────────────┬────────────────────┬────────────────────┬───┘
            │                    │                    │                    │
┌───────────▼────────┐   ┌───────▼────────┐   ┌───────▼────────┐   ┌───────▼────────┐
│     PROJECTS       │   │ KNOWLEDGE BASE │   │     TOOLS      │   │    ACTIONS     │
├────────────────────┤   ├────────────────┤   ├────────────────┤   ├────────────────┤
│ · Active Goals     │   │ · Vault Notes  │   │ · Web Scrapers │   │ · Human Gate   │
│ · Build Briefs     │   │ · Taste Graph  │   │ · Schema Check │   │ · Git Sandbox  │
│ · Decisions        │   │ · Stances      │   │ · Link Verifier│   │ · Note Writer  │
│ · Journey Ledger   │   │ · Frameworks   │   │ · Model Adapts │   │ · Staged Posts │
└────────────────────┘   └────────────────┘   └────────────────┘   └────────────────┘
            ▲                    ▲                    ▲                    ▲
            └────────────────────┴──────────┬─────────┴────────────────────┘
                                            │
                             COMPOSABLE BUILDING BLOCKS
                    (Plug and play in whatever order you want)
```

### The Four Blocks
1. **Projects:** Where your intent lives. Contains active goals, site-replication briefs, architectural decisions, and build-in-public logs.
2. **Knowledge Base:** Ground truth on disk. Your markdown second brain, taste graph (`interests.md`), stances (what you defend), negative filters (what you reject), and deconstructed thinking frameworks.
3. **Tools:** Pure, stateless instruments. Model adapters (`claude`, `codex`, `agy`), prompt templates, strict JSON schema validators, tweet length calculators, and URL link checkers.
4. **Actions:** Controlled side effects with built-in safety rails. Every output lands as `status: pending_review`, builds run on isolated git branches, and human approval is required before anything is final.

---

## The Loop

```
 [ SOURCES ] ───▶ [ /ingest ] ───▶ [ FRAMEWORKS ]
 (Books, URLs,                     (Mental moves &
  Papers, Code)                     principles)
                                         │
                                         ▼
                                   [ /apply ]
                                         │
                 ┌───────────────────────┼───────────────────────┐
                 │                       │                       │
                 ▼                       ▼                       ▼
          [ CODE BRIEFS ]       [ CONTENT PACKAGES ]     [ DECISIONS ]
                 │                       │                       │
                 ▼                       ▼                       ▼
          [ Coding Agent ]        [ Draft & Ship ]       [ Project Wiki ]
                 │                       │                       │
                 ▼                       ▼                       ▼
           Git Branch              Human Approval          Permanent Note
          (Sandboxed)              (Zero Auto-Post)          (Ground Truth)

 ─────────────────────────────────────────────────────────────────────────────
  STEERING FOUNDATION (Taste Graph): interests.md · Stances · Negative Filters
  FEEDBACK LOOP: /journey records real execution ──▶ compounds back into Taste
```

OverMind operates as a continuous learning loop across the blocks:
1. **Ingest (`/ingest`):** Pulls from **Sources** into the **Knowledge Base**, extracting mental moves and core principles.
2. **Steer (Taste Graph):** The **Knowledge Base** guides what is worth keeping, what gets mined (`/curate`), and what web noise gets rejected (`/research`).
3. **Apply (`/apply`):** Translates frameworks into target **Projects** (content packages, code build briefs, or decisions).
4. **Execute & Gate:** The **Agent Orchestrator** triggers **Tools** and **Actions** (coding agents build on git branches; threads are drafted for manual review).
5. **Feedback (`/journey`):** Real-world build results feed back into the **Knowledge Base**, updating your stances and taste.

---

## Commands

Run these directly inside your vault with Claude Code:

| Command | What it does | Blocks Used |
|---|---|---|
| `/ingest <source>` | Book / URL / notes → framework note: principles, **mental moves**, anti-patterns | Knowledge |
| `/apply <framework> content\|code\|project [target]` | Framework → curation package, **build brief**, or proposed decision | Knowledge → Projects |
| `/curate [topic]` | Mines vault for non-obvious ideas and records what was rejected | Knowledge |
| `/research <topic>` | Taste-filtered web research → signal notes + curation package | Tools → Knowledge |
| `/draft <note>` | Curation package or journey entry → thread draft (character-checked) | Projects → Tools |
| `/ship <draft> [posted <url>]` | Stages copy-paste text, logs post metrics. **Never posts for you.** | Actions |
| `/journey [what happened]` | Build-in-public entry with tweet candidates and privacy filtering | Projects → Actions |

### Example: Steal like an artist, for websites

```bash
/ingest Steal Like an Artist by Austin Kleon
/apply steal-like-an-artist code https://some-awwwards-site.com https://a-portfolio-you-love.dev
```

→ Generates `frameworks/briefs/<date>-<slug>-build-brief.md`: an element-by-element breakdown (layout, typography, motion, interaction), what to steal (the mechanism) vs. transform (the expression), acceptance criteria, and source credits. Hand it directly to your coding agent.

---

## Multi-Agent Pipeline & CLI

For automated runs, scheduled tasks, or using multiple AI models with failover:

```
 [ pipeline.py <command> ]
            │
            ▼
 ┌──────────────────────┐
 │ Context Assembly     │ ──▶ Budgeted tokens & strict privacy deny-list
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ Agent Dispatch       │ ──▶ Primary: Claude Code (Sonnet)
 └──────────┬───────────┘          │ (down / timeout / quota)
            │                      ▼
            │                 Fallback: Antigravity / Codex
            │
            ▼
 ┌──────────────────────┐
 │ Strict Validation    │ ──▶ Schema Check + Link Verifier + Char Counter
 └──────────┬───────────┘
            ├─── ✗ Invalid  ──▶ Retry 1x with exact error diagnostic
            └─── ✓ Valid
                    │
                    ▼
         ┌──────────────────────┐
         │ status: pending      │ ──▶ Written to Markdown vault
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ Human Approval Gate  │ ──▶ pipeline.py approve <file>
         └──────────────────────┘
```

```bash
cd <vault>
python <engine>/scripts/pipeline.py list                     # pipelines, agents, routing
python <engine>/scripts/pipeline.py doctor                   # verify installed agent CLIs
python <engine>/scripts/pipeline.py ingest "Make it stick.md"   # vault note, URL, or book title
python <engine>/scripts/pipeline.py curate "agent memory"
python <engine>/scripts/pipeline.py research "temporal knowledge graphs" --agent agy
python <engine>/scripts/pipeline.py draft "<curation note>"
python <engine>/scripts/pipeline.py journey "what I shipped today"
python <engine>/scripts/pipeline.py replicate steal-like-an-artist https://a.com https://b.com --goal "portfolio hero" --build ../my-site
python <engine>/scripts/pipeline.py approve "<file>"          # human gate
python <engine>/scripts/pipeline.py status | resume <run-id>
```

### Pipeline Guarantees
- **Python owns the flow:** Agent CLIs are isolated workers receiving structured prompts and returning strict JSON schemas.
- **Code-level validation:** Schemas, character limits, and web citations are verified programmatically. If invalid, the harness retries once with exact error diagnostics.
- **Cross-model failover:** If your primary agent is rate-limited, down, or unauthorized, the harness automatically falls back to your configured secondary agents (e.g., Claude → Antigravity → Codex).
- **Human-in-the-loop gate:** All generated notes land as `status: pending_review`. Nothing is published, committed, or posted automatically.
- **Resumable runs:** Run state is persisted to `.taste-engine/runs/`. Interrupted runs resume from the last successful step without redundant API costs.

Agent CLIs supported: [Claude Code](https://claude.com/claude-code), [Codex CLI](https://github.com/openai/codex), Antigravity CLI (`agy`), Gemini CLI. Configure routing in `taste-engine.config.json`.

---

## Supplying OverMind as MCP to Coding Agents

Because OverMind separates **Projects**, **Knowledge**, **Tools**, and **Actions** into clean modular interfaces, it can act as a **Model Context Protocol (MCP)** server:
- **Cursor / Windsurf / Claude Code / Antigravity** can connect to OverMind.
- Agents can query the **Knowledge Base** (stances, negative filters, frameworks) to guide design choices.
- Agents can read active **Projects** (build briefs, architectural decisions) to know what to build.
- Agents can trigger **Tools** (schema checkers, web research) and propose gated **Actions** (revising notes, sandboxed branches).

The coding agent remains the builder; OverMind provides the taste, context, and boundaries.

---

## Installation (5 Minutes)

**Prerequisites:** [Claude Code](https://claude.com/claude-code) and Python 3.10+.

```bash
git clone https://github.com/KaiwalPanchal/OverMind.git overmind && cd overmind
python install.py --vault "/path/to/your/vault" --owner "Your Name"
```

### Setup Steps:
1. Edit `<vault>/taste-engine/interests.md` with 3–7 topics you want to explore and be known for.
2. Seed initial stances and negative filters (`python new_curation.py stance "..."`), or allow `/ingest` and `/research` to propose them.
3. Open your vault in Claude Code and run `/ingest` on any book, paper, or article.

Re-running `install.py` updates commands, scripts, prompts, schemas, and templates. It **never modifies your existing notes** or configuration settings.

### Installation Options
| Flag | Default | Description |
|---|---|---|
| `--engine-dir` | `taste-engine` | Folder name for the taste graph, pipeline, and scripts |
| `--frameworks-dir` | `frameworks` | Vault-wide frameworks folder (shared across all projects) |
| `--twitter-dir` | `Twitter` | Build-in-public journey & tweet drafts folder |
| `--overmind-dir` | none | Optional: personal wiki / goals folder (`/ship` and `/journey` log here) |
| `--x-char-limit` | `280` | Character limit for social posts (e.g. increase for X Premium) |

---

## Vault Structure

```
<vault>/
├── CLAUDE.md                       # Marked instructions configuring Claude Code
├── taste-engine.config.json        # Path mappings and agent model routing
├── .claude/commands/*.md           # The 7 vault slash commands
├── .taste-engine/runs/             # Resumable pipeline run logs
├── frameworks/                     # Extracted thinking frameworks & build briefs
│   ├── briefs/
│   └── sources/
├── Twitter/                        # Build-in-public logs & drafts
│   ├── journey/
│   ├── drafts/
│   ├── ready/
│   └── posted.md
└── taste-engine/                   # The taste engine core
    ├── interests.md                # Topics you care about
    ├── 01-taste-graph/             # Stances · Negative-filters · Exemplars
    ├── 02-signals/                 # Papers · Repos · Postmortems · Web notes
    ├── 03-pipeline/                # Inbox → Curation → Drafts → Ready → Archive
    ├── playbooks/                  # Editorial lenses, thread templates, hooks
    ├── templates/                  # Framework & build-brief templates
    └── scripts/                    # pipeline.py, new_curation.py, thread_validator.py
```

---

## Core Principles

- **The machine drafts, you decide:** OverMind does not auto-post. Taste and judgment cannot be outsourced.
- **Frameworks must be executable:** Summaries are passive. Frameworks require concrete mental moves and application rules.
- **Steal from many, credit all:** Every build brief and post traces its genealogy and credits original creators.
- **Ship over structure:** Organizing your second brain is not output. Concrete drafts, briefs, and shipped work are.

See [`examples/`](examples/) for an end-to-end framework example (*Steal Like an Artist* by Austin Kleon).

---

## Contributing

Contributions, bug reports, and pull requests are welcome.

If contributing from your own vault, enable the pre-commit privacy hook:

```bash
git config core.hooksPath .githooks
echo "your-private-project-name" >> .private-strings   # Local gitignored deny-list
```

---

## License

[MIT](LICENSE) © 2026 OverMind Contributors
