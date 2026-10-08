"""Capture workflow: clip web URLs or raw text directly into inbox/ without LLM."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import typer

from noetic.knowledge.config import Config, config_file, load_config, slugify
from noetic.tools import clipper


def _config(vault: str | None) -> Config:
  if not vault:
    return load_config()
  root = Path(vault).expanduser().resolve()
  f = config_file(root)
  return Config(root, json.loads(f.read_text(encoding="utf-8")) if f.exists() else {})


def register(app, registry):
  if app is None:
    return

  @app.command()
  def clip(
      target: str = typer.Argument(..., help="URL or raw text to clip into inbox"),
      context: str = typer.Option("", "--context", "-c", help="Optional context or title"),
      vault: str = typer.Option(None, "--vault", help="Vault root (default: auto-detected)"),
  ):
    """Clip a URL or raw text into inbox/ as a signal note. Deterministic, no LLM."""
    cfg = _config(vault)
    inbox = cfg.vault / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)

    if target.startswith("http://") or target.startswith("https://"):
      clip_data = clipper.clip_url(target)
      if context:
        clip_data["context"] = context
    else:
      title = context.strip() or target[:40].strip()
      clip_data = {
        "title": title,
        "url": "",
        "content": target,
        "clipped_at": datetime.now().isoformat(),
      }

    title = clip_data.get("title") or "clip"
    base_slug = slugify(title)[:40] or "clip"
    out_path = inbox / f"{base_slug}.md"
    i = 2
    while out_path.exists():
      out_path = inbox / f"{base_slug}-{i}.md"
      i += 1

    content = clipper.format_as_signal_note(clip_data)
    out_path.write_text(content, encoding="utf-8")
    typer.echo(str(out_path))
