# Architecture

The Taste Engine is a **framework**, not a fixed app. It has four layers, and every future feature (a new pipeline, tool, agent or action) has a clear home in one of them.

```
                      ┌──────────────────────────────────────────┐
  you / Claude Code ─▶│  ORCHESTRATION  (the planner)            │
  python pipeline.py  │  registry · runs on disk · agent steps   │
                      │  route → call → validate → retry → fall back
                      └───────┬──────────────┬──────────────┬────┘
                              │              │              │
                 ┌────────────▼───┐  ┌───────▼───────┐  ┌───▼────────────┐
                 │   KNOWLEDGE    │  │     TOOLS     │  │    ACTIONS     │
                 │  the vault     │  │  instruments  │  │  side effects  │
                 │  config        │  │  agent CLIs   │  │  human gate    │
                 │  context       │  │  prompts      │  │  git branches  │
                 │  notes         │  │  validators   │  │  (future: more)│
                 └────────────────┘  └───────────────┘  └────────────────┘
```

Code lives in `engine/scripts/taste_engine/`:

| Layer | Folder | What it owns | Rule |
|---|---|---|---|
| **Orchestration** | `orchestration/` | `registry.py` (pipelines register here), `run.py` (run state, pause/resume), `steps.py` (the agent step), `cli.py` | Control flow is plain Python. LLM calls are isolated steps, never an open-ended loop. |
| **Knowledge** | `knowledge/` | `config.py` (paths), `context.py` (what a model may see), `notes.py` (writing results as notes) | Markdown is the source of truth. Any index or cache must be rebuildable from the `.md` files. Private folders are never read. |
| **Tools** | `tools/` | `agents.py` (claude · codex · agy · gemini), `prompts.py`, `schema_check.py`, `tweets.py`, `links.py` | Tools are plain functions with no control flow. Swappable. |
| **Actions** | `actions/` | `gate.py` (approve/reject), `git.py` (branch in a target repo) | Anything public or irreversible needs `status: approved` first. Prefer the reversible version (a branch, not a commit). Posting stays manual. |
| **Pipelines** | `pipelines/` | One file each: `ingest`, `curate`, `research`, `draft`, `journey`, `replicate` | A pipeline composes the four layers and registers with `@pipeline(...)`. |

Dependency direction: **pipelines → orchestration → tools / actions → knowledge**. Lower layers never import higher ones.

Prompts (`engine/prompts/*.md`) and output schemas (`engine/schemas/*.json`) are plain files. They're versioned like code and editable without touching Python.

## How a pipeline runs

```
python pipeline.py draft "curation-004-….md"

 run 20261006-0539-draft-…           ← run state: <vault>/.taste-engine/runs/<id>.json
   ▸ draft                            ← agent step
       build context (knowledge)      ← budgeted, privacy-filtered
       render prompt (tools)          ← engine/prompts/draft.md
       call agent per routing         ← config: agents.draft = claude
       validate: schema + extra       ← schema_check + tweet length (code, not vibes)
       ✗ invalid → retry once with the exact errors
       ✗ agent down / quota / auth → next agent in agents.fallback
   ▸ write                            ← Python writes the note, status: pending_review
 ✓ Done → you review → pipeline.py approve <file>
```

If any step fails, the run stops with a compact error (e.g. `{"code": "DIRTY_WORKTREE", …}`). Fix the cause, then `pipeline.py resume <run-id>`. Finished steps are reused, not paid for twice.

## Two ways to drive it

| | Claude Code commands (`/ingest`, `/draft`, …) | Python pipeline (`pipeline.py ingest …`) |
|---|---|---|
| Who's in charge | Claude, following the command's prompt | Python, following fixed steps |
| Best for | interactive work, conversation, judgment calls | repeatable runs, mixing agents, scheduling later |
| Agents | Claude | claude · codex · agy · gemini, routed per step |
| Output | notes (`draft-for-review`) | notes (`pending_review`) plus run logs |

Both write to the same vault folders.

## Extending it

**A new pipeline** (e.g. a knowledge pipeline that indexes or organizes the vault):
```python
# engine/scripts/taste_engine/pipelines/index.py
from taste_engine.knowledge import context
from taste_engine.orchestration.registry import arg, pipeline

@pipeline("index", kind="knowledge", help="rebuild the vault index", args=[arg("--full", action="store_true")])
def index(run, a):
    notes = run.step("scan", lambda: [str(p) for p in context.iter_notes(run.cfg)])
    ...
    return [run.output(path)]
```
It shows up in `pipeline.py list` and `--help` automatically. If it uses an LLM, add `engine/prompts/index.md` and `engine/schemas/index.json`, call `agent_step(...)`, and optionally route it in config (`"agents": {"index": "claude"}`).

**A new agent CLI:** in `tools/agents.py`, write `fn(prompt, schema, cwd, web, write, timeout, model) -> AgentResult` and decorate it with `@adapter("name")`.

**A new tool:** add a module to `tools/` with plain functions (e.g. a DOM scraper, an embedding index client).

**A new action:** add a module to `actions/`. Call `gate.require_approved(note)` before doing anything public.

## Configuration (`<vault>/taste-engine.config.json`)

```json
{
  "owner": "Ada",
  "agent": "Claude Code",
  "x_char_limit": 280,
  "paths": { "engine": "taste-engine", "frameworks": "frameworks", "twitter": "Twitter", "overmind": null },
  "agents": { "ingest": "claude", "research": "agy", "draft": "claude", "deconstruct": "claude", "build": "codex",
              "fallback": ["claude", "agy", "codex"] },
  "models": { "claude": "sonnet" },
  "private_paths": ["Journal", "Finance"]
}
```

## Agent notes (as tested Oct 2026)
- **claude**: `claude -p --json-schema`, run lean (no user plugins/MCP/skills). About $0.02–0.12 per step on Sonnet.
- **codex**: `codex exec --output-schema`. Strict schemas (all fields required, no extras). Free tiers hit usage limits quickly, and fallback covers that.
- **agy** (Antigravity): `agy -p --json-schema`. Doesn't read prompts from stdin, so the prompt is passed as a file. Good at web research, but slow (minutes).
- **gemini**: the Gemini CLI no longer works with individual Google accounts (Google points people to Antigravity). The adapter remains for API-key users.

## The 12-factor mapping
| Factor | Where |
|---|---|
| 1 NL → tool calls | each agent step returns schema JSON, never free text |
| 2 Own your prompts | `engine/prompts/` |
| 3 Own your context window | `knowledge/context.py` budgets |
| 4 Tools are structured outputs | `engine/schemas/` + `tools/schema_check.py` |
| 5 Unify state | notes carry `status` + `run` id; the vault is the database |
| 6 Pause / resume | `.taste-engine/runs/` + `resume` |
| 7 Contact humans | `pending_review` → `approve` / `reject` (`actions/gate.py`) |
| 8 Own your control flow | pipelines are fixed Python step sequences |
| 9 Compact errors | `{"code": …, "detail": …}` diagnostics, fed back on retry |
| 10 Small focused agents | one narrow job per step, routed per step |
| 11 Trigger from anywhere | Claude Code commands + CLI (cron and folder-drop triggers: future) |
| 12 Stateless reducer | each step = f(context, input) → JSON; state lives in the run file |
