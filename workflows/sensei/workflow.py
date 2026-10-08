"""Sensei workflow: registers focus and park commands, plus think pipeline and tools."""

from __future__ import annotations

import typer

from noetic.knowledge.config import load_config


def register(app, registry):
  from workflows.sensei import focus as _focus  # noqa: F401 (registers tools)
  from workflows.sensei import pipelines as _pipelines  # noqa: F401 (registers think pipeline)

  if app is None:
    return

  @app.command()
  def focus(
      commitment: str = typer.Argument(None, help="New commitment string"),
      project: str = typer.Option("", "--project", "-p", help="Associated project name"),
      done_when: str = typer.Option("", "--done-when", help="Completion criteria"),
      done: bool = typer.Option(False, "--done", help="Mark current focus as finished"),
  ):
    """Manage current focus commitment, warn on frequent switches, or finish focus."""
    cfg = load_config()
    try:
      if done:
        prev = _focus.finish_focus(cfg)
        if prev:
          typer.echo(f"Finished focus: {prev.get('commitment')}")
        else:
          typer.echo("No focus was set.")
        return

      if commitment is not None:
        prev = _focus.switch_focus(cfg, commitment, project, done_when)
        if prev:
          typer.echo(f"Switched focus from '{prev.get('commitment')}' to '{commitment}'.")
        else:
          typer.echo(f"Focus set to '{commitment}'.")
        return

      cur = _focus.get_focus(cfg)
      if cur:
        typer.echo(f"Current focus: {cur.get('commitment')}")
        if cur.get("project"):
          typer.echo(f"Project: {cur.get('project')}")
        if cur.get("done_when"):
          typer.echo(f"Done when: {cur.get('done_when')}")
        days = _focus.days_on(cur)
        if days:
          typer.echo(f"Days active: {days}")
      else:
        typer.echo("No focus set.")

      switches = _focus.recent_switches(cfg, 7)
      if switches >= 3:
        typer.echo(f"Warning: {switches} focus switches in the last 7 days.")
    except Exception as exc:
      typer.echo(f"Error: {exc}", err=True)
      raise typer.Exit(code=1)

  @app.command()
  def park(
      thought: str = typer.Argument(..., help="Thought or tangent to park"),
      title: str = typer.Option("", "--title", "-t", help="Title for the parked note"),
  ):
    """Park an idea or tangent directly into ideas/PARKED.md."""
    cfg = load_config()
    try:
      focus_data = _focus.get_focus(cfg) if cfg.overmind else None
      park_title = title.strip() or thought[:60].strip()
      path = _focus.park_idea(cfg, park_title, "", thought=thought, focus=focus_data)
      typer.echo(f"Parked: {path}")
    except Exception as exc:
      typer.echo(f"Error: {exc}", err=True)
      raise typer.Exit(code=1)
