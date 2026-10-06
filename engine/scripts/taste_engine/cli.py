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

from taste_engine.knowledge.config import load_config
from taste_engine.security.policy_gate import validate_vault_path, validate_python_ast, SecurityViolation

app = typer.Typer(
    name="overmind",
    help="OverMind: Autonomous agent harness, MCP protocol server, and taste engine for knowledge vaults.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def doctor():
  """Verifies installed LLM CLIs, MCP server readiness, and security policy gates."""
  from taste_engine.tools.agents import AGENTS, available, run_agent

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

  for name in AGENTS:
    is_avail = available(name)
    status_str = "Ready" if is_avail else "Not on PATH"
    agent_table.add_row(name, "[OK]" if is_avail else "[X]", status_str)

  console.print(agent_table)

  # 3. Check MCP Server Readiness
  try:
    from taste_engine.mcp.server import create_mcp_server
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
  from taste_engine.mcp.server import create_mcp_server

  vault_path = Path(vault).resolve() if vault else None
  server = create_mcp_server(vault_path)
  console.print(f"[bold cyan]Starting OverMind MCP Server (transport: {transport})...[/bold cyan]")
  if transport == "stdio":
    server.run(transport="stdio")
  elif transport == "sse":
    server.run(transport="sse", port=port)
  else:
    server.run(transport="streamable-http", port=port)


@app.command()
def eval(
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress detailed output"),
    extractor: str = typer.Option(None, "--extractor", "-e", help="module:callable to grade (default: rule-based baseline)"),
    dataset: str = typer.Option("golden", "--dataset", "-d", help="golden | heldout | path to a JSON file"),
    output: str = typer.Option(None, "--output", "-o", help="Write JSON results to this path"),
    threshold: float = typer.Option(None, "--threshold", help="F1 gate (default: built-in floor)"),
):
  """Grades an extractor (default: rule-based baseline, NOT an LLM) on a labelled dataset."""
  from taste_engine.evals.extractors import load_extractor
  from taste_engine.evals.run_evals import DATASET_PATH, F1_REGRESSION_THRESHOLD, HELDOUT_PATH, run_evaluations

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
def validate_thread(
    file_path: str = typer.Argument(..., help="Path to thread markdown file"),
    limit: int = typer.Option(280, "--limit", "-l", help="Character limit per tweet"),
):
  """Validates a Twitter/X thread draft against character limits and URL weighting."""
  cfg = load_config()
  try:
    safe_file = validate_vault_path(file_path, cfg.vault)
  except SecurityViolation as e:
    console.print(f"[bold red]Security Error:[/bold red] {e}")
    raise typer.Exit(code=2)

  from taste_engine.projects.twitter.scripts.thread_validator import validate_thread as _validate
  passed = _validate(safe_file, limit)
  if not passed:
    raise typer.Exit(code=1)


@app.command()
def status(
    run_id: str = typer.Argument(None, help="Optional specific run ID to inspect"),
):
  """Inspects pipeline execution status and run logs."""
  cfg = load_config()
  from taste_engine.orchestration.cli import show_status
  show_status(cfg, run_id)


@app.command()
def approve(
    file_path: str = typer.Argument(..., help="Path to pending note to approve"),
):
  """Approves a pending generated note through the human gate."""
  cfg = load_config()
  from taste_engine.knowledge.context import resolve_vault_path
  from taste_engine.actions import gate

  path = resolve_vault_path(cfg, file_path)
  if not path:
    console.print(f"[red]Not found:[/red] {file_path}")
    raise typer.Exit(code=1)
  gate.approve(path)
  console.print(f"[green]✓ Approved:[/green] {path.relative_to(cfg.vault)} → status: approved")


if __name__ == "__main__":
  app()
