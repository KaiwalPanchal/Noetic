"""twitter workflow: draft / journey pipelines and the `noetic validate-thread` command.

The agent drafts; the owner posts by hand. Nothing here ever posts.
"""

from __future__ import annotations


def register(app, registry):
  from workflows.twitter.pipelines import draft, journey  # noqa: F401 (registers the pipelines)

  if app is None:
    return
  import typer

  from noetic.gates.policy_gate import SecurityViolation, validate_vault_path
  from noetic.knowledge.config import load_config

  @app.command("validate-thread")
  def validate_thread(
      file_path: str = typer.Argument(..., help="Path to thread markdown file"),
      limit: int = typer.Option(280, "--limit", "-l", help="Character limit per tweet"),
  ):
    """Validates a Twitter/X thread draft against character limits and URL weighting."""
    cfg = load_config()
    try:
      safe_file = validate_vault_path(file_path, cfg.vault)
    except SecurityViolation as e:
      typer.echo(f"Security Error: {e}")
      raise typer.Exit(code=2)

    from workflows.twitter.scripts.thread_validator import validate_thread as _validate
    if not _validate(safe_file, limit):
      raise typer.Exit(code=1)
