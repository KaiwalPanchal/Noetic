"""Modern Typer CLI for OverMind Taste Engine.

Unifies developer tooling, MCP server launcher, evaluation suite,
and pipeline orchestration under clean developer ergonomics.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
  sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
  sys.stderr.reconfigure(encoding="utf-8")

from rich.console import Console
from rich.table import Table
import typer

from overmind.knowledge.config import load_config
from overmind.gates.policy_gate import validate_python_ast

app = typer.Typer(
    name="overmind",
    help="OverMind: Autonomous agent harness, MCP protocol server, and taste engine for knowledge vaults.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def doctor():
  """Verifies installed LLM CLIs, MCP server readiness, and security policy gates."""
  from overmind.agents.runners import available, known_agents

  console.print("[bold cyan]Running OverMind System Diagnostic & Health Check...[/bold cyan]\n")

  # 1. Check Configuration & Vault
  cfg = None
  try:
    cfg = load_config()
    console.print(f"[green][OK][/green] Vault located at: [bold]{cfg.vault}[/bold] (Owner: {cfg.owner})")
  except (Exception, SystemExit) as e:
    console.print(f"[yellow][!][/yellow] Vault configuration note: {e}")

  # 2. Check Agent CLIs
  agent_table = Table(title="Agent CLI Adapters")
  agent_table.add_column("Agent", style="cyan")
  agent_table.add_column("Installed", style="magenta")
  agent_table.add_column("Status", style="green")

  for name in known_agents(cfg.commands if cfg else None):
    is_avail = available(name, cfg.commands if cfg else None)
    status_str = "Ready" if is_avail else "Not on PATH"
    agent_table.add_row(name, "[OK]" if is_avail else "[X]", status_str)

  console.print(agent_table)

  # 3. Check MCP Server Readiness
  try:
    from overmind.mcp.server import create_mcp_server
    server = create_mcp_server()
    console.print(f"[green][OK][/green] Model Context Protocol (MCP) Server: [bold]Ready[/bold] ({server.name} v{server.version})")
  except Exception as e:
    console.print(f"[red][X][/red] MCP Server Error: {e}")

  # 4. Check Security Policy Gate
  try:
    validate_python_ast("print('Safe test string')")
    console.print("[green][OK][/green] Security Policy Gate: [bold]Active[/bold] (AST validation operational)")
  except Exception as e:
    console.print(f"[red][X][/red] Security Gate Error: {e}")

  console.print("\n[bold green]System diagnostic complete.[/bold green]")


@app.command()
def mcp(
    transport: str = typer.Option("stdio", "--transport", "-t", help="MCP transport: stdio, sse, streamable-http"),
    vault: str = typer.Option(None, "--vault", help="Path to markdown vault"),
    port: int = typer.Option(8000, "--port", "-p", help="Port for SSE/HTTP transport"),
):
  """Starts the native Model Context Protocol (MCP) server."""
  from overmind.mcp.server import create_mcp_server

  vault_path = Path(vault).resolve() if vault else None
  server = create_mcp_server(vault_path)
  console.print(f"[bold cyan]Starting OverMind MCP Server (transport: {transport})...[/bold cyan]")
  if transport == "stdio":
    server.run(transport="stdio")
  elif transport == "sse":
    server.run(transport="sse", port=port)
  else:
    server.run(transport="streamable-http", port=port)


@app.command("mcp-config")
def mcp_config(
    vault: str = typer.Option(..., "--vault", help="Vault root the MCP server should serve"),
    client: str = typer.Option("all", "--client", "-c", help="claude-desktop | claude-code | cursor | windsurf | all"),
    scope: str = typer.Option("project", "--scope", help="Cursor only: project (<vault>/.cursor) or global (~/.cursor)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be written; change nothing"),
):
  """Adds OverMind to your AI client's MCP config (merges; never clobbers other servers)."""
  from overmind.mcp.clients import CLIENTS, write_client

  root = Path(vault).expanduser().resolve()
  if not root.is_dir():
    console.print(f"[red]Vault not found:[/red] {root}")
    raise typer.Exit(code=2)
  names = list(CLIENTS) if client == "all" else [client]
  failed = False
  for name in names:
    try:
      r = write_client(name, root, scope, dry_run)
    except ValueError as e:
      console.print(f"[red]{e}[/red]")
      raise typer.Exit(code=2)
    failed |= r.action == "error"
    typer.echo(f"{r.client:<15} {r.action:<9} {r.path}{'  ' + r.detail if r.detail else ''}")
  if failed:
    raise typer.Exit(code=1)


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True, "help_option_names": []})
def install(ctx: typer.Context):
  """Installs/updates OverMind into a vault (same flags as install.py: --vault, --owner, --agents, --with-wiki ...)."""
  from overmind.installer import main as install_main

  install_main(list(ctx.args))


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True, "help_option_names": []})
def run(ctx: typer.Context):
  """Runs a pipeline: `overmind run list | ingest <src> | curate <topic> | research <topic> | replicate ... | approve <file> | resume <id>`."""
  from overmind.orchestration.cli import main as pipeline_main

  sys.argv = ["overmind run", *ctx.args]
  pipeline_main()


@app.command()
def eval(
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress detailed output"),
    extractor: str = typer.Option(None, "--extractor", "-e", help="module:callable to grade (default: rule-based baseline)"),
    dataset: str = typer.Option("golden", "--dataset", "-d", help="golden | heldout | path to a JSON file"),
    output: str = typer.Option(None, "--output", "-o", help="Write JSON results to this path"),
    threshold: float = typer.Option(None, "--threshold", help="F1 gate (default: built-in floor)"),
):
  """Grades an extractor (default: rule-based baseline, NOT an LLM) on a labelled dataset."""
  from overmind.evals.extractors import load_extractor
  from overmind.evals.run_evals import DATASET_PATH, F1_REGRESSION_THRESHOLD, HELDOUT_PATH, run_evaluations

  gate = F1_REGRESSION_THRESHOLD if threshold is None else threshold
  path = {"golden": DATASET_PATH, "heldout": HELDOUT_PATH}.get(dataset, dataset)
  metrics, passed = run_evaluations(
      extractor=load_extractor(extractor) if extractor else None,
      quiet=quiet, output=output, threshold=gate, dataset_path=path)
  if passed:
    console.print(f"[bold green]GATE PASSED:[/bold green] F1 {metrics['f1']:.3f} >= {gate}")
  else:
    console.print(f"[bold red]GATE FAILED:[/bold red] F1 {metrics['f1']:.3f} < {gate}")
    raise typer.Exit(code=1)


@app.command()
def sync(
    vault: str = typer.Option(..., "--vault", help="Vault root to generate agent adapters into"),
    agents: str = typer.Option(None, "--agents", help="Comma list: claude,codex,gemini,antigravity,universal (default: the vault config, else the four main ones)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Report what would change; write nothing"),
):
  """Generates CLAUDE.md / AGENTS.md / GEMINI.md and per-agent command files from the canonical sources."""
  from overmind.adapters.sync import sync as run_sync

  root = Path(vault).expanduser().resolve()
  if not root.is_dir():
    console.print(f"[red]Vault not found:[/red] {root}")
    raise typer.Exit(code=2)
  try:
    report = run_sync(root, [a for a in agents.split(",") if a] if agents else None, dry_run=dry_run)
  except (ValueError, FileNotFoundError) as e:
    console.print(f"[red]sync failed:[/red] {e}")
    raise typer.Exit(code=2)
  typer.echo(f"agents: {', '.join(report.agents)}{' (dry run)' if dry_run else ''}")
  for f in report.files:
    typer.echo(f"  {f.action:<9} {f.path}")
  for n in report.notes:
    typer.echo(f"  note: {n}")
  typer.echo(f"{report.summary()}")


@app.command()
def status(
    run_id: str = typer.Argument(None, help="Optional specific run ID to inspect"),
):
  """Inspects pipeline execution status and run logs."""
  cfg = load_config()
  from overmind.orchestration.cli import show_status
  show_status(cfg, run_id)
  if not run_id:
    from overmind.knowledge import repos
    typer.echo("\nREPOS\n" + repos.render_repo_telemetry(repos.load_repo_telemetry(cfg)))


@app.command()
def approve(
    file_path: str = typer.Argument(..., help="Path to pending note to approve"),
):
  """Approves a pending generated note through the human gate."""
  cfg = load_config()
  from overmind.knowledge.context import resolve_vault_path
  from overmind.gates import gate

  path = resolve_vault_path(cfg, file_path)
  if not path:
    console.print(f"[red]Not found:[/red] {file_path}")
    raise typer.Exit(code=1)
  gate.approve(path)
  console.print(f"[green]✓ Approved:[/green] {path.relative_to(cfg.vault)} → status: approved")


# Workflows (briefing, projects, validate-thread, ...) add their own commands through the loader.
from overmind.orchestration.loader import load_workflows  # noqa: E402
from overmind.orchestration import registry as _pipeline_registry  # noqa: E402

load_workflows(app, _pipeline_registry)


if __name__ == "__main__":
  app()
