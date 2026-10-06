# OverMind

**Turn what you read into how you work.**

**In plain words:** You give it a book, a website, or a research paper. It extracts *how that author thinks* and stores it as a reusable, executable framework. Later, you ask it to apply that framework to produce a site-replication build brief for your coding agent ("build it like that site, but mine"), or think through a complex architectural decision. It lives inside your notes app, never posts anything automatically, and keeps your data strictly on your local machine.

An open-source agent harness and taste engine for your second brain (Obsidian or any markdown vault).

---

## Philosophy: You Are the Filter

> *"Thinking in frameworks is the most underrated skill of the AI age."*

### 1. AI Moved the Bottleneck to Taste
Learning from a book used to mean reading it twice, highlighting passages, and hoping some insight showed up when you needed it. Mostly it didn't.

Now, an agent can read any source, extract arguments, and summarize in seconds. Consuming, summarizing, and understanding content is basically solved.

**What's left is Taste:** knowing what to keep, what to reject, and what you are actually trying to build. That part is yours, and it is the only part that matters. What you reject (your negative filters) defines you more than what you hoard.

### 2. Evolutionary Loops: You Are the Selection Pressure
The more iterations a system runs, the faster it compounds toward excellence:
- **Nature:** variation → selection → repeat.
- **Machine Learning:** guess → measure loss → adjust → repeat.
- **Craft & Engineering:** draft → critique → revise → repeat.

OverMind optimizes for **cycle time and fast iteration loops**, not first-try perfection:
- **The machine generates the variations.** It drafts frameworks, outlines briefs, and proposes code replications.
- **You are the selection pressure.** Your taste, stances, and real-world judgment decide what survives into the next round.
- **Taste cannot be outsourced.** The machine drafts, you decide.

### 3. The Core Stances
- **Frameworks over summaries:** A summary sits passively on disk. A framework is executable — if you cannot apply it to a codebase, design, or decision, you didn't learn it.
- **Taste is subtraction:** What you reject defines your work. Negative filters protect your attention from noise and web sludge.
- **The machine drafts, you decide:** OverMind enforces zero automatic publishing. Human approval gates are mandatory before anything is permanent.
- **Iteration count beats first-draft quality:** Reps with rapid feedback beat endless planning.
- **Ship over structure:** Organizing your second brain is not output. Shipped code, published ideas, and completed briefs are.
- **Steal from many, credit all:** Every build brief traces its lineage and credits original creators.

Read the full philosophical grounding in [`PHILOSOPHY.md`](PHILOSOPHY.md) and the essay [*You Are the Filter*](essays/overmind-essay-my-voice-v2.md).

---

### Architecture: The 4 Primitives

OverMind unifies your work into **four core primitives**:
- **Projects:** Active goals, build briefs, ideas incubator, roadmaps, and domain applications (e.g. `projects/twitter/`, `ideas/`, site replication).
- **Knowledge Base:** Ground truth on disk — your local markdown vault, taste graph, stances, negative filters, and extracted thinking frameworks.
- **Tools:** Pure, stateless instruments — model adapters, scrapers, schema checkers, link verifiers, and the Web Clipper (`tools/clipper.py`).
- **Agents:** Autonomous intelligences and pipeline orchestrators (`compete`, `curate`, `research`, `ingest`, `goal-aligner`) bound by strict human-approval gates.

> **The Inception Loop:** OverMind is a self-bootstrapping meta-harness — **we use OverMind to design, test, and build OverMind itself.** Specific workflows (like Twitter build-in-public or competitor research) are not baked into the core engine; they are modular **projects** or **pipelines** running on top of it.
>
> **The Agent's Role:** Autonomous agents wire these primitives together. OverMind can also be exposed as an **MCP (Model Context Protocol)** server to any coding agent (Claude Code, Cursor, Antigravity, Codex).

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
│     PROJECTS       │   │ KNOWLEDGE BASE │   │     TOOLS      │   │     AGENTS     │
├────────────────────┤   ├────────────────┤   ├────────────────┤   ├────────────────┤
│ · OverMind Engine  │   │ · Vault Notes  │   │ · Model Adapts │   │ · Subagents    │
│ · Twitter Pack     │   │ · Taste Graph  │   │ · Schema Check │   │ · Goal Aligner │
│ · Ideas Incubator  │   │ · Stances      │   │ · Web Clipper  │   │ · Multi-model  │
│ · Build Briefs     │   │ · Frameworks   │   │ · Link Verifier│   │ · Human Gates  │
└────────────────────┘   └────────────────┘   └────────────────┘   └────────────────┘
            ▲                    ▲                    ▲                    ▲
            └────────────────────┴──────────┬─────────┴────────────────────┘
                                            │
                             COMPOSABLE BUILDING BLOCKS
                    (Plug and play in whatever order you want)
```

### The 4 Primitives
1. **Projects:** Where intent lives. Contains active goals, site-replication briefs, the ideas incubator (`ideas/`), and modular project packs (e.g. `projects/twitter/`).
2. **Knowledge Base:** Ground truth on disk. Your markdown second brain, taste graph (`interests.md`), stances (what you defend), negative filters (what you reject), and deconstructed thinking frameworks.
3. **Tools:** Pure, stateless instruments. Model adapters (`claude`, `codex`, `agy`), prompt templates, strict JSON schema validators, link checkers, and the stateless Web Clipper (`tools/clipper.py`).
4. **Agents:** Autonomous intelligences & pipelines. Multi-step pipelines (`compete`, `curate`, `research`, `ingest`, `replicate`) and specialized agents (e.g. `goal-aligner`) operating under human-in-the-loop review gates (`status: pending_review`).

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
          [ CODE BRIEFS ]       [ PROJECT DECISIONS ]     [ CONTENT / POSTS ]
        (Site Replication)       (OverMind Meta-Build)     (Your Project)  
                 │                       │                       │
                 ▼                       ▼                       ▼
          [ Coding Agent ]        [ Project Wiki ]        [ Review Stager ]
                 │                       │                       │
                 ▼                       ▼                       ▼
           Git Branch              Permanent Note          Human Approval
          (Sandboxed)              (Ground Truth)          (Zero Auto-Post)

 ─────────────────────────────────────────────────────────────────────────────
  STEERING FOUNDATION (Taste Graph): interests.md · Stances · Negative Filters
  FEEDBACK LOOP: real execution results ──▶ compound back into Taste
```

OverMind operates as a continuous learning loop across the blocks:
1. **Ingest (`/ingest`):** Pulls from **Sources** into the **Knowledge Base**, extracting mental moves and core principles.
2. **Steer (Taste Graph):** The **Knowledge Base** guides what is worth keeping, what gets mined (`/curate`), and what web noise gets rejected (`/research`).
3. **Apply (`/apply`):** Translates frameworks into target **Projects** (content packages, code build briefs, or decisions).
4. **Execute & Gate:** The **Agent Orchestrator** triggers **Tools** and **Actions** (coding agents build on git branches; content is drafted for manual review).
5. **Feedback:** Real-world build results feed back into the **Knowledge Base**, updating your stances and taste.

---

## Commands

Run these directly inside your vault with Claude Code:

| Command | What it does | Primitives Used |
|---|---|---|
| `/ingest <source>` | Book / URL / notes → framework note: principles, **mental moves**, anti-patterns | Knowledge |
| `/apply <framework> content\|code\|project [target]` | Framework → curation package, **build brief**, or proposed decision | Knowledge → Projects |
| `/curate [topic]` | Mines vault for non-obvious ideas and records what was rejected | Knowledge |
| `/research <topic>` | Taste-filtered web research → signal notes + curation package | Tools → Knowledge |

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
python <engine>/scripts/pipeline.py replicate steal-like-an-artist https://a.com https://b.com --goal "portfolio hero" --build ../my-site
python <engine>/scripts/pipeline.py approve "<file>"          # human gate
python <engine>/scripts/pipeline.py status | resume <run-id>
```

### Pipeline Guarantees
- **Python owns the flow:** Agent CLIs are isolated workers receiving structured prompts and returning strict JSON schemas.
- **Code-level validation:** Schemas and web citations are verified programmatically. If invalid, the harness retries once with exact error diagnostics.
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

### Extensibility: Domain Tools & Project Packs

OverMind is modular by design. You can attach domain-specific tools and project packs without bloating the core engine:
- **Web Clipper Tool (`taste_engine/tools/clipper.py`):** Pure, stateless tool that ingests web DOM and articles, returning structured Markdown signal notes directly to your Knowledge Base (`02-signals/web/` or `/ingest`).
- **Project Packs (`projects/<name>/`):** Self-contained applications (such as `projects/twitter/`) bringing their own commands, prompts, schemas, and pipelines that install cleanly into your vault.
- **Environment & Secrets (`.env`):** Optional API keys and external endpoints live in `.env`, which is strictly git-ignored and never committed.

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
4. *(Optional)* If using external modules (such as the MongoDB Web Clipper), copy `.env.example` to `.env` and configure your credentials.

Re-running `install.py` updates commands, scripts, prompts, schemas, and templates. It **never modifies your existing notes** or configuration settings.

### Installation Options
| Flag | Default | Description |
|---|---|---|
| `--engine-dir` | `taste-engine` | Folder name for the taste graph, pipeline, and scripts |
| `--frameworks-dir` | `frameworks` | Vault-wide frameworks folder (shared across all projects) |
| `--overmind-dir` | none | Optional: personal wiki / goals folder |

---

## Vault Structure

```
<vault>/
├── CLAUDE.md                       # Marked instructions configuring Claude Code
├── taste-engine.config.json        # Path mappings and agent model routing
├── .env.example                    # Template for module secrets (e.g. MONGODB_URI)
├── .claude/commands/*.md           # The vault slash commands
├── .taste-engine/runs/             # Resumable pipeline run logs
├── frameworks/                     # Extracted thinking frameworks & build briefs
│   ├── briefs/
│   └── sources/
└── taste-engine/                   # The taste engine core
    ├── interests.md                # Topics you care about
    ├── 01-taste-graph/             # Stances · Negative-filters · Exemplars
    ├── 02-signals/                 # Papers · Repos · Postmortems · Web notes
    ├── 03-pipeline/                # Inbox → Curation → Drafts → Ready → Archive
    ├── playbooks/                  # Editorial lenses and reusable playbooks
    ├── templates/                  # Framework & build-brief templates
    └── scripts/                    # pipeline.py, new_curation.py
```

---

## Further Reading & Examples

- **The Philosophy in Full:** [`PHILOSOPHY.md`](PHILOSOPHY.md) covers why thinking in frameworks is the defining skill of the AI age, and why AI moved the bottleneck to taste.
- **The Long Essay:** [*You Are the Filter*](essays/overmind-essay-my-voice-v2.md) dives deep into evolutionary loops and selection pressure.
- **End-to-End Walkthrough:** See [`examples/`](examples/) for a complete framework extraction and application from Austin Kleon's *Steal Like an Artist*.

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
