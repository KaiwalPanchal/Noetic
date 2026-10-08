# OverMind Roadmap

> **Prime Directive:** Keep the owner moving toward the life they said they wanted, without adding to their administrative load.
> **Product Vision:** A lightweight, provider-neutral personal operating system, taste engine, and universal MCP server for markdown second brains.

---

## High-Level Milestone Tracker

| Phase | Milestone | Focus | Status |
|---|---|---|---|
| **Phase 1** | **Personal State Anchor & 2-Door OS** | Local CLI, Zen Web view, Door 1 clipper, Door 2 focus defense | **COMPLETED** |
| **Phase 2** | **Universal MCP Protocol Server** | Native MCP server connecting Claude Desktop, Cursor, and CLI tools | **COMPLETED** |
| **Phase 3** | **Single-Command Vault Installer** | `uvx` / curl / powershell 1-step installer into any Markdown vault | **COMPLETED** |
| **Phase 4** | **Public Packaging & PyPI Release** | Publish `overmind-engine` to PyPI (wheel + CI + release workflow done; the upload itself is the one manual step) | **READY TO PUBLISH** |
| **Phase 5** | **Autonomous Background Fleet** | Background Librarian for graph memory + on-demand Worker dispatch | **BUILT** |

---

## Detailed Phases

### Phase 1: Local State Anchor & 2-Door OS (Completed)
*Objective: Lower the cost of starting and the cost of coming back to zero.*

- [x] **Lightweight Subscription Harness:** Zero-token-cost local execution wrapping `agy` (Gemini 3.8) and `claude` CLI subscriptions with automatic fallback (`harness/`).
- [x] **Door 1 Quick Capture:**
  - Direct drop into vault [`inbox/`](inbox/).
  - CLI Web Clipper & Thought Capture: `overmind clip <url|text> [context]` with stateless HTML-to-Markdown cleaning, metadata extraction, and Obsidian YAML frontmatter.
- [x] **Door 2 Thinking Partner:**
  - `overmind think "<thought>"`: Stream-of-consciousness compressor returning Core Signal, Applied Framework, and bounded Next Action.
  - Sensei focus defense: intercepts off-focus tangents, safely parks them in [`ideas/PARKED.md`](ideas/PARKED.md), and redirects to the active commitment.
- [x] **Commitment Anchor (`overmind focus`):** Single verifiable commitment in [`wiki/focus.md`](wiki/focus.md); anti-drift guard alerts on 3+ switches in 7 days.
- [x] **Zen Web View (`overmind web`):** Localhost single-page dashboard at `http://127.0.0.1:8787` showing focus, stalest-first projects, parked tangents, live think box, and help recap.
- [x] **Onboarding & Recap:** `overmind help [topic]` and `overmind recap` showing recent log history and immediate next actions.

---

### Phase 2: Universal Model Context Protocol (MCP) Server (Completed)
*Objective: Allow any AI client (Claude Desktop, Claude Code, Cursor, Windsurf, Antigravity) to natively read and navigate OverMind.*

- [x] **Native MCP 2.x Server:** Implemented in [`overmind/mcp/server.py`](file:///C:/External%20Apps/overmind-taste-engine/overmind/mcp/server.py), executable via `overmind-mcp`.
- [x] **MCP Resources:**
  - `overmind://briefing`: Deterministic briefing of current focus, active projects, staleness, and gates.
  - `overmind://projects`: Active projects registry and metadata.
  - `overmind://stances`: Core engineering taste filters and principles.
  - `overmind://frameworks`: Available mental models in the vault.
  - `overmind://status`: Live operational health and recent run history.
- [x] **MCP Tools:**
  - `get_briefing()`: Deterministic project overview without LLM latency.
  - `list_projects()`: Reads project registry without exposing private profile notes.
  - `get_active_stances()`: Retrieves taste stances for content/code generation.
  - `inspect_code_safety()`: Pre-execution AST security validation.
  - `validate_thread()`: Checks character limits and link validity.
- [x] **Client Hook Configurations:** `overmind mcp-config --vault <path> [--client claude-desktop|claude-code|cursor|windsurf]` merges into each client's config without clobbering it.
- [x] **End-to-End Verification:** `test_mcp_stdio_handshake` spawns the real server and lists tools through the MCP client.

---

### Phase 3: Single-Command Installation & Vault Bootstrapping (Completed)
*Objective: Allow anyone with an Obsidian or Markdown vault to install OverMind in 10 seconds.*

- [x] **Core Installer Engine (`install.py`):**
  - Installs canonical commands, agent contracts, templates, and schemas into any target vault directory.
  - Idempotent: safe to run repeatedly; never overwrites existing user notes or edits outside managed markers.
  - `--with-wiki`: Optional scaffolding of generic OverMind wiki structure for new users.
- [x] **Multi-Agent Adapters (`overmind.adapters.sync`):**
  - Generates `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, and `.claude/` / `.gemini/` commands from canonical templates.
- [x] **Single-Command Web Launchers:**
  - Windows PowerShell:
    ```powershell
    irm https://raw.githubusercontent.com/KaiwalPanchal/OverMind/main/install.ps1 | iex
    ```
  - macOS / Linux:
    ```bash
    curl -sSL https://raw.githubusercontent.com/KaiwalPanchal/OverMind/main/install.sh | bash
    ```
- [x] **`uvx` / `pipx` Instant Runner:**
  - Run without installing globally:
    ```bash
    uvx overmind-engine install --vault "/path/to/vault"
    ```

---

### Phase 4: Public Packaging & PyPI Release (Ready to publish)
*Objective: Publish `overmind-engine` as a standard, distributable open-source Python package.*

- [x] **Package Configuration (`pyproject.toml`):** Configured for `overmind-engine` with MIT License and console scripts `overmind` and `overmind-mcp`.
- [x] **Test Suite Harmonization:** the 29 path-mismatch failures from the `engine/` -> `overmind/` + `workflows/` move are fixed; 245 tests pass.
- [x] **Multi-Version CI Matrix:** Verify GitHub Actions pass cleanly across Python 3.10, 3.11, 3.12, 3.13, and 3.14.
- [ ] **PyPI Publishing (manual last step: needs your PyPI trusted-publisher setup, then publish a GitHub release; `.github/workflows/release.yml` does the rest):**
  - Build source distribution and wheel: `python -m build`.
  - Publish to PyPI: `twine upload dist/*`.
- [x] **Public Documentation:**
  - Architecture overview and quickstart guide in `README.md`.
  - Terminal demo recordings demonstrating `overmind status`, `clip`, `think`, and MCP integration.

---

### Phase 5: Autonomous Background Fleet (Built)
*Objective: Transition from interactive sessions to proactive background assistance.*

- [x] **The Daily Librarian:**
  - `overmind librarian` (once per 24h; `--schedule` prints the Task Scheduler / cron line, installs nothing). Deterministic, no LLM: flags empty/duplicate inbox notes and suggests links, as a `pending_review` digest. It never moves, edits or deletes notes (framework extraction stays with `/ingest`).
- [x] **On-Demand Worker Agents:**
  - `overmind delegate <project> "<task>" [--test CMD] [--max-iterations N]`: worker agent in the project's repo on a fresh `overmind/...` branch, loops on the test command, never commits, logs to `wiki/log`.
- [x] **Active Repo Telemetry (CLI):** `overmind repos` and a REPOS section in `overmind status`. The Zen Web view in the vault harness does not show it yet.
  - Original scope:
  - Extends `overmind status` and Zen Web view to inspect real git status, uncommitted changes, and latest commits across all registered project workspaces.
