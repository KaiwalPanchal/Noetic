"""Briefing workflow: `overmind briefing`, `overmind projects`, and the narrated briefing pipeline."""

from __future__ import annotations

import json

import typer

from overmind.knowledge import registry as wiki
from overmind.knowledge.config import load_config
from workflows.briefing import pipeline as _pipeline  # noqa: F401 (registers the `briefing` pipeline)
from workflows.briefing.pipeline import build_briefing, render_briefing_text


def register(app, registry):
  """Add the briefing/projects CLI commands (when a Typer app is given). Pipelines register on import."""
  if app is None:
    return

  @app.command()
  def projects(
      as_json: bool = typer.Option(False, "--json", help="Print JSON instead of a table"),
  ):
    """Lists projects from <overmind>/wiki/projects (no LLM; the private profile is never read)."""
    cfg = load_config()
    rows = wiki.load_projects(cfg)
    if as_json:
      typer.echo(json.dumps(rows, indent=2, ensure_ascii=False))
      return
    if cfg.overmind is None:
      typer.echo("paths.overmind is not set in taste-engine.config.json")
    for p in rows:
      stale = "" if p["stale_days"] is None else f", {p['stale_days']}d since touched"
      flag = f"  [incomplete: missing {', '.join(p['missing'])}]" if p["incomplete"] else ""
      gate = f"  gate: {p['gate']}" if p["gate"] else ""
      typer.echo(f"{p['name']} [{p['status'] or '?'}] goal: {p['goal'] or '-'}; next: {p['next_action'] or '-'}{stale}{gate}{flag}")

  @app.command()
  def briefing(
      as_json: bool = typer.Option(False, "--json", help="Print the deterministic briefing as JSON"),
      narrate: bool = typer.Option(False, "--narrate", help="Run the overmind agent contract over the briefing; lands a pending_review note"),
      agent: str = typer.Option(None, "--agent", help="With --narrate: force one agent (no fallback)"),
  ):
    """What needs doing next and what is blocked. Works with no agent CLI installed unless --narrate."""
    if agent and not narrate:
      typer.echo("--agent only applies with --narrate")
      raise typer.Exit(code=2)
    cfg = load_config()
    if narrate:
      from overmind.orchestration.cli import execute

      registry.discover()
      execute(cfg, "briefing", {"agent": agent})
      return
    data = build_briefing(cfg)
    typer.echo(json.dumps(data, indent=2, ensure_ascii=False) if as_json else render_briefing_text(data))
