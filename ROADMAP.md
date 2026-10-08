# Noetic Roadmap

> **Prime Directive:** Keep the owner moving toward the life they said they wanted, without adding to their administrative load.
> **Product Vision:** A lightweight, provider-neutral personal operating system, taste engine, and universal MCP server for markdown second brains.

---

## High-Level Milestone Tracker

| Phase | Milestone | Focus | Status |
|---|---|---|---|
| **Phase 1** | **Personal State Anchor & 2-Door OS** | Local CLI, Zen Web view, Door 1 clipper, Door 2 focus defense | **PACKAGED (web view in vault)** |
| **Phase 2** | **Universal MCP Protocol Server** | Native MCP server connecting Claude Desktop, Cursor, and CLI tools | **COMPLETED** |
| **Phase 3** | **Single-Command Vault Installer** | `uvx` / curl / powershell 1-step installer into any Markdown vault | **COMPLETED** |
| **Phase 4** | **Public Packaging & PyPI Release** | Publish `noetic-cli` to PyPI (wheel + CI + release workflow done; the upload itself is the one manual step) | **READY TO PUBLISH** |
| **Phase 5** | **Autonomous Background Fleet** | Background Librarian for graph memory + on-demand Worker dispatch | **BUILT** |
| **Phase 6** | **Agent Spec + Loop + Taste + Liminal** | Declarative AgentSpec, bounded run_loop, deterministic taste gate, Liminal sidecar | **COMPLETED** |

---

## Detailed Phases

### Phase 1: Local State Anchor & 2-Door OS (Packaged; web view remains in vault)
> `clip`, `think`, and `focus` are packaged in `noetic` (`workflows/sensei`, `workflows/capture`). The Zen web view remains in the vault's `OverMind/harness/web.py`.
*Objective: Lower the cost of starting and the cost of coming back to zero.*

- [x] **Lightweight Subscription Harness:** Zero-token-cost local execution wrapping `agy` (Gemini 3.8) and `claude` CLI subscriptions with automatic fallback (`noetic/agents/runners.py`).
- [x] **Door 1 Quick Capture:**
  - Direct drop into vault [`inbox/`](inbox/).
  - CLI Web Clipper & Thought Capture: `noetic clip <url|text> [context]` packaged in `workflows/capture/workflow.py` with stateless HTML-to-Markdown cleaning, metadata extraction, and Obsidian YAML frontmatter.
- [x] **Door 2 Thinking Partner:**
  - `noetic run think "<thought>"`: Stream-of-consciousness compressor returning Core Signal, Applied Framework, and bounded Next Action.
  - Sensei focus defense: intercepts off-focus tangents, safely parks them in [`ideas/PARKED.md`](ideas/PARKED.md), and redirects to the active commitment.
- [x] **Commitment Anchor (`noetic focus`):** Single verifiable commitment in [`wiki/focus.md`](wiki/focus.md); anti-drift guard alerts on 3+ switches in 7 days.
- [ ] **Zen Web View (`noetic web`):** Localhost single-page dashboard at `http://127.0.0.1:8787` (remains vault-only in `OverMind/harness/web.py`; not yet packaged).
- [x] **Onboarding & Recap:** `noetic help [topic]` and `noetic recap` in vault harness; CLI command help across all surfaces.

---

### Phase 2: Universal Model Context Protocol (MCP) Server (Completed)
*Objective: Allow any AI client (Claude Desktop, Claude Code, Cursor, Windsurf, Antigravity) to natively read and navigate Noetic.*

- [x] **Native MCP 2.x Server:** Implemented in [`noetic/mcp/server.py`](noetic/mcp/server.py), executable via `noetic-mcp`.
- [x] **MCP Resources:**
  - `noetic://briefing`: Deterministic briefing of current focus, active projects, staleness, and gates.
  - `noetic://projects`: Active projects registry and metadata.
  - `noetic://stances`: Core engineering taste filters and principles.
  - `noetic://frameworks`: Available mental models in the vault.
  - `noetic://status`: Live operational health and recent run history.
- [x] **MCP Tools:**
  - `get_briefing()`: Deterministic project overview without LLM latency.
  - `list_projects()`: Reads project registry without exposing private profile notes.
  - `get_active_stances()`: Retrieves taste stances for content/code generation.
  - `inspect_code_safety()`: Pre-execution AST security validation.
  - `validate_thread()`: Checks character limits and link validity.
- [x] **Client Hook Configurations:** `noetic mcp-config --vault <path> [--client claude-desktop|claude-code|cursor|windsurf]` merges into each client's config without clobbering it.
- [x] **End-to-End Verification:** `test_mcp_stdio_handshake` spawns the real server and lists tools through the MCP client.

---

### Phase 3: Single-Command Installation & Vault Bootstrapping (Completed)
*Objective: Allow anyone with an Obsidian or Markdown vault to install Noetic in 10 seconds.*

- [x] **Core Installer Engine (`install.py`):**
  - Installs canonical commands, agent contracts, templates, and schemas into any target vault directory.
  - Idempotent: safe to run repeatedly; never overwrites existing user notes or edits outside managed markers.
  - `--with-wiki`: Optional scaffolding of generic Noetic wiki structure for new users.
- [x] **Multi-Agent Adapters (`noetic.adapters.sync`):**
  - Generates `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, and `.claude/` / `.gemini/` commands from canonical templates.
- [x] **Single-Command Web Launchers:**
  - Windows PowerShell:
    ```powershell
    irm https://raw.githubusercontent.com/KaiwalPanchal/Noetic/main/install.ps1 | iex
    ```
  - macOS / Linux:
    ```bash
    curl -sSL https://raw.githubusercontent.com/KaiwalPanchal/Noetic/main/install.sh | bash
    ```
- [x] **`uvx` / `pipx` Instant Runner:**
  - Run without installing globally:
    ```bash
    uvx noetic-cli install --vault "/path/to/vault"
    ```

---

### Phase 4: Public Packaging & PyPI Release (Ready to publish)
*Objective: Publish `noetic-cli` as a standard, distributable open-source Python package.*

- [x] **Package Configuration (`pyproject.toml`):** Configured for `noetic-cli` with MIT License and console scripts `noetic` and `noetic-mcp`.
- [x] **Test Suite Harmonization:** the 29 path-mismatch failures from the `engine/` -> `noetic/` + `workflows/` move are fixed; 245 tests pass.
- [x] **Multi-Version CI Matrix:** Verify GitHub Actions pass cleanly across Python 3.10, 3.11, 3.12, 3.13, and 3.14.
- [ ] **PyPI Publishing (manual last step: needs your PyPI trusted-publisher setup, then publish a GitHub release; `.github/workflows/release.yml` does the rest):**
  - Build source distribution and wheel: `python -m build`.
  - Publish to PyPI: `twine upload dist/*`.
- [x] **Public Documentation:**
  - Architecture overview and quickstart guide in `README.md`.
  - Terminal demo recordings demonstrating `noetic status`, `clip`, `think`, and MCP integration.

---

### Phase 5: Autonomous Background Fleet (Built)
*Objective: Transition from interactive sessions to proactive background assistance.*

- [x] **The Daily Librarian:**
  - `noetic librarian` (once per 24h; `--schedule` prints the Task Scheduler / cron line, installs nothing). Deterministic, no LLM: flags empty/duplicate inbox notes and suggests links, as a `pending_review` digest. It never moves, edits or deletes notes (framework extraction stays with `/ingest`).
- [x] **On-Demand Worker Agents:**
  - `noetic delegate <project> "<task>" [--test CMD] [--max-iterations N]`: worker agent in the project's repo on a fresh `noetic/...` branch, loops on the test command, never commits, logs to `wiki/log`.
- [x] **Active Repo Telemetry (CLI):** `noetic repos` and a REPOS section in `noetic status`. The Zen Web view in the vault harness does not show it yet.
  - Original scope:
  - Extends `noetic status` and Zen Web view to inspect real git status, uncommitted changes, and latest commits across all registered project workspaces.

---

### Phase 6: Agent Spec + Loop + Taste + Liminal Sidecar (Completed)
*Objective: Full agent-agnostic harness with declarative specs, bounded loops, pre-write taste gating, and optional graph memory.*

- [x] **Declarative Agent Specs (`noetic/agents/spec.py`):**
  - Markdown agent contracts in `workflows/*/agents/<name>.md` with YAML frontmatter.
  - Strict input/output JSON schemas, registered tool capabilities, and event hooks.
  - CLI commands: `noetic agents`, `noetic agent <name>`, and `noetic fire <event>`.
  - Sensei (`workflows/sensei/`), Capture (`workflows/capture/`), and Fleet Librarian/Worker specs.
- [x] **Bounded Execution Loops (`noetic/orchestration/loop.py`):**
  - `run_loop(act, evaluate, max_iterations, budget_usd)` bounding multi-turn agent execution.
  - Distinct step tracking (`<name>-act-N`, `<name>-eval-N`) preserving resume cache.
  - `workflows/fleet/delegate.py` refactored onto `run_loop`.
- [x] **Deterministic Taste Gate (`noetic/gates/taste.py`):**
  - Evaluates `.noetic/taste/anti-patterns.md` (banned phrases and regex patterns) and `.noetic/taste/dogmas.md`.
  - Integrated into `agent_step` before notes are written; retries with exact JSONPath violations.
  - CLI commands `noetic taste check` and `noetic taste show`; MCP tool `check_taste`.
- [x] **Optional Liminal Sidecar Client (`noetic/knowledge/liminal.py`, `recall.py`):**
  - Sidecar client talking to Liminal (`liminalfinal`) backend over HTTP on port 8000.
  - Unified `recall(cfg, question)` with pass-through of `REFUSED_INSUFFICIENT_CONTEXT` and vault-grep fallback.
  - Opt-in Librarian push (`noetic librarian --liminal`) with SHA-1 deduplication in `.noetic/liminal.json`.
  - CLI commands `noetic recall` and `noetic liminal`; MCP tool `recall`.

