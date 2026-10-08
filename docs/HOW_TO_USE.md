# How to use OverMind

A practical guide: install it, connect your AI tools, and use it day to day. For the ideas behind it, read the [README](../README.md) and [PHILOSOPHY](../PHILOSOPHY.md). For internals, read [ARCHITECTURE](../ARCHITECTURE.md).

## What you get

OverMind installs into a folder of markdown notes (an Obsidian vault or any folder) and gives you:

| Piece | What it does |
|---|---|
| **Slash commands** | `/ingest`, `/apply`, `/curate`, `/research`, `/draft`, `/ship`, `/journey` for Claude Code, Gemini CLI, Codex and Antigravity. They are generated from one source, so every tool behaves the same. |
| **`overmind` CLI** | Install, sync, run pipelines, brief, check repos, triage your inbox, delegate work. |
| **MCP server** | Lets Claude Desktop, Claude Code, Cursor and Windsurf read your focus, projects and taste rules. |
| **Human gate** | Everything the machine writes lands as `status: pending_review`. You approve it. Nothing is posted or published for you. |

## 1. Install

You need Python 3.10+ and either [uv](https://docs.astral.sh/uv/) or pipx.

```bash
# macOS / Linux
curl -sSL https://raw.githubusercontent.com/KaiwalPanchal/OverMind/main/install.sh | bash -s -- --vault ~/my-vault

# Windows PowerShell
irm https://raw.githubusercontent.com/KaiwalPanchal/OverMind/main/install.ps1 | iex

# Any OS, nothing installed globally
uvx --from overmind-engine overmind install --vault /path/to/vault
```

Until the package is on PyPI, install from a checkout instead: `pip install -e .` then `overmind install --vault /path/to/vault`.

Useful flags (all optional):

| Flag | Meaning |
|---|---|
| `--owner "Ada"` | Your name, used on AI-written notes |
| `--agents claude,gemini` | Which tools get generated files. Default: claude, codex, gemini, antigravity. The choice is remembered. |
| `--with-wiki` | Also create the generic OverMind wiki (focus, projects, log). Never overwrites existing files. |
| `--engine-dir`, `--frameworks-dir`, `--twitter-dir`, `--overmind-dir` | Rename the folders OverMind uses |

Running the installer again is safe. It updates OverMind's own files and never touches your notes or the text you wrote in `CLAUDE.md` outside the marked block.

After installing:

1. Open `<vault>/taste-engine/interests.md` and write what you care about. Everything is curated against this.
2. Run `overmind doctor` to see which agent CLIs (claude, codex, agy, gemini) are found.

## 2. Connect your AI tools (MCP)

```bash
overmind mcp-config --vault /path/to/vault                  # every supported client
overmind mcp-config --vault /path/to/vault --client cursor  # one client
overmind mcp-config --vault /path/to/vault --dry-run        # preview only
```

Clients: `claude-desktop`, `claude-code`, `cursor` (`--scope global` for `~/.cursor`), `windsurf`. The command adds one `overmind` entry to each client's config and leaves everything else alone. If a config file is not valid JSON it is left untouched and reported. Restart the client afterwards.

What the client can then use:

- Resources: `overmind://briefing`, `overmind://projects`, `overmind://stances`, `overmind://frameworks`, `overmind://status`
- Tools: `get_briefing`, `list_projects`, `get_active_stances`, `inspect_code_safety`, `validate_thread`

The private profile folder is never exposed.

## 3. Everyday use

### Turn something you read into a framework

In Claude Code (or Gemini CLI, Codex, Antigravity), from the vault:

```
/ingest Steal Like an Artist
/ingest https://example.com/essay
/apply steal-like-an-artist  <your situation>
```

`/ingest` extracts how the author thinks into `frameworks/`. `/apply` uses a framework on your problem, for example to write a build brief for a coding agent.

### Curate and write

```
/curate agent memory          # what is worth your attention on a topic
/research temporal graphs     # sourced research with checked links
/draft <curation note>        # a thread draft (never posted for you)
/journey Shipped the pipeline # build-in-public log entry
/ship                         # validate and stage a draft in Twitter/ready/
```

You post by hand. OverMind never posts anywhere.

### Run the same jobs from the terminal

Pipelines run fixed steps and can route steps to different agents:

```bash
overmind run list                          # pipelines, agents, routing
overmind run ingest "Make it stick.md"
overmind run curate "agent memory"
overmind run research "temporal knowledge graphs" --agent agy
overmind run status                        # recent runs
overmind run resume <run-id>               # continue a failed run; finished steps are reused
```

### Review and approve

Machine output is `status: pending_review`. Read it, then:

```bash
overmind approve "frameworks/steal-like-an-artist.md"
overmind run reject "<file>" --reason "too generic"
```

`curated` is always your call. OverMind never marks anything curated for you.

### Briefing and projects

```bash
overmind briefing            # what is next, what is blocked, what is stale (no LLM needed)
overmind briefing --narrate  # same, written up by an agent
overmind projects            # project registry from <overmind>/wiki/projects
overmind repos               # live git status of every project that has a `repo:` field
overmind status              # recent runs plus the repo table
```

A project is a markdown file in `wiki/projects/` with front matter: `name`, `status` (active, blocked, parked...), `goal`, `competency`, `next_action`, `last_touched`, and optionally `repo` (absolute path, or relative to the vault), `gate`, `test`.

### Inbox librarian

```bash
overmind librarian --vault /path/to/vault           # runs at most once per 24h; --force to rerun
overmind librarian --vault /path/to/vault --schedule  # prints the Task Scheduler / cron line to paste
```

It reads `inbox/`, flags empty and duplicate notes, suggests `[[links]]` to existing notes, and writes a digest marked `pending_review`. It never moves, edits or deletes anything, and it installs no scheduled task itself.

### Delegate work to an agent

```bash
overmind delegate my-project "add input validation to the signup form" --test "pytest -q"
```

What happens: OverMind finds the project's repo, refuses if the working tree is dirty, creates a branch named `overmind/<project>-<task>-<id>`, runs an agent there, runs your test command, and feeds failures back (up to `--max-iterations`, default 3). It never commits or pushes. Review the diff, then commit or discard the branch yourself. The result is appended to `wiki/log/YYYY-MM.md`.

## 4. Keeping agent files in sync

`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.claude/commands/`, `.gemini/commands/` and `.agent/skills/` are generated. Do not edit the marked sections by hand. Regenerate with:

```bash
overmind sync --vault /path/to/vault               # all recorded agents
overmind sync --vault /path/to/vault --dry-run     # show what would change
overmind sync --vault /path/to/vault --agents claude,gemini
```

Text you wrote outside the marked block, and command files you wrote yourself, are preserved.

## 5. Configuration

`<vault>/taste-engine.config.json`:

```json
{
  "owner": "Ada",
  "agent": "Claude Code",
  "x_char_limit": 280,
  "paths": { "engine": "taste-engine", "frameworks": "frameworks", "twitter": "Twitter", "overmind": "OverMind" },
  "adapters": ["claude", "gemini"],
  "agents": ["claude", "codex", "agy"],
  "steps": { "research": "agy", "build": "codex" },
  "models": { "claude": "sonnet" },
  "private_paths": ["Journal", "Finance"]
}
```

- `agents` is the ordered list tried for every step; the next one is used when an agent is missing, out of quota or not logged in.
- `steps` pins a step to a specific agent.
- `private_paths` folders are never read as context.
- Set `TASTE_ENGINE_VAULT` to point the CLI at a vault from anywhere.

## 6. Troubleshooting

| Symptom | Fix |
|---|---|
| `Could not find taste-engine.config.json` | Run `overmind install --vault ...` first, run from inside the vault, or set `TASTE_ENGINE_VAULT`. |
| `doctor` shows an agent as not installed | Install that CLI, or remove it from `agents` in the config. At least one is needed for LLM steps. |
| Pipeline run failed | Read the error code, fix the cause, then `overmind run resume <run-id>`. |
| `DIRTY_WORKTREE` from `delegate` | Commit or stash the target repo's changes first. |
| MCP client does not show OverMind | Restart the client; check the file `mcp-config` printed; make sure `overmind-mcp` or `uvx` is on that client's PATH. |
| `mcp-config` reports an error for a client | That config file is not valid JSON. Fix or delete it, then rerun. |

## 7. Rules OverMind keeps

- It never posts to X/Twitter or any external service.
- AI-written notes carry `author: ai-agent` and start as `pending_review`.
- Private folders and the private profile are never read or quoted.
- Agent steps report what they could not do under "Agent notes" instead of improvising.
- Work in other repos happens on a new branch and is never committed or pushed.
