"""Fleet workflow: background helpers.

  librarian   daily inbox triage (deterministic; never moves or deletes notes)
  repos       live git telemetry for every registered project repo
  delegate    worker agent in a project's repo, on its own branch, looping on tests
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from noetic.knowledge import repos as repo_telemetry
from noetic.knowledge.config import CONFIG_NAME, Config, load_config
from workflows.fleet import delegate as _delegate  # noqa: F401 (registers the `delegate` pipeline)
from workflows.fleet import librarian as lib


def _config(vault: str | None) -> Config:
  if not vault:
    return load_config()
  root = Path(vault).expanduser().resolve()
  f = root / CONFIG_NAME
  return Config(root, json.loads(f.read_text(encoding="utf-8")) if f.exists() else {})


def register(app, registry):
  if app is None:
    return

  @app.command()
  def librarian(
      vault: str = typer.Option(None, "--vault", help="Vault root (default: auto-detected)"),
      force: bool = typer.Option(False, "--force", help="Run even if it already ran in the last 24 hours"),
      schedule: bool = typer.Option(False, "--schedule", help="Print the scheduler command for a daily run (installs nothing)"),
  ):
    """Daily inbox triage: flags empties/duplicates and suggests links. Never moves or deletes notes."""
    cfg = _config(vault)
    if schedule:
      for name, cmd in lib.schedule_hint(cfg.vault).items():
        typer.echo(f"{name}: {cmd}")
      return
    path = lib.run_librarian(cfg, force)
    typer.echo("Already ran in the last 24h (use --force)." if path is None
               else f"Digest written: {path.relative_to(cfg.vault)} (pending_review)")

  @app.command()
  def repos(
      as_json: bool = typer.Option(False, "--json", help="Print JSON instead of text"),
  ):
    """Live git status of every registered project's repo (branch, uncommitted changes, last commit)."""
    rows = repo_telemetry.load_repo_telemetry(load_config())
    typer.echo(json.dumps(rows, indent=2, ensure_ascii=False) if as_json else repo_telemetry.render_repo_telemetry(rows))

  @app.command()
  def delegate(
      project: str = typer.Argument(..., help="Project name from the registry"),
      task: str = typer.Argument(..., help="What the worker agent should do"),
      test: str = typer.Option(None, "--test", help="Test command to loop on"),
      max_iterations: int = typer.Option(3, "--max-iterations"),
      agent: str = typer.Option(None, "--agent", help="Force one agent (no fallback)"),
  ):
    """Spawns a worker agent in the project's repo on a fresh branch; loops on tests; logs the result."""
    from noetic.orchestration import registry as reg
    from noetic.orchestration.cli import execute

    reg.discover()
    execute(load_config(), "delegate", {"project": project, "task": task, "test": test,
                                        "max_iterations": max_iterations, "agent": agent})
